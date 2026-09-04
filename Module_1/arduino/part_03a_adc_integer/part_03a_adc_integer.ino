void setup() {
  Serial.begin(9600);
}

void loop() {
  int adcCount = analogRead(A0);

  Serial.print("ADC:");
  Serial.println(adcCount);

  delay(100);
}