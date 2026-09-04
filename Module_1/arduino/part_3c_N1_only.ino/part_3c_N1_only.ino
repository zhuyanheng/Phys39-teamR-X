/*
 * Part 3C - N=1 Only (for min discrete voltage jump estimation)
 * 
 * This sketch continuously outputs N=1 (single reading) data.
 * Use this to capture a Serial Plotter screenshot showing only
 * the unaveraged "rough" data.
 */

void setup() {
  Serial.begin(9600);
}

void loop() {
  int sensorValue = analogRead(A0);
  float voltage = sensorValue * (5.0 / 1023.0);
  

  Serial.print("N1 ");
  Serial.println(voltage, 6);
  delay(10);
}