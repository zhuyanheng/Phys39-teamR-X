const int LED_PIN = LED_BUILTIN;

// Select 0 for 1:1, 1 for 10:1, or 2 for 1:10 HIGH:LOW timing.
const int TIMING_MODE = 0;
const unsigned long HIGH_TIMES_MS[] = {500, 1000, 100};
const unsigned long LOW_TIMES_MS[] = {500, 100, 1000};

void setup() {
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_PIN, HIGH);
  delay(HIGH_TIMES_MS[TIMING_MODE]);

  digitalWrite(LED_PIN, LOW);
  delay(LOW_TIMES_MS[TIMING_MODE]);
}
