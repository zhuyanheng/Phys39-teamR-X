# Module 3: TEC Instrument and Python GUI

## Team and Test Information

- Team members: Ricky Huang and Xavier Zhu
- Test date: **TODO**
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
| High-current leads are 18 AWG? | **TODO: confirm** |
| Both female spade crimps tug-tested? | **TODO: record result** |
| Both female spade crimps checked for continuity? | **TODO: record result** |
| Power-supply voltage | **TODO: enter measured setting** |
| Power-supply current limit | **TODO: enter setting** |
| Thermal cutoff identified and connected? | **TODO: confirm** |
| Instructor check complete? | **TODO: add name/signature or confirmation** |

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

**TODO:** Add a link to the final wiring photograph or wiring sketch and
record the verified high-current path through the thermal cutoff.

## Oscilloscope Verification

The oscilloscope verification must be performed with TEC actuator power off.

| Command | D9 observation | D10 observation | Expected TEC direction |
| --- | --- | --- | --- |
| PWM = 0 | **TODO** | **TODO** | Off |
| HEAT, low PWM | **TODO** | **TODO** | Heat |
| COOL, low PWM | **TODO** | **TODO** | Cool |

Existing oscilloscope evidence:

- [Arduino digital-input oscilloscope video](../../Module_3/figures/part_3_oscilloscope_on_digitals.mp4)
- [H-bridge M+/M- oscilloscope video](../../Module_3/figures/part_3_oscilloscope_on_M+-.mp4)
- [Part 7 heating oscilloscope photograph](../../Module_3/figures/part_7_heating.png)
- [Part 7 cooling oscilloscope photograph](../../Module_3/figures/part_7_cooling.png)

**TODO:** Record the PWM command, observed duty cycle, active pin, inactive pin,
scope voltage scale, and time scale. Confirm explicitly that Python commands
changed pins `9` and `10` correctly while TEC power was off.

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
| Power-supply voltage | **TODO** |
| Power-supply current limit | **TODO** |
| Hardware thermal cutoff | **TODO: confirm installed and normally closed** |

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

**TODO:** Add or link a final labeled figure that clearly shows both the
low-power heating and cooling intervals, units, PWM limit, and direction.

## Python Display-Only Program

Current display-only program:

- [Display-only Python program](../../Module_3/python/part_4_graphing.py)
- [Temperature strip-chart screenshot](../../Module_3/figures/part_4_temperature_graph.png)

This version reads Arduino serial data, parses measurement lines, plots the
temperature, and saves accepted measurements to a CSV file. It does not send
commands to the Arduino.

**TODO before C3:** The course Part 5 requirement calls for two strip charts,
temperature versus time and PWM versus time. Add the PWM plot to the
display-only program and save a screenshot of that completed version.

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

## Safety Tests

| Test | Expected safe result | Observed result | Passed? |
| --- | --- | --- | --- |
| Startup | D9 and D10 begin at zero PWM | **TODO** | **TODO** |
| Direction change | PWM returns to zero before reversing direction | **TODO** | **TODO** |
| Invalid serial command | Outputs enter or remain in a documented safe state | **TODO** | **TODO** |
| Invalid thermistor temperature | TEC output is disabled safely | **TODO** | **TODO** |
| Broken serial connection | TEC output is disabled safely | **TODO** | **TODO** |
| Over-temperature condition | Software disables PWM and/or the thermal cutoff removes power | **TODO** | **TODO** |

The physical thermal cutoff is the independent hardware protection against
unsafe TEC temperature. Software behavior must also be explained during the
C3 oral check.

**Important current limitation:** malformed Arduino commands are ignored, an
invalid Python measurement is skipped, and there is no Arduino command timeout
or software over-temperature cutoff. These behaviors must be discussed and
either improved or documented accurately before the final demonstration.

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
- Current pushed commit before final Module 3 cleanup: `56f6538 Done for now`
- Required final commit summary: `Organize Module 3 TEC control project`

Final checkpoint:

- [ ] Complete every experimental `TODO` above.
- [ ] Update the repository README with Module 3 instructions and evidence.
- [ ] Confirm the final Arduino and Python filenames clearly identify the pair.
- [ ] Convert the Part 7 heating/cooling HEIF images to real PNG or JPEG files.
- [ ] Commit with summary `Organize Module 3 TEC control project`.
- [ ] Push the final commit to GitHub.
- [ ] Verify the files on GitHub.
- [ ] Record the final commit hash in the C3 Team Checkoff receipt.
