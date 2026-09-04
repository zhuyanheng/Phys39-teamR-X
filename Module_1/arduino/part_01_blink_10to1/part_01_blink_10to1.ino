/*
 * Part 1 - Blink with 10:1 Duty Cycle (HIGH:LOW = 10:1)
 * 
 * For oscilloscope measurement:
 * Record: High voltage, Low voltage, Period, Frequency, Duty Cycle
 * Expected duty cycle: ~90.9%
 */

const int ledPin = 9;  

void setup() {
  pinMode(ledPin, OUTPUT);
}

void loop() {
  digitalWrite(ledPin, HIGH);
  delay(1000);  // HIGH for 1000 ms
  
  digitalWrite(ledPin, LOW);
  delay(100);   // LOW for 100 ms
  
  // Duty cycle = HIGH / (HIGH + LOW) = 1000/(1000+100) ≈ 90.9% = 10:1
}