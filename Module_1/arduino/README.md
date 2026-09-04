# Module 1 Arduino Sketches

This directory contains the Arduino sketches used for the Module 1 experiments.
Each sketch is stored in a folder with the same name as its `.ino` file.

## Sketches

| Part | Sketch | Purpose |
|---|---|---|
| Part 1 | [Blink 1:1](./part_01_blink_1to1/part_01_blink_1to1.ino) | Generates a 500 ms HIGH and 500 ms LOW digital waveform. |
| Part 1 | [Blink 1:10](./part_01_blink_1to10/part_01_blink_1to10.ino) | Generates a 100 ms HIGH and 1000 ms LOW digital waveform. |
| Part 1 | [Blink 10:1](./part_01_blink_10to1/part_01_blink_10to1.ino) | Generates a 1000 ms HIGH and 100 ms LOW digital waveform. |
| Part 2 | [AnalogReadSerial](./part_02_analog_read_serial/part_02_analog_read_serial.ino) | Reads analog pin A0 and prints the raw ADC value. |
| Part 3A | [Integer ADC readings](./part_03a_adc_integer/part_03a_adc_integer.ino) | Prints A0 readings as labeled integer ADC values. |
| Part 3B | [ADC-to-voltage conversion](./part_03b_adc_voltage/part_03b_adc_voltage.ino) | Converts ADC readings to voltage using a nominal 5.00 V reference. |
| Part 3C | [Averaging comparison](./part_03c_averaging_comparison/part_03c_averaging_comparison.ino) | Produces 100 N=1 points followed by 100 N=1000 averaged points. |
| Part 3D | [ADC acquisition timing](./part_03d_averaging_timing/part_03d_averaging_timing.ino) | Measures the time required for 1000 `analogRead()` conversions. |
| Part 4 | [Averaged ADC PWM LED](./part_04_averaged_adc_pwm_led/part_04_averaged_adc_pwm_led.ino) | Maps the averaged potentiometer input to PWM output on pin 9. |

## Hardware Connections

### Potentiometer

| Potentiometer terminal | Arduino connection |
|---|---|
| Outer terminal | 5 V |
| Other outer terminal | GND |
| Center wiper | A0 |

### LED and PWM

| Component | Arduino connection |
|---|---|
| PWM output | Pin 9 |
| LED | Connected in series with a current-limiting resistor |
| Ground | Arduino GND |

## Part 3C Output

The Part 3C sketch repeatedly produces:

1. 100 voltage points with one ADC conversion per point, \(N=1\).
2. 100 voltage points with 1000 ADC conversions averaged per point, \(N=1000\).
3. A return to the \(N=1\) block.

The potentiometer must remain fixed while both blocks are collected.

## Usage

1. Open the selected sketch in Arduino IDE.
2. Select **Arduino Uno**.
3. Select the correct serial port.
4. click **Verify**.
5. click **Upload**.
6. Open Serial Monitor or Serial Plotter at `9600 baud`.

## Notes

- The sketches assume a nominal ADC reference voltage of 5.00 V.
- The Arduino Uno ADC produces 1024 possible integer codes, from 0 through 1023.
- Printing additional decimal places does not improve the physical resolution of a single ADC conversion.
- The LED must be connected through a current-limiting resistor.