# Phys39 teamR&X
Ricky & Xavier's work
- Ricky Huang
- Xavier Zhu

## Repository

https://github.com/zhuyanheng/Phys39-teamR-X

## Module 1: Arduino Measurements

This repository contains the Arduino sketches, measurement notes, figures, wiring documentation, data, and analysis files for Module 1.

## Arduino Sketches

- `arduino/module_01/part_01_blink/part_01_blink.ino`
  - Tests different LED blinking duty cycles.

- `arduino/module_01/part_02_analog_read_serial/part_02_analog_read_serial.ino`
  - Reads the raw ADC value from analog pin A0.

- `arduino/module_01/part_03a_adc_integer/part_03a_adc_integer.ino`
  - Displays integer ADC readings.

- `arduino/module_01/part_03b_adc_voltage/part_03b_adc_voltage.ino`
  - Converts ADC readings into voltage.

- `arduino/module_01/part_03c_averaging_comparison/part_03c_averaging_comparison.ino`
  - Compares single measurements with averages of 1000 measurements.

- `arduino/module_01/part_03d_averaging_timing/part_03d_averaging_timing.ino`
  - Measures the time required to average 1000 ADC readings.

- `arduino/module_01/part_04_averaged_adc_pwm_led/part_04_averaged_adc_pwm_led.ino`
  - Uses the averaged ADC measurement to control LED brightness with PWM.

## Hardware

- Arduino Uno
- Potentiometer
- LED
- Current-limiting resistor
- Breadboard
- Jumper wires

## Tested Sketches

All Module 1 sketches were verified, uploaded to an Arduino Uno, and tested with the appropriate hardware configuration:

- `arduino/module_01/part_01_blink/part_01_blink.ino`
- `arduino/module_01/part_02_analog_read_serial/part_02_analog_read_serial.ino`
- `arduino/module_01/part_03a_adc_integer/part_03a_adc_integer.ino`
- `arduino/module_01/part_03b_adc_voltage/part_03b_adc_voltage.ino`
- `arduino/module_01/part_03c_averaging_comparison/part_03c_averaging_comparison.ino`
- `arduino/module_01/part_03d_averaging_timing/part_03d_averaging_timing.ino`
- `arduino/module_01/part_04_averaged_adc_pwm_led/part_04_averaged_adc_pwm_led.ino`

### Test Results

- Part 1 successfully demonstrated the required LED blinking patterns and duty cycles.
- Part 2 successfully displayed raw analog input readings through serial communication.
- Part 3A successfully displayed integer ADC readings from analog pin A0.
- Part 3B successfully converted ADC readings into voltage.
- Part 3C successfully compared individual measurements with averages of 1000 measurements.
- Part 3D successfully measured the time required to collect and average 1000 ADC readings.
- Part 4 successfully used averaged ADC measurements to control LED brightness through PWM.

## How to Run a Sketch

1. Open the `.ino` file in Arduino IDE.
2. Select `Arduino Uno` under the board menu.
3. Select the Arduino serial port.
4. Click **Verify**.
5. Click **Upload**.
6. Open the Serial Monitor or Serial Plotter at `9600 baud` when required.

## Measurement Summary

Module 1 demonstrates ADC quantization, conversion from ADC values to voltage, reduction of measurement noise through averaging, the time cost of averaging, and PWM control of LED brightness.

## AI Use

AI tools were used to help organize files, explain Arduino code, and review documentation. All Arduino sketches were reviewed and tested by the team.