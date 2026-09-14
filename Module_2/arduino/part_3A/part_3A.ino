const int TRIM_POT_PIN = A1;
const int DIRECTION_PIN = 11;

const int RPWM_PIN = 9;
const int LPWM_PIN = 10;

const int SAMPLE_COUNT = 100;

unsigned long lastPrintTime = 0;
const unsigned long PRINT_INTERVAL_MS = 500;

float averageAnalogRead(int pin) {
  unsigned long total = 0;

  for (int i = 0; i < SAMPLE_COUNT; i++) {
    total += analogRead(pin);
  }

  return total / float(SAMPLE_COUNT);
}

int adcToPwm(float averageAdc) {
  int pwmCommand =
      int(averageAdc * 255.0 / 1023.0 + 0.5);

  return constrain(pwmCommand, 0, 255);
}

void setBridgeCommand(int pwmCommand, bool heatMode) {
  analogWrite(RPWM_PIN, 0);
  analogWrite(LPWM_PIN, 0);

  if (pwmCommand == 0) {
    return;
  }

  if (heatMode) {
    // Heat / clockwise
    analogWrite(RPWM_PIN, pwmCommand);
  } else {
    // Cool / counterclockwise
    analogWrite(LPWM_PIN, pwmCommand);
  }
}

void printStatus(
    float averagePotAdc,
    int pwmCommand,
    bool heatMode) {

  Serial.print("pot ADC = ");
  Serial.print(averagePotAdc, 1);

  Serial.print("    PWM = ");
  Serial.print(pwmCommand);

  Serial.print("    duty cycle = ");
  Serial.print(100.0 * pwmCommand / 255.0, 1);
  Serial.print("%");

  Serial.print("    mode = ");

  if (heatMode) {
    Serial.print("heat / clockwise");
    Serial.print("    D9 = ");
    Serial.print(pwmCommand);
    Serial.println("    D10 = 0");
  } else {
    Serial.print("cool / counterclockwise");
    Serial.print("    D9 = 0");
    Serial.print("    D10 = ");
    Serial.println(pwmCommand);
  }
}

void setup() {
  Serial.begin(9600);

  pinMode(DIRECTION_PIN, INPUT);
  pinMode(RPWM_PIN, OUTPUT);
  pinMode(LPWM_PIN, OUTPUT);

  analogWrite(RPWM_PIN, 0);
  analogWrite(LPWM_PIN, 0);

  Serial.println("Part 3A: trim-pot and H-bridge command test");
}

void loop() {
  float averagePotAdc =
      averageAnalogRead(TRIM_POT_PIN);

  int pwmCommand =
      adcToPwm(averagePotAdc);

  bool heatMode =
      digitalRead(DIRECTION_PIN) == HIGH;

  setBridgeCommand(pwmCommand, heatMode);

  unsigned long currentTime = millis();

  if (currentTime - lastPrintTime >= PRINT_INTERVAL_MS) {
    lastPrintTime = currentTime;

    printStatus(
        averagePotAdc,
        pwmCommand,
        heatMode);
  }
}