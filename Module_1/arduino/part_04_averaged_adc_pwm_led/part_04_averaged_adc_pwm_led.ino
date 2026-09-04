const int ANALOG_PIN = A0;
const int PWM_PIN = 9;
const int AVERAGE_SAMPLES = 1000;
const float V_REF_VOLTS = 5.00;
const unsigned long REPORT_INTERVAL_MS = 100;

float readAverageAdcCount() {
  unsigned long total = 0;

  for (int sampleIndex = 0; sampleIndex < AVERAGE_SAMPLES; sampleIndex++) {
    total += analogRead(ANALOG_PIN);
  }

  return total / float(AVERAGE_SAMPLES);
}

void setup() {
  pinMode(PWM_PIN, OUTPUT);
  analogWrite(PWM_PIN, 0);
  Serial.begin(9600);
}

void loop() {
  const float averageCount = readAverageAdcCount();
  const float averageVoltage =
      V_REF_VOLTS * averageCount / 1023.0;

  int pwmValue = round(averageCount * 255.0 / 1023.0);
  pwmValue = constrain(pwmValue, 0, 255);
  analogWrite(PWM_PIN, pwmValue);

  Serial.print("Average_ADC:");
  Serial.print(averageCount, 3);
  Serial.print(" Voltage_V:");
  Serial.print(averageVoltage, 4);
  Serial.print(" PWM_value:");
  Serial.print(pwmValue);
  Serial.print(" Expected_duty_percent:");
  Serial.println(100.0 * pwmValue / 255.0, 2);

  delay(REPORT_INTERVAL_MS);
}
