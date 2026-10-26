#include <math.h>
#include <string.h>

// Module 7 six-channel rod instrument.
//
// Copied from Module_6/arduino/p_only_tec/p_only_tec.ino. The actuator path,
// command protocol, and TEC safety logic are unchanged so that Module 6 remains
// a verified checkpoint. Two things are added:
//
//   1. Five measurement-only rod channels on A1..A5.
//   2. A machine-readable "DATA,..." report line instead of labeled text.
//
// The A0 channel is still the only PI feedback and the only software safety
// input. Rod channels never change the actuator output: a loose rod probe must
// not abort a 40-minute steady-state run.
//
// Column names below must stay in sync with Module_7/python/rod_protocol.py.

// Channel map
const int TEC_THERMISTOR_PIN = A0;   // TEC base: feedback + software limit
const int ROD_COUNT = 5;
const int ROD_PINS[ROD_COUNT] = {A1, A2, A3, A4, A5};  // rod 1 first, near x = 0

// Arduino pins
const int HEAT_PWM_PIN = 9;
const int COOL_PWM_PIN = 10;

// Thermistor parameters (identical divider and beta to Module 6)
const float VREF = 5.00;
const float FIXED_RESISTOR = 100000.0;
const float NOMINAL_RESISTANCE = 100000.0;
const float NOMINAL_TEMPERATURE_K = 298.15;
const float THERMISTOR_BETA = 4540.0;

// Sampling and reporting settings.
// One analogRead takes about 112 us on a 16 MHz AVR, so one full sweep costs
// 1000*112 us (TEC) + 5*100*112 us (rods) = about 168 ms. That keeps the 500 ms
// report period intact, which the step response needs. Do not raise
// ROD_SAMPLE_COUNT without rechecking the sweep time against the report period.
const int TEC_SAMPLE_COUNT = 1000;
const int ROD_SAMPLE_COUNT = 100;
const unsigned long REPORT_INTERVAL_MS = 500;

// Software safety limit (Part 1 requirement, unchanged from Module 6)
const float SOFTWARE_TEMPERATURE_LIMIT_C = 60.0;

// A rod channel outside this window is reported as nan and does not count
// toward rod_ok. The window is wide: valid runs stay inside 20..55 C.
const float ROD_PLAUSIBLE_MIN_C = -20.0;
const float ROD_PLAUSIBLE_MAX_C = 90.0;

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

// Return the average of multiple ADC readings on one pin.
float averageThermistorAdc(int pin, int sampleCount) {
  unsigned long total = 0;

  for (int i = 0; i < sampleCount; i++) {
    total += analogRead(pin);
  }

  return total / float(sampleCount);
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

// Full conversion chain for one channel.
float readCelsius(int pin, int sampleCount) {
  float averageAdc = averageThermistorAdc(pin, sampleCount);
  float voltage = adcToVoltage(averageAdc);
  float resistance = voltageToResistance(voltage);

  return resistanceToCelsius(resistance);
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

// Parse one complete command from Python. Protocol unchanged from Module 6.
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

// Print one temperature, or the literal nan when the reading is unusable.
// Python's float() accepts both, so a missing probe never corrupts a column.
void printCelsius(float temperatureC) {
  if (!isfinite(temperatureC)) {
    Serial.print("nan");
    return;
  }

  Serial.print(temperatureC, 2);
}

// Print the column names once at startup so a raw log is self-describing.
// The leading # keeps it out of the measurement stream.
void printHeader() {
  Serial.print("#DATA,time_s,tec_C");

  for (int i = 0; i < ROD_COUNT; i++) {
    Serial.print(",rod");
    Serial.print(i + 1);
    Serial.print("_C");
  }

  Serial.println(",pwm,heat_cool,heat_pwm,cool_pwm,limit_C,safety,rod_ok");
}

// Print build and wiring identifiers: C5 evidence for which firmware ran.
void printBanner() {
  Serial.println("#firmware,module_07_rod_controller,2026-10-26");
  Serial.println("#channels,tec=A0,rod1=A1,rod2=A2,rod3=A3,rod4=A4,rod5=A5");
  Serial.println("#pins,heat=D9,cool=D10,baud=9600,report_ms=500");
}

// Print the standard measurement line.
// Fields after DATA: time, TEC, rod 1..5, PWM, direction, firmware HEAT PWM,
// firmware COOL PWM, limit, safety, number of valid rod channels.
void printMeasurement(
    float tecC,
    const float rodC[ROD_COUNT],
    float timeSeconds,
    int validRodChannels) {

  Serial.print("DATA,");
  Serial.print(timeSeconds, 2);
  Serial.print(",");
  printCelsius(tecC);

  for (int i = 0; i < ROD_COUNT; i++) {
    Serial.print(",");
    printCelsius(rodC[i]);
  }

  Serial.print(",");
  Serial.print(commandedPwm);

  Serial.print(",");
  Serial.print(heatMode ? 1 : 0);

  // Firmware output values; these do not replace a physical pin measurement.
  Serial.print(",");
  Serial.print(safetyShutdownActive || !heatMode ? 0 : commandedPwm);
  Serial.print(",");
  Serial.print(safetyShutdownActive || heatMode ? 0 : commandedPwm);

  Serial.print(",");
  Serial.print(SOFTWARE_TEMPERATURE_LIMIT_C, 2);

  Serial.print(",");
  Serial.print(safetyShutdownActive ? "SHUTDOWN" : "OK");

  Serial.print(",");
  Serial.println(validRodChannels);
}

void setup() {
  pinMode(TEC_THERMISTOR_PIN, INPUT);

  for (int i = 0; i < ROD_COUNT; i++) {
    pinMode(ROD_PINS[i], INPUT);
  }

  pinMode(HEAT_PWM_PIN, OUTPUT);
  pinMode(COOL_PWM_PIN, OUTPUT);

  // Start with both H-bridge control outputs at zero.
  analogWrite(HEAT_PWM_PIN, 0);
  analogWrite(COOL_PWM_PIN, 0);

  commandedPwm = 0;
  heatMode = false;
  safetyShutdownActive = false;

  Serial.begin(9600);
  printBanner();
  printHeader();
}

void loop() {
  // Measure and check the TEC channel first, before accepting actuator
  // commands, so control latency is no worse than in Module 6.
  float tecC = readCelsius(TEC_THERMISTOR_PIN, TEC_SAMPLE_COUNT);

  // Stop for an invalid TEC reading or at the 60 C upper limit.
  safetyShutdownActive = !isfinite(tecC)
      || tecC >= SOFTWARE_TEMPERATURE_LIMIT_C;

  // When safety shutdown is active, force both PWM outputs to zero.
  if (safetyShutdownActive) {
    commandedPwm = 0;
    analogWrite(HEAT_PWM_PIN, 0);
    analogWrite(COOL_PWM_PIN, 0);
  }

  readSerialCommands();

  // Sweep the rod channels. Unusable readings become nan and are counted so a
  // probe that fell out is visible in the log without stopping the run.
  float rodC[ROD_COUNT];
  int validRodChannels = 0;

  for (int i = 0; i < ROD_COUNT; i++) {
    float reading = readCelsius(ROD_PINS[i], ROD_SAMPLE_COUNT);

    if (isfinite(reading)
        && reading >= ROD_PLAUSIBLE_MIN_C
        && reading <= ROD_PLAUSIBLE_MAX_C) {
      rodC[i] = reading;
      validRodChannels++;
    } else {
      rodC[i] = NAN;
    }
  }

  unsigned long currentTime = millis();
  if (currentTime - lastReportTime >= REPORT_INTERVAL_MS) {
    lastReportTime = currentTime;
    printMeasurement(tecC, rodC, currentTime / 1000.0, validRodChannels);
  }
}

