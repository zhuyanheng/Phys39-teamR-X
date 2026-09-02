/*
 * Part 1 - Blink with 1:1 Duty Cycle (HIGH:LOW = 1:1)
 * 
 * For oscilloscope measurement:
 * Record: High voltage, Low voltage, Period, Frequency, Duty Cycle
 * Expected duty cycle: 50%
 */

const int ledPin = 13;  // Built-in LED, or use pin 9 for external LED

void setup() {
  pinMode(ledPin, OUTPUT);
}

void loop() {
  digitalWrite(ledPin, HIGH);
  delay(500);  // HIGH for 500 ms
  
  digitalWrite(ledPin, LOW);
  delay(500);  // LOW for 500 ms
  
  // Duty cycle = HIGH / (HIGH + LOW) = 500/(500+500) = 50% = 1:1
}