# Module 3 Arduino Sketches

This directory contains the Arduino sketches used for the Module 3 experiments.
Each sketch is stored in a folder with the same name as its `.ino` file.

## Sketches

| Part | Sketch | Purpose |
|---|---|---|
| Part 2 | [Manual Trim-pot Control](./part_2/part_2.ino) | Controls the H-bridge using a trim-pot (A1) for PWM and a physical wire (D11) for direction. Used initially to test the motor. |
| Part 3 | [Manual TEC Control](./part_3/part_3.ino) | Identical to Part 2 code. Used to safely identify heating and cooling directions with the TEC and verify H-bridge PWM signals with an oscilloscope. |
| Part 6 | [TEC Python Serial Control](./part_6_tec_python_control/part_6_tec_python_control.ino) | Reads serial commands from the Python GUI to set PWM and direction. Includes thermistor averaging and prints labeled measurement lines. |

## Hardware Connections

### TEC and H-Bridge (BTS7960)

| Component | Arduino / Power connection |
|---|---|
| H-Bridge VCC, R_EN, L_EN | Arduino 5 V |
| H-Bridge GND | Arduino GND |
| H-Bridge RPWM (Forward) | Arduino D9 (HEAT_PWM_PIN) |
| H-Bridge LPWM (Reverse) | Arduino D10 (COOL_PWM_PIN) |
| 12V Power Supply V+ / V- | H-Bridge B+ / B- (Do not go through the terminal block) |
| H-Bridge M+ | Thermal Switch -> TEC+ |
| H-Bridge M- | TEC- |
| Heat Exchanger | Direct to 12V Power Supply (Must be running before TEC power is applied) |

### Thermistor

| Component | Arduino connection |
|---|---|
| Voltage Divider | 5 V -> 100kΩ Fixed Resistor -> A0 -> 100kΩ Thermistor -> GND |

## Part 6 Serial Command Format

The Part 6 sketch listens for newline-terminated commands from the Python GUI:

**Input Command:**
`SET PWM <0-255> DIR <HEAT/COOL>\n`

**Output Measurement Line (every 500 ms):**
`Temperature (C): XX.XX, Time (s): XX.XX, PWM: XXX, Heat/Cool: X\n`
*(Note: Heat/Cool: 1 = HEAT, 0 = COOL)*

## Usage

1. Open the selected sketch in Arduino IDE.
2. Select **Arduino Uno**.
3. Select the correct serial port.
4. click **Verify**.
5. click **Upload**.
6. For Part 2/3: Open Serial Monitor at `9600 baud` to view temperature and manually adjust the trim-pot.
7. For Part 6: **Close Serial Monitor**. Run the Python GUI (`part_5_tec_control_gui.py`) to send commands and log data.

## Notes

- **Safety First**: Ensure the heat exchanger is running before applying power to the TEC.
- **PWM Start**: The sketch initializes both H-bridge outputs to zero (`analogWrite(pin, 0)`) in `setup()`.
- **Thermistor Averaging**: The ADC reading (A0) is averaged over 1000 samples before conversion to voltage and temperature using the Beta formula.
- **Command Clamping**: PWM values received over serial are constrained to the range 0 to 255.
- **Instructor Approval**: Verify pin outputs and low-power heating/cooling behaviors with an instructor before full-power operation.