const int ANALOG_PIN = A0;
const float V_REF_VOLTS = 5.00;
const unsigned long REPORT_INTERVAL_MS = 100;

void setup() {
  Serial.begin(9600);
}

void loop() {
  const int adcCount = analogRead(ANALOG_PIN);
  const float voltage = V_REF_VOLTS * adcCount / 1023.0;

  // Displaying four decimals does not increase the physical ADC resolution.
  Serial.print("Voltage_V:");
  Serial.println(voltage, 4);

  delay(REPORT_INTERVAL_MS);
}
