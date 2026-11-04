#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "angstrom_core.h"

// Module 8 v1: firmware owns timing, waveform, schedule, control and fail-off.
// A0 is TEC feedback; A1 is the separately monitored rod-base boundary.
// Physical thermal switch remains independent. Never energize both directions.
using namespace angstrom;
const uint8_t HEAT_PWM_PIN=9, COOL_PWM_PIN=10;
const uint8_t ROD_PINS[5]={A1,A2,A3,A4,A5};
const uint16_t TEC_SAMPLE_COUNT=1000, ROD_SAMPLE_COUNT=100;
const uint32_t REPORT_INTERVAL_MS=500;
Engine engine;
char commandBuffer[144]; uint8_t commandLength=0; bool commandOverflow=false;
uint32_t lastScan=0, lastHeartbeat=0, lastMeasurement=0, sequence=0;
float tecC=NAN, rodC[5]={NAN,NAN,NAN,NAN,NAN};
uint8_t rodOk=0;

float readCelsius(uint8_t pin, uint16_t count) {
  // Discard the first reading after mux switching before averaging.
  analogRead(pin);
  uint32_t sum=0; for(uint16_t i=0;i<count;++i) sum+=analogRead(pin);
  float adc=float(sum)/count;
  if(adc<=0 || adc>=1023) return NAN;
  float resistance=100000.f*adc/(1023.f-adc);
  return 1.f/(1.f/298.15f+logf(resistance/100000.f)/4540.f)-273.15f;
}
void applyOutput() {
  analogWrite(HEAT_PWM_PIN,0); analogWrite(COOL_PWM_PIN,0);
  int pwm=engine.state==RUNNING ? engine.out.pwm : 0;
  if(pwm>0) analogWrite(HEAT_PWM_PIN,pwm);
  if(pwm<0) analogWrite(COOL_PWM_PIN,-pwm);
}
void ack(const __FlashStringHelper* tag) { Serial.print(F("#ACK,")); Serial.println(tag); }
void error(const __FlashStringHelper* tag) { Serial.print(F("#ERR,")); Serial.println(tag); }
void faultEvent() {
  applyOutput(); Serial.print(F("#EVENT,FAULT,")); Serial.print(millis());
  Serial.print(','); Serial.println(faultName(engine.fault));
}
bool number(const char* token, float &value) {
  if(!token || !*token) return false;
  char* end; value=strtod(token,&end); return !*end && isfinite(value);
}
void command(char* text) {
  char* tokens[10]; uint8_t n=0; char* save;
  for(char* t=strtok_r(text," ",&save);t;t=strtok_r(NULL," ",&save)) {
    if(n==10) { error(F("FIELDS")); return; } tokens[n++]=t;
  }
  if(!n) return;
  if(n==1 && strcmp(tokens[0],"PING")==0) { lastHeartbeat=millis(); return; }
  if(n==1 && strcmp(tokens[0],"HELLO")==0) { ack(F("HELLO,module_08_angstrom_v1")); return; }
  if(n==1 && strcmp(tokens[0],"STOP")==0) {
    engine.stop(); applyOutput(); ack(F("STOP")); return;
  }
  if(n==1 && strcmp(tokens[0],"START")==0) {
    uint32_t now=millis();
    if(now-lastMeasurement>TIMEOUT_MS || engine.state==RUNNING || now-lastHeartbeat>TIMEOUT_MS) {
      error(F("START_STALE_OR_RUNNING")); return;
    }
    if(!engine.start(now,tecC,rodC[0])) { error(F("START_REJECTED")); if(engine.state==FAULT) faultEvent(); return; }
    lastHeartbeat=now; ack(F("START"));
    Serial.print(F("#EVENT,STEP,")); Serial.print(now); Serial.println(F(",0")); return;
  }
  if(engine.state==RUNNING) { error(F("STOP_BEFORE_CONFIG")); return; }
  if(n==1 && strcmp(tokens[0],"CLEAR")==0) {
    if(engine.state==FAULT && engine.sensorFault(tecC,rodC[0])!=NONE) { error(F("SENSORS_UNSAFE")); return; }
    engine.clear(); ack(F("CLEAR")); return;
  }
  if(engine.state==FAULT) { error(F("CLEAR_FAULT_FIRST")); return; }
  float values[7];
  if(n==4 && strcmp(tokens[0],"CONFIG")==0) {
    for(uint8_t i=0;i<3;++i) if(!number(tokens[i+1],values[i])) { error(F("NUMBER")); return; }
    if(values[0]<=0 || values[0]>20 || values[1]<1 || values[1]>255 || floorf(values[1])!=values[1]
       || (values[2]!=0 && values[2]!=1)) { error(F("CONFIG_RANGE")); return; }
    engine.ratio=values[0]; engine.pwmLimit=int(values[1]); engine.antiWindup=values[2]!=0;
    engine.prepared=false; ack(F("CONFIG")); return;
  }
  if(n==3 && strcmp(tokens[0],"CAL")==0) {
    if(engine.pointCount>=MAX_POINTS || !number(tokens[1],values[0]) || !number(tokens[2],values[1])
       || fabsf(values[1])>255) { error(F("CAL_RANGE")); return; }
    if(engine.pointCount && (values[0]<=engine.points[engine.pointCount-1].temperature
       || values[1]<=engine.points[engine.pointCount-1].pwm)) { error(F("CAL_ORDER")); return; }
    engine.points[engine.pointCount++]={values[0],values[1]}; engine.prepared=false; ack(F("CAL")); return;
  }
  if(n==8 && strcmp(tokens[0],"STEP")==0) {
    // STEP duration mean amplitude period mode kp ki. No AVR scanf-float dependency.
    if(engine.count>=MAX_STEPS) { error(F("STEP_COUNT")); return; }
    for(uint8_t i=0;i<4;++i) if(!number(tokens[i+1],values[i])) { error(F("NUMBER")); return; }
    if(!number(tokens[6],values[4]) || !number(tokens[7],values[5])) { error(F("NUMBER")); return; }
    Mode mode=strcmp(tokens[5],"OPEN")==0 ? OPEN : strcmp(tokens[5],"P")==0 ? P : strcmp(tokens[5],"PI")==0 ? PI_MODE : OFF;
    engine.steps[engine.count++]={values[0],values[1],values[2],values[3],values[4],values[5],mode};
    engine.prepared=false; ack(F("STEP")); return;
  }
  if(n==3 && strcmp(tokens[0],"COMMIT")==0) {
    if(!number(tokens[1],values[0]) || !number(tokens[2],values[1])
      || values[0]!=engine.count || values[1]!=engine.pointCount || !engine.validate()) {
      engine.prepared=false; error(F("INVALID_PLAN")); return;
    }
    engine.prepared=true; ack(F("COMMIT")); return;
  }
  error(F("UNKNOWN_COMMAND"));
}
void readSerialCommands() {
  while(Serial.available()>0) {
    char c=Serial.read(); if(c=='\r') continue;
    if(c=='\n') {
      if(commandOverflow) {
        engine.trip(SERIAL_OVERFLOW); faultEvent(); error(F("LINE_OVERFLOW"));
      } else if(commandLength) { commandBuffer[commandLength]='\0'; command(commandBuffer); }
      commandLength=0; commandOverflow=false;
    } else if(!commandOverflow) {
      if(commandLength<sizeof(commandBuffer)-1) commandBuffer[commandLength++]=c;
      else { commandOverflow=true; commandLength=0; engine.trip(SERIAL_OVERFLOW); applyOutput(); }
    }
  }
}
void printFloat(float value) { if(isfinite(value)) Serial.print(value,5); else Serial.print(F("nan")); }
void cell(float value) { Serial.print(','); printFloat(value); }
void printMeasurement(uint32_t now) {
  const Step* s=engine.current(); int pwm=engine.state==RUNNING ? engine.out.pwm : 0;
  Serial.print(F("DATA,")); Serial.print(now*.001f,3); cell(tecC);
  for(uint8_t i=0;i<5;++i) cell(rodC[i]);
  Serial.print(','); Serial.print(abs(pwm)); Serial.print(','); Serial.print(pwm>0?1:0);
  Serial.print(','); Serial.print(pwm>0?pwm:0); Serial.print(','); Serial.print(pwm<0?-pwm:0);
  cell(TEC_LIMIT_C); Serial.print(','); Serial.print(engine.state==FAULT?F("SHUTDOWN"):F("OK"));
  Serial.print(','); Serial.print(rodOk); Serial.print(','); Serial.print(stateName(engine.state));
  Serial.print(','); Serial.print(s?modeName(s->mode):"OFF"); Serial.print(','); Serial.print(s?engine.index:-1);
  cell(s?s->ta:NAN); cell(s?s->tb:NAN); cell(s?s->period:NAN); cell(engine.setpoint);
  cell(engine.out.feedforward); cell(engine.out.controller); cell(engine.ratio);
  Serial.print(','); Serial.print(pwm); cell(engine.phase); cell(s?s->kp:NAN); cell(s?s->ki:NAN);
  Serial.print(','); Serial.print(engine.pwmLimit); Serial.print(','); Serial.print(engine.antiWindup?1:0);
  cell(engine.out.error); cell(engine.integral); cell(engine.out.compensated);
  Serial.print(','); Serial.print(engine.out.saturated?1:0);
  Serial.print(','); Serial.print(engine.out.integrationBlocked?1:0);
  cell(BASE_LIMIT_C); cell(MAX_C); Serial.print(','); Serial.print(now-lastHeartbeat);
  Serial.print(','); Serial.print(faultName(engine.fault)); Serial.print(','); Serial.print(now);
  Serial.print(','); Serial.println(sequence++);
}
void setup() {
  pinMode(A0,INPUT); for(uint8_t i=0;i<5;++i) pinMode(ROD_PINS[i],INPUT);
  pinMode(HEAT_PWM_PIN,OUTPUT); pinMode(COOL_PWM_PIN,OUTPUT); applyOutput();
  Serial.begin(115200);
  Serial.println(F("#firmware,module_08_angstrom_v1,2026-11-04"));
  Serial.println(F("#channels,tec=A0,rod1=A1,rod2=A2,rod3=A3,rod4=A4,rod5=A5"));
  Serial.println(F("#pins,heat=D9,cool=D10,baud=115200,report_ms=500"));
  Serial.println(F("#DATA,time_s,tec_C,rod1_C,rod2_C,rod3_C,rod4_C,rod5_C,pwm,heat_cool,heat_pwm,cool_pwm,limit_C,safety,rod_ok,run_state,control_mode,step,Ta_C,Tb_C,period_s,setpoint_C,feedforward_pwm,controller_pwm,heating_to_cooling_ratio,signed_pwm,phase_rad,Kp_pwm_per_C,Ki_pwm_per_C_s,pwm_limit,anti_windup,error_C,integral_error_C_s,compensated_pwm,saturated,integration_blocked,rod_base_limit_C,operating_max_C,heartbeat_age_ms,fault_code,time_ms,seq"));
}
void loop() {
  readSerialCommands(); uint32_t now=millis();
  if(engine.state==RUNNING && now-lastHeartbeat>TIMEOUT_MS) { engine.trip(LINK_TIMEOUT); faultEvent(); }
  if(now-lastScan<REPORT_INTERVAL_MS) return;
  lastScan=now;
  tecC=readCelsius(A0,TEC_SAMPLE_COUNT); rodOk=0;
  for(uint8_t i=0;i<5;++i) {
    float t=readCelsius(ROD_PINS[i],ROD_SAMPLE_COUNT);
    rodC[i]=isfinite(t) && t>=-20 && t<=90 ? t : NAN;
    if(isfinite(rodC[i])) ++rodOk;
  }
  now=millis(); lastMeasurement=now; State old=engine.state;
  engine.update(now,tecC,rodC[0],now-lastHeartbeat); applyOutput();
  if(engine.state==FAULT && old!=FAULT) faultEvent();
  for(uint8_t i=1;i<engine.count;++i) if(engine.transitions&(uint16_t(1)<<i)) {
    Serial.print(F("#EVENT,STEP,")); Serial.print(now); Serial.print(','); Serial.println(i);
  }
  if(engine.state==DONE && old==RUNNING) { Serial.print(F("#EVENT,DONE,")); Serial.println(now); }
  printMeasurement(now);
}
