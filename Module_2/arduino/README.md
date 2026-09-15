# Module 2 Arduino Sketches

This directory contains the Arduino sketches used for the Module 2 experiments.
Each sketch is stored in a folder with the same name as its `.ino` file.

## Sketches

| Part | Sketch | Purpose |
|---|---|---|
| Part 1 | [Thermistor Serial Data](./part_1/part_1.ino) | Reads thermistor on A0, averages ADC samples, converts to voltage, resistance, and temperature using the Beta model, and prints human-readable serial output. |
| Part 2 | [Serial Plotter Output](./part_2/part_2.ino) | Modified from Part 1 to output only the temperature value (one decimal place) per line for Arduino Serial Plotter. |
| Part 3 | [Trim-Pot PWM and H-Bridge Control](./part_3/part_3.ino) | Uses trim-pot on A1 to set PWM duty cycle and a direction switch on pin 11 to select heat/cool. Outputs PWM to H-bridge pins 9 (RPWM) and 10 (LPWM) with proper interlock. Includes serial status output for verification. |

## Hardware Connections

### Thermistor Voltage Divider (Part 1 & Part 2)

| Component | Arduino connection |
|---|---|
| Fixed resistor (100 kΩ) | 5V to A0 |
| Thermistor (100 kΩ NTC) | A0 to GND |
| Thermistor wiper | A0 |

### Trim-Pot (Part 3)

| Potentiometer terminal | Arduino connection |
|---|---|
| Outer terminal | 5 V |
| Other outer terminal | GND |
| Center wiper | A1 |

### Direction Switch (Part 3)

| Switch terminal | Arduino connection |
|---|---|
| Common (center) | Pin 11 |
| Throw 1 | 5 V (Heat / Clockwise) |
| Throw 2 | GND (Cool / Counterclockwise) |

Alternatively, use `INPUT_PULLUP` and connect switch between pin 11 and GND (logic inverted in code).

### H-Bridge (Part 3)

| H-Bridge pin | Arduino connection |
|---|---|
| RPWM | Pin 9 |
| LPWM | Pin 10 |
| VCC | 5 V |
| R_EN | 5 V |
| L_EN | 5 V |
| GND | GND |

Motor connects to M+ and M-. External 12 V supply connects to B+ and B-.

## Usage

1. Open the selected sketch in Arduino IDE.
2. Select **Arduino Uno**.
3. Select the correct serial port.
4. Click **Verify**.
5. Click **Upload**.
6. Open Serial Monitor or Serial Plotter at `9600 baud`.

- For Part 1, use Serial Monitor to view human-readable measurements.
- For Part 2, use Serial Plotter to view temperature vs. read order.
- For Part 3, use Serial Monitor to verify PWM and direction commands. Use an oscilloscope to check pin 9 and 10 signals before connecting the motor and 12 V supply.

## Notes

- The sketches assume a nominal ADC reference voltage of 5.00 V.
- The Arduino Uno ADC produces 1024 possible integer codes, from 0 through 1023.
- Part 1 and Part 2 use the same thermistor constants: $R_0 = 100\,\text{k}\Omega$, $T_0 = 298.15\,\text{K}$, $\beta = 4540\,\text{K}$.
- Part 3 uses `analogWrite()` on pins 9 and 10. Only one pin is active at a time to prevent H-bridge shoot-through.
- Always verify H-bridge command signals with the oscilloscope before connecting the motor or TEC. Keep the TEC disconnected throughout Module 2.
- For the motor test in Part 3C, start with PWM = 0, turn on actuator power only after instructor check, and stop immediately if anything becomes warm.