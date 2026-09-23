#include <math.h>
#include <string.h>

// Arduino pins
const int THERMISTOR_PIN = A0;
const int HEAT_PWM_PIN = 9;
const int COOL_PWM_PIN = 10;

// Thermistor parameters
const float VREF = 5.00;
const float FIXED_RESISTOR = 100000.0;
const float NOMINAL_RESISTANCE = 100000.0;
const float NOMINAL_TEMPERATURE_K = 298.15;
const float THERMISTOR_BETA = 4540.0;

// Sampling and reporting settings
const int SAMPLE_COUNT = 1000;
const unsigned long REPORT_INTERVAL_MS = 500;

// Software safety limit (Part 1 requirement)
const float SOFTWARE_TEMPERATURE_LIMIT_C = 60.0;

// Serial command buffer
const int COMMAND_BUFFER_SIZE = 48;
char commandBuffer[COMMAND_BUFFER_SIZE];
int commandLength = 0;
bool commandOverflow = false;

// Current command state
int commandedPwm = 0;
bool heatMode = false;

// Safety shutdown state
bool safetyShutdownActive = false;

unsigned long lastReportTime = 0;

// Return the average of multiple thermistor ADC readings.
float averageThermistorAdc() {
  unsigned long total = 0;

  for (int i = 0; i < SAMPLE_COUNT; i++) {
    total += analogRead(THERMISTOR_PIN);
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

// Apply the current command using the experimentally verified mapping.
void applyBridgeCommand() {
  // If safety shutdown is active, force both outputs off and return.
  if (safetyShutdownActive) {
    analogWrite(HEAT_PWM_PIN, 0);
    analogWrite(COOL_PWM_PIN, 0);
    return;
  }

  // Turn both directions off before applying a new command.
  analogWrite(HEAT_PWM_PIN, 0);
  analogWrite(COOL_PWM_PIN, 0);

  if (commandedPwm == 0) {
    return;
  }

  if (heatMode) {
    analogWrite(HEAT_PWM_PIN, commandedPwm);
  } else {
    analogWrite(COOL_PWM_PIN, commandedPwm);
  }
}

// Parse one complete command from Python.
void processCommand(const char* command) {
  int requestedPwm;
  char requestedDirection[8];

  int matchedFields = sscanf(
      command,
      "SET PWM %d DIR %7s",
      &requestedPwm,
      requestedDirection);

  if (matchedFields != 2) {
    return;
  }

  bool requestedHeatMode;

  if (strcmp(requestedDirection, "HEAT") == 0) {
    requestedHeatMode = true;
  } else if (strcmp(requestedDirection, "COOL") == 0) {
    requestedHeatMode = false;
  } else {
    return;
  }

  // If safety shutdown is active, ignore any non-zero PWM command.
  if (safetyShutdownActive && requestedPwm > 0) {
    return;
  }

  // Disable both outputs before changing PWM or direction.
  analogWrite(HEAT_PWM_PIN, 0);
  analogWrite(COOL_PWM_PIN, 0);

  commandedPwm = constrain(requestedPwm, 0, 255);
  heatMode = requestedHeatMode;

  applyBridgeCommand();
}

// Collect newline-terminated serial commands without using String objects.
void readSerialCommands() {
  while (Serial.available() > 0) {
    char incomingCharacter = Serial.read();

    if (incomingCharacter == '\r') {
      continue;
    }

    if (incomingCharacter == '\n') {
      if (!commandOverflow && commandLength > 0) {
        commandBuffer[commandLength] = '\0';
        processCommand(commandBuffer);
      }

      commandLength = 0;
      commandOverflow = false;
      continue;
    }

    if (commandOverflow) {
      continue;
    }

    if (commandLength < COMMAND_BUFFER_SIZE - 1) {
      commandBuffer[commandLength] = incomingCharacter;
      commandLength++;
    } else {
      commandLength = 0;
      commandOverflow = true;
    }
  }
}

// Print the standard Arduino-Python measurement line.
// Added Safety field so the serial output clearly reports shutdown state.
void printMeasurement(
    float temperatureC,
    float timeSeconds) {

  Serial.print("Temperature (C): ");
  Serial.print(temperatureC, 2);

  Serial.print(", Time (s): ");
  Serial.print(timeSeconds, 2);

  Serial.print(", PWM: ");
  Serial.print(commandedPwm);

  Serial.print(", Heat/Cool: ");
  Serial.print(heatMode ? 1 : 0);

  Serial.print(", Safety: ");
  Serial.print(safetyShutdownActive ? "SHUTDOWN" : "OK");
  // Firmware output values; these do not replace a physical pin measurement.
  Serial.print(", Heat PWM: ");
  Serial.print(safetyShutdownActive || !heatMode ? 0 : commandedPwm);
  Serial.print(", Cool PWM: ");
  Serial.print(safetyShutdownActive || heatMode ? 0 : commandedPwm);
  Serial.print(", Limit (C): ");
  Serial.println(SOFTWARE_TEMPERATURE_LIMIT_C, 2);
}

void setup() {
  pinMode(THERMISTOR_PIN, INPUT);
  pinMode(HEAT_PWM_PIN, OUTPUT);
  pinMode(COOL_PWM_PIN, OUTPUT);

  // Start with both H-bridge control outputs at zero.
  analogWrite(HEAT_PWM_PIN, 0);
  analogWrite(COOL_PWM_PIN, 0);

  commandedPwm = 0;
  heatMode = false;
  safetyShutdownActive = false;

  Serial.begin(9600);
}

void loop() {
  // Measure and check safety every loop, before accepting actuator commands.
  float averageAdc = averageThermistorAdc();
  float voltage = adcToVoltage(averageAdc);
  float resistance = voltageToResistance(voltage);
  float temperatureC = resistanceToCelsius(resistance);
  // Invalid sensor readings also force the actuator off.
  safetyShutdownActive = !isfinite(temperatureC)
      || temperatureC > SOFTWARE_TEMPERATURE_LIMIT_C;

  // When safety shutdown is active, force both PWM outputs to zero.
  if (safetyShutdownActive) {
    commandedPwm = 0;
    analogWrite(HEAT_PWM_PIN, 0);
    analogWrite(COOL_PWM_PIN, 0);
  }

  readSerialCommands();

  unsigned long currentTime = millis();
  if (currentTime - lastReportTime >= REPORT_INTERVAL_MS) {
    lastReportTime = currentTime;
    printMeasurement(temperatureC, currentTime / 1000.0);
  }
}
