#ifndef ANGSTROM_CORE_H
#define ANGSTROM_CORE_H
// Portable controller/schedule core, also compiled by the hardware-free tests.
#include <math.h>
#include <stdint.h>

namespace angstrom {
const uint8_t MAX_STEPS = 12, MAX_POINTS = 12;
const float PHASE_TURN = 6.283185307179586f;
const float MIN_C = 10.f, MAX_C = 45.f, TEC_LIMIT_C = 60.f, BASE_LIMIT_C = 56.f;
const uint32_t TIMEOUT_MS = 2000;
enum Mode { OFF, OPEN, P, PI_MODE };
enum State { IDLE, RUNNING, DONE, FAULT };
enum Fault { NONE, TEC_SENSOR, TEC_LIMIT, TEC_RANGE, BASE_SENSOR, BASE_LIMIT,
             LINK_TIMEOUT, TIME_GAP, LOOKUP_RANGE, SERIAL_OVERFLOW, BAD_COMMAND };
struct Step { float duration, ta, tb, period, kp, ki; Mode mode; };
struct Point { float temperature, pwm; };
struct Output {
  float feedforward, controller, compensated, error;
  int pwm;
  bool saturated, integrationBlocked;
};
inline const char* modeName(Mode m) {
  switch(m) { case OPEN:return "OPEN"; case P:return "P"; case PI_MODE:return "PI"; default:return "OFF"; }
}
inline const char* stateName(State s) {
  switch(s) { case RUNNING:return "RUNNING"; case DONE:return "DONE"; case FAULT:return "FAULT"; default:return "IDLE"; }
}
inline const char* faultName(Fault f) {
  switch(f) {
    case TEC_SENSOR:return "TEC_SENSOR"; case TEC_LIMIT:return "TEC_LIMIT";
    case TEC_RANGE:return "TEC_RANGE"; case BASE_SENSOR:return "BASE_SENSOR";
    case BASE_LIMIT:return "BASE_LIMIT"; case LINK_TIMEOUT:return "LINK_TIMEOUT";
    case TIME_GAP:return "TIME_GAP"; case LOOKUP_RANGE:return "LOOKUP_RANGE";
    case SERIAL_OVERFLOW:return "SERIAL_OVERFLOW"; case BAD_COMMAND:return "BAD_COMMAND";
    default:return "NONE";
  }
}
class Engine {
 public:
  Step steps[MAX_STEPS]; Point points[MAX_POINTS];
  uint8_t count, pointCount, index;
  float ratio, phase, withinStep, integral, setpoint;
  int pwmLimit; bool antiWindup, prepared;
  State state; Fault fault; Output out;
  uint32_t previousMs; uint16_t transitions;
  Engine(): count(0), pointCount(0), index(0), ratio(1), phase(0), withinStep(0),
    integral(0), setpoint(NAN), pwmLimit(96), antiWindup(true), prepared(false),
    state(IDLE), fault(NONE), previousMs(0), transitions(0) { zero(); }
  void zero() { out = {NAN, NAN, 0, NAN, 0, false, false}; }
  void stop() { if(state != FAULT) state=IDLE; integral=0; zero(); }
  void trip(Fault f) { fault=f; state=FAULT; integral=0; prepared=false; zero(); }
  void clear() {
    stop(); state=IDLE; fault=NONE; count=pointCount=index=0;
    prepared=false; phase=withinStep=0; setpoint=NAN;
  }
  const Step* current() const { return count ? &steps[index] : 0; }
  Fault sensorFault(float tec, float base) const {
    if(!isfinite(tec)) return TEC_SENSOR;
    if(tec>=TEC_LIMIT_C) return TEC_LIMIT;
    if(tec<MIN_C || tec>MAX_C) return TEC_RANGE;
    if(!isfinite(base)) return BASE_SENSOR;
    if(base>=BASE_LIMIT_C) return BASE_LIMIT;
    return NONE;
  }
  bool validate() const {
    if(!count || count>MAX_STEPS || pointCount>MAX_POINTS || !isfinite(ratio)
       || ratio<=0 || ratio>20 || pwmLimit<1 || pwmLimit>255) return false;
    float total=0;
    for(uint8_t i=0;i<pointCount;++i) {
      if(!isfinite(points[i].temperature) || !isfinite(points[i].pwm)
        || fabs(points[i].pwm)>255) return false;
      if(i && (points[i].temperature<=points[i-1].temperature
               || points[i].pwm<=points[i-1].pwm)) return false;
    }
    for(uint8_t i=0;i<count;++i) {
      const Step &s=steps[i];
      if(!isfinite(s.duration) || s.duration<1 || !isfinite(s.ta) || !isfinite(s.tb)
        || s.tb<0 || s.ta-s.tb<MIN_C || s.ta+s.tb>MAX_C
        || !isfinite(s.period) || s.period<100 || s.period>86400
        || !isfinite(s.kp) || s.kp<0 || s.kp>1000
        || !isfinite(s.ki) || s.ki<0 || s.ki>100
        || (s.mode!=OPEN && s.mode!=P && s.mode!=PI_MODE)) return false;
      total+=s.duration;
      if(s.mode==OPEN && (pointCount<2 || s.ta-s.tb<points[0].temperature
        || s.ta+s.tb>points[pointCount-1].temperature)) return false;
    }
    return total<=86400;
  }
  bool start(uint32_t now, float tec, float base) {
    if(state==RUNNING || state==FAULT || !prepared || !validate()) return false;
    Fault f=sensorFault(tec,base); if(f!=NONE) { trip(f); return false; }
    index=0; phase=withinStep=integral=0; transitions=0; previousMs=now;
    setpoint=steps[0].ta; state=RUNNING; fault=NONE; zero(); return true;
  }
  float lookup(float t) const {
    if(pointCount<2 || t<points[0].temperature || t>points[pointCount-1].temperature) return NAN;
    for(uint8_t i=1;i<pointCount;++i) if(t<=points[i].temperature) {
      const Point &a=points[i-1], &b=points[i];
      return a.pwm+(b.pwm-a.pwm)*(t-a.temperature)/(b.temperature-a.temperature);
    }
    return NAN;
  }
  void update(uint32_t now, float tec, float base, uint32_t heartbeatAge) {
    transitions=0;
    if(state!=RUNNING) return;
    Fault f=sensorFault(tec,base); if(f!=NONE) { trip(f); return; }
    if(heartbeatAge>TIMEOUT_MS) { trip(LINK_TIMEOUT); return; }
    uint32_t elapsed=now-previousMs;
    if(elapsed>TIMEOUT_MS) { trip(TIME_GAP); return; }
    previousMs=now;
    float dt=elapsed*.001f, remaining=dt;
    // Integrate the old frequency exactly up to each boundary, then the new one.
    while(remaining>0 && state==RUNNING) {
      float left=steps[index].duration-withinStep;
      float use=remaining<left ? remaining : left;
      phase=fmodf(phase+PHASE_TURN*use/steps[index].period,PHASE_TURN);
      withinStep+=use; remaining-=use;
      if(withinStep>=steps[index].duration) {
        if(index+1>=count) { state=DONE; integral=0; zero(); return; }
        Mode old=steps[index].mode;
        ++index; withinStep=0; transitions|=(uint16_t(1)<<index);
        if(steps[index].mode!=old) integral=0;
      }
    }
    const Step &s=steps[index]; setpoint=s.ta+s.tb*sinf(phase);
    out.error=setpoint-tec; out.saturated=out.integrationBlocked=false;
    if(s.mode==OPEN) {
      out.feedforward=lookup(setpoint); out.controller=NAN;
      if(!isfinite(out.feedforward)) { trip(LOOKUP_RANGE); return; }
      out.compensated=out.feedforward; integral=0;
    } else {
      out.feedforward=NAN;
      float ki=s.mode==PI_MODE ? s.ki : 0;
      float proposed=s.mode==PI_MODE ? integral+out.error*dt : 0;
      float raw=s.kp*out.error+ki*proposed;
      float compensated=raw<0 ? ratio*raw : raw;
      bool blocked=s.mode==PI_MODE && antiWindup &&
        ((compensated>pwmLimit && out.error>0) || (compensated<-pwmLimit && out.error<0));
      if(!blocked) integral=proposed;
      out.integrationBlocked=blocked;
      out.controller=s.kp*out.error+ki*integral;
      out.compensated=out.controller<0 ? ratio*out.controller : out.controller;
    }
    if(!isfinite(out.compensated) || !isfinite(integral)) { trip(BAD_COMMAND); return; }
    out.saturated=fabsf(out.compensated)>pwmLimit;
    float clamped=fmaxf(-pwmLimit,fminf(pwmLimit,out.compensated));
    out.pwm=int(roundf(clamped));
  }
};
}
#endif
