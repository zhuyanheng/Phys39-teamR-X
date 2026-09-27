# Module 3 Data

This directory contains the experimental data and quantitative analysis for the Module 3 TEC (Thermoelectric Cooler) manual control experiments.

## Files

- [Part 4 display-only data](./part_4_data.csv)
- [Part 5 manual GUI control data](./part_5_data.csv)
- [Part 6 serial-command control data](./part_6_data.csv)
- [Part 7 integrated manual-control test data](./part_7_integrated_control_data.csv)
- [Part 4 Python graphing script](../python/part_4_graphing.py)
- [Part 5 Python GUI script](../python/part_5_tec_control_gui.py)
- [Part 6 Arduino serial-command sketch](../arduino/part_6_tec_python_control/part_6_tec_python_control.ino)

## Data Collection Metadata

| Item | Description |
|---|---|
| Date | September 16, 2026 |
| Experimenters | Ricky Huang and Xavier Zhu |
| Board | Arduino Uno |
| Thermistor input | A0 (100kΩ NTC thermistor, 100kΩ fixed resistor divider) |
| Actuator | TEC via BTS7960 H-Bridge |
| Heat exchanger | 12 V pump and radiator fans, running continuously |
| Data format | CSV |
| Temperature unit | Degrees Celsius (°C) |
| PWM range | 0 to 255 (8-bit timer) |
| Direction mapping | 1 = HEAT, 0 = COOL |
| Reporting interval | 500 ms |
| Thermistor samples per reported temperature | 1000 |
| Serial baud rate | 9600 baud |
| Power-supply voltage and current limit | Not yet recorded; add from the signed lab checklist |

## Data Columns

All CSV files contain the following columns:

| Column | Meaning | Unit |
|---|---|---|
| `time_s` | Arduino elapsed time | seconds (s) |
| `temperature_C` | Measured TEC temperature | °C |
| `pwm` | Commanded PWM value (0-255) | Dimensionless |
| `heat_cool` | Direction (1 = HEAT, 0 = COOL) | Dimensionless |

## Part 4 Data (Display-Only)

The [Part 4 CSV file](./part_4_data.csv) contains open-loop data with no computer control. PWM stays at 0 for the first 31 seconds, then manually steps through 50, 96, 144, 216, 253, and 255 as the user adjusts the physical trim-pot. The temperature plateaus near 32.5°C before rising rapidly above 50°C. This data verifies the display-only strip chart.

## Part 5 Data (Manual GUI Control)

The [Part 5 CSV file](./part_5_data.csv) contains a development heating and cooling cycle commanded from the Python GUI. The user sets a low PWM (40) to observe gentle heating, then applies a high PWM (255) for rapid heating, followed by a direction change to COOL at 78.5 seconds. This development run tests the GUI slider, text box, and direction toggle synchronization; it is not the final low-power C3 record.

## Part 6 Data (Serial-Command Control)

The [Part 6 CSV file](./part_6_data.csv) contains a development test of the serial interface. Commands step from 114 to 124, then 219, 255, 189, and eventually 0. The direction is switched between HEAT and COOL multiple times to verify that the Arduino correctly parses the `SET PWM <x> DIR <HEAT/COOL>` command format. It is not the final low-power C3 record.

## Part 7 Data (Integrated Manual-Control Test)

The [Part 7 CSV file](./part_7_integrated_control_data.csv) is the canonical manual-control test result.

The [labeled Part 7 heat/cool figure](../figures/part_7_heat_cool_record.png)
was generated directly from this CSV file using
[`plot_part_7_record.py`](../python/plot_part_7_record.py).

Key observations from this run:

- **Heat test (PWM 40):** From 26.0 s to 65.0 s, the temperature rose from 22.06°C to 28.90°C at a steady rate.
- **Cool test (PWM 40):** From 88.5 s to 179.0 s, the temperature fell from 27.68°C to 20.87°C.
- **Idle state:** Between tests (PWM 0), the temperature drifted slowly back toward ambient.

This confirms that Python sets and displays PWM and direction, the Arduino applies the command and measures temperature, and the GUI correctly plots and saves the instrument state.

## Notes

- All data was logged by the Python GUI scripts (`part_4_graphing.py` and `part_5_tec_control_gui.py`).
- The Arduino serial monitor must be closed before running the Python scripts, as the serial port is exclusive.
- The TEC heat exchanger (pump and fans) must be running before applying any power to the TEC.
