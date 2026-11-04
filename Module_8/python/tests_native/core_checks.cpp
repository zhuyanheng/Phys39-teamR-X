#include "../../arduino/module_08_rod_controller/angstrom_core.h"
#include <cassert>
#include <cmath>
#include <iostream>
using namespace angstrom;
Engine single(Mode mode=PI_MODE,float ta=35,float tb=5,float period=100) {
  Engine e;e.ratio=4;e.pwmLimit=30;e.steps[0]={1000,ta,tb,period,2,1,mode};e.count=1;
  e.points[0]={10,-30};e.points[1]={30,0};e.points[2]={45,30};e.pointCount=3;
  e.prepared=true;assert(e.start(0,25,25));return e;
}
bool near(float a,float b,float tol=1e-4) { return fabs(a-b)<tol; }
int main() {
  {auto e=single(OPEN);for(int t=500;t<=25000;t+=500)e.update(t,25,25,0);
    assert(near(e.setpoint,40));assert(near(e.out.feedforward,20));assert(e.out.pwm==20);
    assert(std::isnan(e.out.controller));}
  {auto e=single(PI_MODE,20,0);e.update(500,25,25,0);
    assert(e.out.integrationBlocked);assert(e.integral==0);assert(e.out.controller==-10);
    assert(e.out.compensated==-40);assert(e.out.pwm==-30);assert(e.out.saturated);
    e.antiWindup=false;e.update(1000,25,25,0);assert(e.integral<0);}
  {auto e=single(PI_MODE,30,0);e.integral=100;e.update(500,31,25,0);
    assert(!e.out.integrationBlocked);assert(near(e.integral,99.5));}
  {auto e=single(P);e.integral=99;e.update(500,25,25,0);assert(e.integral==0);}
  {auto e=single(OPEN);e.steps[0].duration=1.25;
    e.steps[1]={10,35,5,200,2,1,OPEN};e.count=2;e.update(1500,25,25,0);
    assert(e.index==1);assert(near(e.phase,PHASE_TURN*(1.25f/100+.25f/200)));
    assert(e.transitions==2);assert(near(e.withinStep,.25));}
  {auto e=single(P);e.steps[0].duration=1;
    e.steps[1]={1,35,5,150,2,1,P};e.steps[2]={1,35,5,240,2,1,P};e.count=3;
    e.update(2000,25,25,0);assert(e.index==2);assert(e.transitions==6);
    e.update(3000,25,25,0);assert(e.state==DONE);assert(e.out.pwm==0);}
  {auto e=single(P);e.steps[0].duration=1;e.update(1000,25,25,0);
    assert(e.state==DONE && e.out.pwm==0);}
  {auto e=single(P);e.previousMs=0xFFFFFF00u;
    e.update(uint32_t(0xFFFFFF00u+500u),25,25,0);assert(e.state==RUNNING);}
  const float tecs[]={NAN,60,45.01,25,25,25,25};
  const float bases[]={25,25,25,NAN,56,25,25};
  const Fault faults[]={TEC_SENSOR,TEC_LIMIT,TEC_RANGE,BASE_SENSOR,BASE_LIMIT,LINK_TIMEOUT,TIME_GAP};
  for(int i=0;i<7;++i) {auto e=single();e.update(i==6?2001:500,tecs[i],bases[i],i==5?2001:0);
    assert(e.state==FAULT && e.fault==faults[i] && e.out.pwm==0);
    e.stop();assert(e.state==FAULT);assert(!e.start(1000,25,25));}
  {auto e=single();e.steps[0].period=99;assert(!e.validate());e.steps[0].period=100;
    e.steps[0].ta=40;e.steps[0].tb=16;assert(!e.validate());}
  {auto e=single(OPEN);e.points[1].pwm=-40;assert(!e.validate());}
  {auto e=single(OPEN);assert(std::isnan(e.lookup(46)));assert(near(e.lookup(45),30));}
  {Engine e;assert(!e.start(0,25,25));}
  std::cout<<"Native core checks passed\n";
}
