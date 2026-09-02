const int ANALOG_PIN = A0;
const float V_REF_VOLTS = 5.00;
const int POINTS_PER_BLOCK = 100;
const int LONG_AVERAGE_SAMPLES = 1000;
const unsigned long PAUSE_BETWEEN_POINTS_MS = 20;

float readAverageAdcCount(int sampleCount) {
  unsigned long total = 0;

  for (int sampleIndex = 0; sampleIndex < sampleCount; sampleIndex++) {
    total += analogRead(ANALOG_PIN);
  }

  return total / float(sampleCount);
}

float adcCountToVoltage(float adcCount) {
  return V_REF_VOLTS * adcCount / 1023.0;
}

void printVoltagePoint(const char *modeName, int pointNumber, float voltage) {
  Serial.print(modeName);
  Serial.print("_Point_");
  Serial.print(pointNumber);
  Serial.print(" Voltage_V:");
  Serial.println(voltage, 4);
}

void printVoltageBlock(int sampleCount, const char *modeName) {
  for (int point = 1; point <= POINTS_PER_BLOCK; point++) {
    const float averageCount = readAverageAdcCount(sampleCount);
    const float voltage = adcCountToVoltage(averageCount);
    printVoltagePoint(modeName, point, voltage);
    delay(PAUSE_BETWEEN_POINTS_MS);
  }
}

void setup() {
  Serial.begin(9600);
  delay(1000);
}

void loop() {
  printVoltageBlock(1, "Ave1");
  printVoltageBlock(LONG_AVERAGE_SAMPLES, "Ave1000");
}
