# Phys 39 Team R&X

Team members:

- Ricky Huang
- Xavier Zhu

## Repository

[Phys39 Team R&X GitHub Repository](https://github.com/zhuyanheng/Phys39-teamR-X)

## Module 1: Arduino Measurements

This repository contains the Arduino sketches, experimental data, figures,
measurement notes, and analysis used for Module 1.

- [Module 1 Arduino documentation](Module_1/arduino/README.md)
- [Module 1 data documentation](Module_1/data/README.md)
- [Part 3C quantitative analysis](Module_1/data/analysis_3c_ab.md)
- [A1 Module 1 evidence note](docs/module_notes/module_01_evidence.md)

## Arduino Sketches

### Part 1: Blink and Digital Output

- [Blink with 1:1 HIGH:LOW ratio](Module_1/arduino/part_01_blink_1to1/part_01_blink_1to1.ino)
- [Blink with 1:10 HIGH:LOW ratio](Module_1/arduino/part_01_blink_1to10/part_01_blink_1to10.ino)
- [Blink with 10:1 HIGH:LOW ratio](Module_1/arduino/part_01_blink_10to1/part_01_blink_10to1.ino)

### Part 2: AnalogReadSerial

- [AnalogReadSerial](Module_1/arduino/part_02_analog_read_serial/part_02_analog_read_serial.ino)

### Part 3: ADC Digitization and Averaging

- [Part 3A: Integer ADC readings](Module_1/arduino/part_03a_adc_integer/part_03a_adc_integer.ino)
- [Part 3B: ADC-to-voltage conversion](Module_1/arduino/part_03b_adc_voltage/part_03b_adc_voltage.ino)
- [Part 3C: N=1 and N=1000 averaging comparison](Module_1/arduino/part_03c_averaging_comparison/part_03c_averaging_comparison.ino)
- [Part 3D: ADC acquisition timing](Module_1/arduino/part_03d_averaging_timing/part_03d_averaging_timing.ino)

### Part 4: PWM LED Control

- [Averaged ADC input controlling LED PWM](Module_1/arduino/part_04_averaged_adc_pwm_led/part_04_averaged_adc_pwm_led.ino)

## Experimental Data

- [N=1 voltage data](Module_1/data/part_3c_N1_data.csv)
- [N=1000 averaged voltage data](Module_1/data/part_3c_N1000_data.csv)
- [Part 3C data analysis](Module_1/data/analysis_3c_ab.md)

## Hardware

- Arduino Uno
- 100 kΩ potentiometer
- LED
- Current-limiting resistor
- Breadboard
- Jumper wires
- Oscilloscope and probe

## Tested Capabilities

The team uploaded and tested the Module 1 sketches on an Arduino Uno.

- The three Part 1 sketches produced the intended HIGH:LOW timing ratios.
- Part 2 reported raw analog-input values over the serial connection.
- Part 3A reported discrete integer ADC values.
- Part 3B converted ADC values to voltage.
- Part 3C compared single readings with 1000-reading averages.
- Part 3D measured the time required for 1000 ADC conversions.
- Part 4 used the averaged potentiometer input to control LED brightness with PWM.

## How to Run a Sketch

1. Open the selected `.ino` file in Arduino IDE.
2. Select `Arduino Uno` as the board.
3. Select the correct serial port.
4. click **Verify**.
5. click **Upload**.
6. Open Serial Monitor or Serial Plotter at `9600 baud` when required.

## AI Use

AI tools were used to help organize files, check calculations, explain Arduino
code, and review documentation. The team reviewed and tested the submitted
Arduino sketches and remains responsible for the final results.
