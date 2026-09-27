# Module 3: TEC Instrument and Python GUI

## Team and Test Information

- Team members: Ricky Huang and Xavier Zhu
- Test date: September 16, 2026
- Arduino board: Arduino Uno
- Serial port used during testing: `/dev/cu.usbmodem101`
- Serial baud rate: `9600`
- Arduino thermistor sample count: `1000`

## Pre-Power Checklist

| Item | Value or observation |
| --- | --- |
| Arduino board and port | Arduino Uno, `/dev/cu.usbmodem101` |
| Thermistor pin | `A0` |
| H-bridge heat pin | `D9` |
| H-bridge cool pin | `D10` |
| PWM starts at zero? | Yes; both outputs are set to zero in `setup()` |
| Module 2 motor test completed with TEC disconnected? | Yes |
| High-current leads are 18 AWG? | Yes |
| Both female spade crimps tug-tested? | Yes |
| Both female spade crimps checked for continuity? | Yes |
| Power-supply voltage | 12 V |
| Thermal cutoff identified and connected? | Yes |
| Instructor check complete? | Yes |

## Final Wiring and Signal Path

The final measurement and command paths were:

```text
Thermistor divider -> Arduino A0 -> 1000-reading average
-> temperature conversion -> serial data -> Python plots and CSV

Python GUI -> serial command -> Arduino
-> D9 for HEAT or D10 for COOL -> H-bridge -> thermal cutoff -> TEC
```

Final Arduino pin assignments:

| Function | Arduino pin |
| --- | --- |
| Thermistor-divider measurement | `A0` |
| H-bridge heat PWM | `D9` |
| H-bridge cool PWM | `D10` |

The final serial-command sketch does not use the trim potentiometer on `A1`
or the physical direction input on `D11`. Direction and PWM are supplied by
the Python GUI.

The written wiring record above matches the final apparatus. The verified
high-current path was `M+ -> thermal switch -> TEC+`, with `TEC- -> M-`.

## Oscilloscope Verification

The oscilloscope verification must be performed with TEC actuator power off.

| Command | D9 observation with TEC power off | D10 observation with TEC power off | M+/M- low-PWM observation | TEC direction |
| --- | --- | --- | --- | --- |
| PWM = 0 | Constant LOW, no PWM | Constant LOW, no PWM | No drive waveform | Off |
| HEAT, PWM 40 | PWM waveform, approximately 15.7% duty cycle | Constant LOW | PWM output observed with heating polarity | Heat |
| COOL, PWM 40 | Constant LOW | PWM waveform, approximately 15.7% duty cycle | PWM output observed with reversed polarity | Cool |

Existing oscilloscope evidence:

- [Arduino digital-input oscilloscope video](../../Module_3/figures/part_3_oscilloscope_on_digitals.mp4)
- [H-bridge M+/M- oscilloscope video](../../Module_3/figures/part_3_oscilloscope_on_M+-.mp4)
- [Part 7 heating oscilloscope photograph](../../Module_3/figures/part_7_heating.jpg)
- [Part 7 cooling oscilloscope photograph](../../Module_3/figures/part_7_cooling.jpg)

The pin `9`/`10` checks were completed with TEC actuator power off. The M+/M-
low-PWM checks were completed after instructor approval. The observed active
input changed with the Python HEAT/COOL command, only one input was active at
a time, and the expected duty cycle for PWM 40 was `40/255 = 15.7%`.

## Low-Power Heating and Cooling Record

### Acquisition Metadata

| Setting | Value |
| --- | --- |
| Raw data file | `Module_3/data/part_7_integrated_control_data.csv` |
| Data columns | `time_s`, `temperature_C`, `pwm`, `heat_cool` |
| Serial baud rate | `9600` |
| Arduino reporting interval | `500 ms` |
| Thermistor sample count per reported temperature | `1000` |
| PWM used for the final low-power test | `40/255` |
| Power-supply voltage | 12 V |
| Hardware thermal cutoff | Installed and normally closed |

Raw data:

- [Part 7 integrated control data](../../Module_3/data/part_7_integrated_control_data.csv)

### Heating Record

- Command: `SET PWM 40 DIR HEAT`
- Recorded direction value: `Heat/Cool = 1`
- Active interval: approximately `26.0 s` to `65.0 s`
- Starting temperature: approximately `22.06 C`
- Ending temperature: approximately `28.90 C`
- Result: the measured temperature increased under the HEAT command.

### Cooling Record

- Command: `SET PWM 40 DIR COOL`
- Recorded direction value: `Heat/Cool = 0`
- Active interval: approximately `88.5 s` to `179.0 s`
- Starting temperature: approximately `27.68 C`
- Ending temperature: approximately `20.87 C`
- Result: the measured temperature decreased under the COOL command.

Control-GUI evidence:

- [Part 7 control GUI screenshot](../../Module_3/figures/part_7_GUI.png)
- [Labeled Part 7 heat/cool record](../../Module_3/figures/part_7_heat_cool_record.png)

The labeled Part 7 record shows both low-power intervals, units, PWM limit,
and direction using the canonical CSV data.

## Python Display-Only Program

Current display-only program:

- [Display-only Python program](../../Module_3/python/part_4_graphing.py)
- [Temperature strip-chart screenshot](../../Module_3/figures/part_4_temperature_graph.png)

This version reads Arduino serial data, parses measurement lines, plots
temperature and PWM, and saves accepted measurements to a CSV file. It does
not send commands to the Arduino.

The display-only program now contains the two required strip charts:
temperature versus time and PWM versus time.

## Python Manual-Control GUI

Final control program:

- [Python TEC control GUI](../../Module_3/python/part_5_tec_control_gui.py)
- [Control-GUI screenshot](../../Module_3/figures/part_7_GUI.png)

The GUI provides:

- a HEAT/COOL direction control,
- a PWM slider from `0` to `255`,
- a synchronized PWM text entry,
- live temperature and PWM plots,
- red PWM samples for heating and blue PWM samples for cooling,
- serial command transmission to the Arduino, and
- CSV data recording.

The principal Python functions are:

- `open_serial_port()` opens the connection to the Arduino.
- `read_serial_data()` reads available serial bytes and separates lines.
- `parse_measurement()` extracts temperature, time, PWM, and direction.
- `process_measurement()` stores accepted measurements and writes the CSV row.
- `update_plots()` refreshes the temperature and PWM strip charts.
- `send_command()` sends a PWM and direction command to the Arduino.

## Final Arduino and Python Pair

The paired programs used for integrated control are:

- [Arduino serial-command sketch](../../Module_3/arduino/part_6_tec_python_control/part_6_tec_python_control.ino)
- [Python TEC control GUI](../../Module_3/python/part_5_tec_control_gui.py)

The Arduino starts with both H-bridge PWM outputs at zero. It accepts commands
such as:

```text
SET PWM 40 DIR HEAT
SET PWM 40 DIR COOL
```

It reports measurements in the following format:

```text
Temperature (C): 27.73, Time (s): 645.06, PWM: 40, Heat/Cool: 1
```

Field meanings:

- `Temperature (C)` is the thermistor temperature in degrees Celsius.
- `Time (s)` is elapsed Arduino time in seconds.
- `PWM` is the current command from `0` to `255`.
- `Heat/Cool` is `1` for heat and `0` for cool.

## Zero-PWM Startup and Serial-Command Test Record

The Arduino sketch initializes both H-bridge control outputs to zero and sets
the stored PWM command to zero before serial control begins. The canonical
[Part 7 CSV file](../../Module_3/data/part_7_integrated_control_data.csv)
records `PWM = 0` in its first measurement at `0.50 s`.

The same record shows that the serial commands were accepted and applied:

- `SET PWM 40 DIR HEAT` produced `PWM = 40`, `Heat/Cool = 1` from
  approximately `26.0 s` to `65.0 s`.
- The command returned to zero between direction changes.
- `SET PWM 40 DIR COOL` produced `PWM = 40`, `Heat/Cool = 0` from
  approximately `88.5 s` to `179.0 s`.
- The final measurements returned to `PWM = 0`.

This provides the required zero-PWM startup and serial-command test record.

## AI Use

AI helped with:

- explaining the Module 3 procedure,
- adapting the manual Arduino sketch,
- writing and debugging the Python serial parser and GUI,
- adding CSV recording,
- checking file organization, and
- reviewing the repository against the C3 requirements.

The team selected the physical pin mapping, fixed the thermistor hardware,
chose the `1000`-sample average, tested the direction mapping, selected the
low-power PWM value, operated the real hardware, and recorded the experimental
data and screenshots.

Representative AI request:

> Modify the Arduino and Python programs for manual TEC control. Use 1000
> thermistor samples, read temperature from A0, use D9 for heat and D10 for
> cool, show temperature and PWM in the GUI, and save the measurements to CSV.
> Do not implement feedback control.

The code behavior that the team should be able to explain without the AI
transcript includes serial parsing, thermistor conversion, slider/text
synchronization, command transmission, plot updating, and safe shutdown.

## Measurement, Manual Actuation, and Feedback Control

Temperature measurement means reading the thermistor voltage and calculating
temperature without deciding how the TEC should be driven. Manual actuation
means a person chooses HEAT or COOL and selects the PWM command through the
GUI. Feedback control would compare the measured temperature with a target and
automatically adjust the TEC command. Module 3 demonstrates measurement and
manual open-loop actuation; it does not yet implement feedback control.

## Repository and Git Checkpoint

- [Team GitHub repository](https://github.com/zhuyanheng/Phys39-teamR-X)
- [Repository README](../../README.md)
- Required final commit summary: `Organize Module 3 TEC control project`

Final checkpoint:

- [x] Complete the required C3 repository evidence listed above.
- [x] Update the repository README with Module 3 instructions and evidence.
- [x] Document the exact final Arduino/Python pair in the README and this note.
- [x] Convert the Part 7 heating/cooling HEIF images to real JPEG files.
- [x] Commit with summary `Organize Module 3 TEC control project`.
- [ ] Push the final commit to GitHub.
- [ ] Verify the files on GitHub.
- [ ] Record the final commit hash in the C3 Team Checkoff receipt.
