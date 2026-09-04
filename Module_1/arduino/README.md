# Arduino Sketches - Module 1

This folder contains all Arduino sketches used for Module 1 experiments. Each sketch is placed in its own folder with the same name as the `.ino` file, following the course repository template guidelines.

## Repository Structure
arduino/
├── part_01_blink_1to1/
│ └── part_01_blink_1to1.ino
├── part_01_blink_1to10/
│ └── part_01_blink_1to10.ino
├── part_01_blink_10to1/
│ └── part_01_blink_10to1.ino
├── part_02_analog_read_serial/
│ └── part_02_analog_read_serial.ino
├── part_03a_adc_integer/
│ └── part_03a_adc_integer.ino
├── part_03b_adc_voltage/
│ └── part_03b_adc_voltage.ino
├── part_03c_averaging_comparison/
│ └── part_03c_averaging_comparison.ino
├── part_03d_averaging_timing/
│ └── part_03d_averaging_timing.ino
├── part_04_averaged_adc_pwm_led/
│ └── part_04_averaged_adc_pwm_led.ino

## Sketch Descriptions

| Sketch | Part | Description |
| :--- | :--- | :--- |
| `part_01_blink_1to1.ino` | Part 1 | Blink with 1:1 duty cycle (500ms HIGH, 500ms LOW). Expected duty cycle: 50%. |
| `part_01_blink_1to10.ino` | Part 1 | Blink with 1:10 duty cycle (100ms HIGH, 1000ms LOW). Expected duty cycle: ~9.09%. |
| `part_01_blink_10to1.ino` | Part 1 | Blink with 10:1 duty cycle (1000ms HIGH, 100ms LOW). Expected duty cycle: ~90.9%. |
| `part_02_analog_read_serial.ino` | Part 2 | Reads potentiometer voltage from A0 and prints raw ADC values to Serial Monitor. |
| `part_03a_adc_integer.ino` | Part 3A | Reads A0 and prints integer ADC values in `ADC:512` format for Serial Plotter compatibility. |
| `part_03b_adc_voltage.ino` | Part 3B | Converts ADC readings to voltage (V) using a 5.00V reference and prints with 4 decimal places. |
| `part_03c_averaging_comparison.ino` | Part 3C | Alternates between 100 points of N=1 (single reading) and 100 points of N=1000 (averaged) voltage outputs within the same sketch, allowing direct side‑by‑side comparison in Serial Plotter. |
| `part_03d_averaging_timing.ino` | Part 3D | Measures the time (in microseconds) required to perform 1000 `analogRead()` conversions using `micros()`. |
| `part_04_averaged_adc_pwm_led.ino` | Part 4 | Averages 1000 ADC readings from the potentiometer, maps the value to PWM (0–255), and outputs to pin 9 for LED brightness control. |

## Part 3C: Side‑by‑Side Comparison

The sketch `part_03c_averaging_comparison.ino` repeatedly produces:

- **100 points** of **N = 1** (single `analogRead()` per point)
- **100 points** of **N = 1000** (average of 1000 `analogRead()` calls per point)

This makes it easy to compare the noise level between unaveraged and averaged data directly in Serial Plotter. The transition between the two blocks is clearly visible: N=1 appears as a rough, noisy trace, while N=1000 appears as a smooth, stable trace.

## Common Hardware Connections

Unless otherwise noted in each sketch, the following connections apply:

| Component | Arduino Pin |
| :--- | :--- |
| Potentiometer (center wiper) | A0 |
| Potentiometer (outer terminal) | 5V |
| Potentiometer (other outer terminal) | GND |
| LED (PWM controlled) | Pin 9 (with series resistor, 200–2000Ω) |

## Usage

1. Open the desired sketch folder in Arduino IDE.
2. Select **Tools → Board → Arduino Uno**.
3. Select the correct **Port**.
4. Click **Upload**.
5. Open **Serial Monitor** (9600 baud) or **Serial Plotter** (Tools → Serial Plotter) to view output.

## Notes

- All sketches are written for **Arduino Uno**.
- The ADC reference voltage is assumed to be **5.00 V** (nominal). If a measured reference voltage is available, update `V_REF_VOLTS` accordingly.
- Displaying many decimal places does **not** improve the physical ADC resolution; it is an artifact of floating-point arithmetic.

---

*Last updated: September 4th 2026*