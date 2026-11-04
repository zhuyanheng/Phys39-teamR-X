// Compile the actual .ino against a hardware-free Arduino surface.
#include <cmath>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <sstream>
#include <iostream>
#include <iomanip>
#include <string>
#include <vector>
#include <deque>
using __FlashStringHelper=char;
#define F(x) x
const int A0=0,A1=1,A2=2,A3=3,A4=4,A5=5,INPUT=0,OUTPUT=1;
uint32_t fakeNow=1000;
int pins[20]={0};
uint32_t millis() { return fakeNow; }
void pinMode(int,int) {}
int analogRead(int) { return 512; }
void analogWrite(int pin,int value) {
  pins[pin]=value;
  if(pins[9] && pins[10]) { std::cerr<<"Both bridge directions active\n";std::exit(99); }
}
struct SerialPort {
  std::deque<char> input;
  void begin(int) {}
  int available() { return input.size(); }
  char read() { char c=input.front();input.pop_front();return c; }
  template<class T> void print(T x) { std::cout<<x; }
  void print(unsigned char x) { std::cout<<int(x); }
  void print(float x,int decimals) { std::cout<<std::fixed<<std::setprecision(decimals)<<x; }
  template<class T> void println(T x) { print(x);std::cout<<'\n'; }
} Serial;
#include "../../arduino/module_08_rod_controller/module_08_rod_controller.ino"
int main() {
  setup(); tecC=25;for(int i=0;i<5;++i)rodC[i]=25;rodOk=5;lastMeasurement=fakeNow;
  std::string line;
  while(std::getline(std::cin,line)) {
    if(line.rfind("@T ",0)==0) {
      std::istringstream in(line.substr(3));float tec,base;uint32_t age=0;
      in>>fakeNow>>tec>>base;in>>age;
      tecC=tec;for(int i=0;i<5;++i)rodC[i]=base;lastMeasurement=fakeNow;
      engine.update(fakeNow,tec,base,age);applyOutput();printMeasurement(fakeNow);
    } else if(line.rfind("@SCAN ",0)==0) {
      fakeNow=std::stoul(line.substr(6));loop();
    } else if(line=="@OVERFLOW") {
      std::string huge(200,'X'); huge+='\n';
      for(char c:huge)Serial.input.push_back(c);
      readSerialCommands();printMeasurement(fakeNow);
    } else {
      std::vector<char> text(line.begin(),line.end());text.push_back(0);command(text.data());
    }
  }
}
