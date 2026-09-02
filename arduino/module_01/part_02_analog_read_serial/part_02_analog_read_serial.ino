const int ANALOG_PIN = A0;
const unsigned long REPORT_INTERVAL_MS = 100;

void setup() {
  Serial.begin(9600);
}

void loop() {
  const int sensorValue = analogRead(ANALOG_PIN);
  Serial.println(sensorValue);
  delay(REPORT_INTERVAL_MS);
}
