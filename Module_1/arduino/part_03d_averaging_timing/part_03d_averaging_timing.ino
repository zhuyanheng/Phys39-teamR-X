const int ANALOG_PIN = A0;
const int SAMPLE_COUNT = 1000;
const float V_REF_VOLTS = 5.00;
const unsigned long PAUSE_BETWEEN_TRIALS_MS = 2000;

void setup() {
  Serial.begin(9600);
}

void loop() {
  unsigned long total = 0;

  // Time only the ADC acquisition loop.
  const unsigned long startTimeUs = micros();

  for (int sampleIndex = 0; sampleIndex < SAMPLE_COUNT; sampleIndex++) {
    total += analogRead(ANALOG_PIN);
  }

  const unsigned long elapsedTimeUs = micros() - startTimeUs;
  const float averageCount = total / float(SAMPLE_COUNT);
  const float averageVoltage =
      V_REF_VOLTS * averageCount / 1023.0;
  const float microsecondsPerConversion =
      elapsedTimeUs / float(SAMPLE_COUNT);
  const float conversionsPerSecond =
      SAMPLE_COUNT * 1000000.0 / elapsedTimeUs;

  Serial.println("--- Averaging timing trial ---");
  Serial.print("Samples = ");
  Serial.println(SAMPLE_COUNT);
  Serial.print("Elapsed_time_us = ");
  Serial.println(elapsedTimeUs);
  Serial.print("Time_per_conversion_us = ");
  Serial.println(microsecondsPerConversion, 2);
  Serial.print("Conversions_per_second = ");
  Serial.println(conversionsPerSecond, 1);
  Serial.print("Average_ADC_count = ");
  Serial.println(averageCount, 3);
  Serial.print("Average_voltage_V = ");
  Serial.println(averageVoltage, 4);
  Serial.println();

  delay(PAUSE_BETWEEN_TRIALS_MS);
}
