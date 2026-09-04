const int ANALOG_PIN = A0;
const unsigned long REPORT_INTERVAL_MS = 100;

void setup() {
  Serial.begin(9600);
}

void loop() {
  const int adcCount = analogRead(ANALOG_PIN);

  // Print one labeled integer quantity for Serial Monitor and Serial Plotter.
  Serial.print("ADC:");
  Serial.println(adcCount);

  delay(REPORT_INTERVAL_MS);
}
