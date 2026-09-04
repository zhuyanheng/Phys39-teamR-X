/*
 * Part 1 - Blink with 1:10 Duty Cycle (HIGH:LOW = 1:10)
 * 
 * For oscilloscope measurement:
 * Record: High voltage, Low voltage, Period, Frequency, Duty Cycle
 * Expected duty cycle: ~9.09%
 */

const int ledPin = 9;  

void setup() {
  pinMode(ledPin, OUTPUT);
}

void loop() {
  digitalWrite(ledPin, HIGH);
  delay(100);   // HIGH for 100 ms
  
  digitalWrite(ledPin, LOW);
  delay(1000);  // LOW for 1000 ms
  
  // Duty cycle = HIGH / (HIGH + LOW) = 100/(100+1000) ≈ 9.09% = 1:10
}