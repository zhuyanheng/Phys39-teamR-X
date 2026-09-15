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

### Module 1 Arduino Sketches

#### Part 1: Blink and Digital Output

- [Blink with 1:1 HIGH:LOW ratio](Module_1/arduino/part_01_blink_1to1/part_01_blink_1to1.ino)
- [Blink with 1:10 HIGH:LOW ratio](Module_1/arduino/part_01_blink_1to10/part_01_blink_1to10.ino)
- [Blink with 10:1 HIGH:LOW ratio](Module_1/arduino/part_01_blink_10to1/part_01_blink_10to1.ino)

#### Part 2: AnalogReadSerial

- [AnalogReadSerial](Module_1/arduino/part_02_analog_read_serial/part_02_analog_read_serial.ino)

#### Part 3: ADC Digitization and Averaging

- [Part 3A: Integer ADC readings](Module_1/arduino/part_03a_adc_integer/part_03a_adc_integer.ino)
- [Part 3B: ADC-to-voltage conversion](Module_1/arduino/part_03b_adc_voltage/part_03b_adc_voltage.ino)
- [Part 3C: N=1 and N=1000 averaging comparison](Module_1/arduino/part_03c_averaging_comparison/part_03c_averaging_comparison.ino)
- [Part 3D: ADC acquisition timing](Module_1/arduino/part_03d_averaging_timing/part_03d_averaging_timing.ino)

#### Part 4: PWM LED Control

- [Averaged ADC input controlling LED PWM](Module_1/arduino/part_04_averaged_adc_pwm_led/part_04_averaged_adc_pwm_led.ino)

### Module 1 Experimental Data

- [N=1 voltage data](Module_1/data/part_3c_N1_data.csv)
- [N=1000 averaged voltage data](Module_1/data/part_3c_N1000_data.csv)
- [Part 3C data analysis](Module_1/data/analysis_3c_ab.md)

## Module 2: First Real Instrument Pieces

This repository contains the Arduino sketches, figures, and evidence note
for Module 2: thermistor temperature measurement, Serial Plotter output,
trim-pot PWM control, H-bridge logic verification, and DC motor drive.

- [Module 2 Arduino documentation](Module_2/arduino/README.md)
- [Module 2 evidence note](docs/module_notes/module_02_instrument_pieces.md)

### Module 2 Arduino Sketches

- [Part 1: Thermistor Serial Data and Temperature Conversion](Module_2/arduino/part_1/part_1.ino)
- [Part 2: Serial Plotter Output](Module_2/arduino/part_2/part_2.ino)
- [Part 3: Trim-Pot PWM and H-Bridge Control](Module_2/arduino/part_3/part_3.ino)

### Module 2 Figures

- [Part 1 Serial Output](Module_2/figures/part_1.png)
- [Part 2 Serial Plotter](Module_2/figures/part_2.png)
- [Part 3A Serial Plotter](Module_2/figures/part_3a_serial_plotter.png)
- [Part 3AB Setup](Module_2/figures/part_3ab_setup.png)
- [Part 3B Cool PWM=142](Module_2/figures/part_3b_cool_PWM=142.png)
- [Part 3B Cool PWM=60](Module_2/figures/part_3b_cool_PWM=60.png)
- [Part 3B Heat PWM=115](Module_2/figures/part_3b_heat_PWM=115.png)
- [Part 3B Heat PWM=60](Module_2/figures/part_3b_heat_PWM=60.png)
- [Part 3C Heat Motor Running](Module_2/figures/part_3c_heat.png)
- [Part 3C Motor Video](Module_2/figures/part_3c.mp4)

## Hardware

- Arduino Uno
- 100 kΩ potentiometer
- LED
- Current-limiting resistor
- Breadboard
- Jumper wires
- Oscilloscope and probe
- 100 kΩ NTC thermistor
- 100 kΩ precision resistor
- BTS7960 H-bridge
- 12 V DC power supply
- Small DC motor
- SPDT switch

## Tested Capabilities

The team uploaded and tested the Module 1 and Module 2 sketches on an Arduino Uno.

- The three Part 1 sketches produced the intended HIGH:LOW timing ratios.
- Part 2 reported raw analog-input values over the serial connection.
- Part 3A reported discrete integer ADC values.
- Part 3B converted ADC values to voltage.
- Part 3C compared single readings with 1000-reading averages.
- Part 3D measured the time required for 1000 ADC conversions.
- Part 4 used the averaged potentiometer input to control LED brightness with PWM.
- Module 2 Part 1 measured temperature using a thermistor voltage divider and the Beta model.
- Module 2 Part 2 output temperature values for the Arduino Serial Plotter.
- Module 2 Part 3 controlled H-bridge PWM and direction with a trim-pot and switch.
- Module 2 Part 3B verified H-bridge command signals with an oscilloscope.
- Module 2 Part 3C drove a small DC motor in both directions with variable speed.

## How to Run a Sketch

1. Open the selected `.ino` file in Arduino IDE.
2. Select `Arduino Uno` as the board.
3. Select the correct serial port.
4. Click **Verify**.
5. Click **Upload**.
6. Open Serial Monitor or Serial Plotter at `9600 baud` when required.

## AI Use

AI tools were used to help organize files, check calculations, explain Arduino
code, and review documentation. The team reviewed and tested the submitted
Arduino sketches and remains responsible for the final results.