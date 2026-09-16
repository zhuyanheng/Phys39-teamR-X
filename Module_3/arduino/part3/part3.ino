#include <math.h>

// Arduino pins
const int THERMISTOR_PIN = A0;
const int TRIM_POT_PIN = A1;
const int DIRECTION_PIN = 11;

const int PWM_PIN_9 = 9;
const int PWM_PIN_10 = 10;

// Thermistor parameters
const float VREF = 5.00;
const float FIXED_RESISTOR = 100000.0;
const float NOMINAL_RESISTANCE = 100000.0;
const float NOMINAL_TEMPERATURE_K = 298.15;
const float THERMISTOR_BETA = 4540.0;

// Sampling and reporting settings
const int SAMPLE_COUNT = 1000;
const unsigned long REPORT_INTERVAL_MS = 500;

unsigned long lastReportTime = 0;

// Return the average of multiple analog readings.
float averageAnalogRead(int pin) {
  unsigned long total = 0;

  for (int i = 0; i < SAMPLE_COUNT; i++) {
    total += analogRead(pin);
  }

  return total / float(SAMPLE_COUNT);
}

// Convert the averaged ADC reading to voltage.
float adcToVoltage(float averageAdc) {
  return averageAdc * VREF / 1023.0;
}

// Convert the divider voltage to thermistor resistance.
float voltageToResistance(float voltage) {
  if (voltage <= 0.0 || voltage >= VREF) {
    return NAN;
  }

  return FIXED_RESISTOR * voltage / (VREF - voltage);
}

// Convert thermistor resistance to degrees Celsius.
float resistanceToCelsius(float resistance) {
  if (resistance <= 0.0 || isnan(resistance)) {
    return NAN;
  }

  float inverseTemperature =
      1.0 / NOMINAL_TEMPERATURE_K
      + log(resistance / NOMINAL_RESISTANCE)
          / THERMISTOR_BETA;

  float temperatureK = 1.0 / inverseTemperature;

  return temperatureK - 273.15;
}

// Convert the potentiometer ADC value to PWM 0-255.
int adcToPwm(float averageAdc) {
  int pwmCommand =
      int(averageAdc * 255.0 / 1023.0 + 0.5);

  return constrain(pwmCommand, 0, 255);
}

// Apply PWM to the selected H-bridge input.
void setBridgeCommand(int pwmCommand, bool heatMode) {
  analogWrite(PWM_PIN_9, 0);
  analogWrite(PWM_PIN_10, 0);

  if (pwmCommand == 0) {
    return;
  }

  if (heatMode) {
    analogWrite(PWM_PIN_9, pwmCommand);
  } else {
    analogWrite(PWM_PIN_10, pwmCommand);
  }
}

// Print only the important values.
void printStatus(
    float temperatureC,
    float timeSeconds,
    float thermistorVoltage,
    int pwmCommand,
    bool heatMode) {

  Serial.print("Temperature (C): ");
  Serial.print(temperatureC, 2);

  Serial.print(", Time (s): ");
  Serial.print(timeSeconds, 2);

  Serial.print(", Voltage (V): ");
  Serial.print(thermistorVoltage, 3);

  Serial.print(", PWM: ");
  Serial.print(pwmCommand);

  Serial.print(", Heat/Cool: ");
  Serial.println(heatMode ? 1 : 0);
}

void setup() {
  pinMode(THERMISTOR_PIN, INPUT);
  pinMode(TRIM_POT_PIN, INPUT);
  pinMode(DIRECTION_PIN, INPUT);

  pinMode(PWM_PIN_9, OUTPUT);
  pinMode(PWM_PIN_10, OUTPUT);

  // Start with both H-bridge outputs at zero.
  analogWrite(PWM_PIN_9, 0);
  analogWrite(PWM_PIN_10, 0);

  Serial.begin(9600);
}

void loop() {
  // Read the potentiometer and calculate PWM.
  float averagePotAdc =
      averageAnalogRead(TRIM_POT_PIN);

  int pwmCommand =
      adcToPwm(averagePotAdc);

  // D11 HIGH selects HEAT; D11 LOW selects COOL.
  bool heatMode =
      digitalRead(DIRECTION_PIN) == HIGH;

  setBridgeCommand(pwmCommand, heatMode);

  unsigned long currentTime = millis();

  if (currentTime - lastReportTime >= REPORT_INTERVAL_MS) {
    lastReportTime = currentTime;

    float averageThermistorAdc =
        averageAnalogRead(THERMISTOR_PIN);

    float thermistorVoltage =
        adcToVoltage(averageThermistorAdc);

    float thermistorResistance =
        voltageToResistance(thermistorVoltage);

    float temperatureC =
        resistanceToCelsius(thermistorResistance);

    float timeSeconds =
        currentTime / 1000.0;

    printStatus(
        temperatureC,
        timeSeconds,
        thermistorVoltage,
        pwmCommand,
        heatMode);
  }
}