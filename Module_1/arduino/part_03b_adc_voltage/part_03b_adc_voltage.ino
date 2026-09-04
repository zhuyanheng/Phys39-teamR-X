const float V_REF_VOLTS = 5.00;

void setup() {
  Serial.begin(9600);
}

void loop() {
  int adcCount = analogRead(A0);

  float voltage = V_REF_VOLTS * adcCount / 1023.0;

  Serial.print("Voltage_V:");
  Serial.println(voltage, 4);

  delay(100);
}
