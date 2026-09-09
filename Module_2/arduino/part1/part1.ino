#include <math.h>

const int THERMISTOR_PIN = A0;

const float VREF = 5.00;
const float FIXED_RESISTOR = 100000.0;       // ohm
const float NOMINAL_RESISTANCE = 100000.0;   // R at 25 C
const float NOMINAL_TEMPERATURE_K = 298.15;  // 25 C in kelvin
const float BETA = 4540.0;                   // kelvin

const int SAMPLE_COUNT = 100;

const unsigned long REPORT_INTERVAL_MS = 500;
unsigned long lastReportMs = 0;

float averageAdcSamples() {
  unsigned long total = 0;

  for (int i = 0; i < SAMPLE_COUNT; i++) {
    total += analogRead(THERMISTOR_PIN);
  }

  return total / float(SAMPLE_COUNT);
}

float adcToVoltage(float averageAdc) {
  return averageAdc * VREF / 1023.0;
}

float voltageToResistance(float voltage) {
  if (voltage <= 0.0 || voltage >= VREF) {
    return NAN;
  }

  return FIXED_RESISTOR * voltage / (VREF - voltage);
}

float resistanceToCelsius(float resistance) {
  if (resistance <= 0.0) {
    return NAN;
  }

  float inverseTemperature =
      1.0 / NOMINAL_TEMPERATURE_K
      + log(resistance / NOMINAL_RESISTANCE) / BETA;

  float temperatureK = 1.0 / inverseTemperature;
  return temperatureK - 273.15;
}

void printHumanReadable(
    float timeSeconds,
    float averageAdc,
    float voltage,
    float resistance,
    float temperatureC) {

  Serial.print("time = ");
  Serial.print(timeSeconds, 2);
  Serial.print(" s    average ADC = ");
  Serial.print(averageAdc, 1);
  Serial.print("    voltage = ");
  Serial.print(voltage, 3);
  Serial.print(" V    resistance = ");
  Serial.print(resistance / 1000.0, 2);
  Serial.print(" kOhm    temperature = ");
  Serial.print(temperatureC, 1);
  Serial.print(" C    samples = ");
  Serial.println(SAMPLE_COUNT);
}

void setup() {
  Serial.begin(9600);
  Serial.println("Thermistor temperature measurement");
}

void loop() {
  unsigned long now = millis();

  if (now - lastReportMs < REPORT_INTERVAL_MS) {
    return;
  }

  lastReportMs = now;

  float averageAdc = averageAdcSamples();
  float voltage = adcToVoltage(averageAdc);
  float resistance = voltageToResistance(voltage);
  float temperatureC = resistanceToCelsius(resistance);
  float timeSeconds = now / 1000.0;

  printHumanReadable(
      timeSeconds,
      averageAdc,
      voltage,
      resistance,
      temperatureC);
}