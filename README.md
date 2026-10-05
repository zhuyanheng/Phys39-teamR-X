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

## Module 3: Manual TEC Heat/Cool And First Python GUI

This repository contains the Arduino sketches, Python scripts, data, and
figures for Module 3: manual TEC control via H-bridge, thermistor feedback,
and a Python GUI for display and control.

- [Module 3 Arduino documentation](Module_3/arduino/README.md)
- [Module 3 Python documentation](Module_3/python/README.md)
- [Module 3 data documentation](Module_3/data/README.md)
- [Module 3 evidence note](docs/module_notes/module_03_tec_gui.md)

### Module 3 Arduino Sketches

- [Part 2: Manual Trim-pot Motor Control](Module_3/arduino/part_2/part_2.ino)
- [Part 3: Manual TEC Calibration](Module_3/arduino/part_3/part_3.ino)
- [Part 6: TEC Python Serial Control](Module_3/arduino/part_6_tec_python_control/part_6_tec_python_control.ino)

### Module 3 Python Scripts

- [Part 4: Temperature Strip Chart](Module_3/python/part_4_graphing.py)
- [Part 5: TEC Control GUI](Module_3/python/part_5_tec_control_gui.py)
- [Python dependencies](requirements.txt)

The final integrated pair is the
[Arduino serial-command sketch](Module_3/arduino/part_6_tec_python_control/part_6_tec_python_control.ino)
and the [Python TEC control GUI](Module_3/python/part_5_tec_control_gui.py).
They communicate at `9600 baud` using commands such as
`SET PWM 40 DIR HEAT` and measurements such as:

```text
Temperature (C): 27.73, Time (s): 645.06, PWM: 40, Heat/Cool: 1
```

The fields are temperature in degrees Celsius, Arduino elapsed time in
seconds, the active PWM command, and direction (`1` = heat, `0` = cool).

### Module 3 Figures

- [Part 2 Cooling](Module_3/figures/part_2_cooling.png)
- [Part 3 Oscilloscope on Digitals](Module_3/figures/part_3_oscilloscope_on_digitals.mp4)
- [Part 3 Oscilloscope on M+ and M-](Module_3/figures/part_3_oscilloscope_on_M+-.mp4)
- [Part 3 Switch Between Cooling and Heating](Module_3/figures/part_3_switch_between_cooling_heating.png)
- [Part 4 Temperature Graph](Module_3/figures/part_4_temperature_graph.png)
- [Part 5 GUI Without Actual Control](Module_3/figures/part_5_GUI_without_actual_control.png)
- [Part 6 TEC Control Using GUI 1](Module_3/figures/part_6_TEC_control_using_GUI_1.png)
- [Part 6 TEC Control Using GUI 2](Module_3/figures/part_6_TEC_control_using_GUI_2.png)
- [Part 7 GUI](Module_3/figures/part_7_GUI.png)
- [Part 7 Labeled Heat/Cool Record](Module_3/figures/part_7_heat_cool_record.png)
- [Part 7 Cooling](Module_3/figures/part_7_cooling.jpg)
- [Part 7 Heating](Module_3/figures/part_7_heating.jpg)

## Module 4: Open-Loop TEC Heating and Cooling

This repository contains the Arduino and Python programs, raw temperature
records, figures, and A2 analysis for Module 4: software temperature shutdown,
open-loop heating and cooling at five PWM levels per direction, and a
steady-temperature-versus-signed-PWM comparison.

- [Module 4 documentation](Module_4/README.md)
- [Module 4 selected-data documentation](data/module_04/README.md)
- [Module 4 lab record and steady-state protocol audit](docs/module_notes/module_04_open_loop_tec.md)

### Module 4 Arduino Sketch

- [Part 1: TEC Control and Temperature Safety](Module_4/arudino/part_1/part_1.ino)

### Module 4 Python Scripts

- [TEC Control GUI and CSV Logger](Module_4/python/part_5_tec_control_gui.py)
- [Part 4 Data Validation and Figures](Module_4/python/plot_a2.py)
- [A2 PDF Builder](Module_4/python/build_a2_existing_data.py)

### Module 4 Data and Figures

- [Ten selected HEAT/COOL measurements](data/module_04/steady_state.csv)
- [Raw experimental CSVs and safety-test logs](Module_4/data/)
- [Part 1 safety-test record](Module_4/check/part_1_safety_check.md)
- [Part 1 HEAT high-current diagram](Module_4/Diagram/heating_high_current.png)
- [Part 1 COOL high-current diagram](Module_4/Diagram/cooling_high_current.png)
- [HEAT time trace](Module_4/figures/heating_trace.svg)
- [COOL time trace](Module_4/figures/cooling_trace.svg)
- [Steady temperature versus signed PWM](Module_4/figures/steady_temperature_vs_pwm.svg)
- [A2 two-page PDF candidate](Module_4/A2_Huang_Zhu.pdf)

The ten-point analysis and A2 PDF are provisional. The professor's revised
Part 3 steady-state rule requires about three step-response time constants
followed by one additional minute of observation. See the Module 4 lab record
for the measurements that need review or longer recordings before submission.
The two Part 1 diagrams are historical illustrations, not verified as-built
wiring records; inspect the actual thermal-switch path with the instructor.

## Module 5: P-Only Temperature Control

This repository contains the Arduino and Python programs, raw temperature
records, figures, and analysis for Module 5: closing the TEC feedback loop with
proportional control. Python computes the signed PWM `u = Kp (T_set − T)`,
sends the direction and magnitude to the Arduino, and the Arduino keeps its
independent 60 °C shutdown. The team verified the feedback signs, swept five
gains at a 30 °C heating setpoint, and compared measured droop with the
Module 4 susceptibility model.

- [Module 5 documentation](Module_5/README.md)
- [Module 5 lab note and Part 6 derivation](docs/module_notes/module_05_p_control.md)

### Module 5 Arduino Sketch

- [P-only TEC sketch](Module_5/arduino/p_only_tec/p_only_tec.ino)

### Module 5 Python Scripts

- [P-control GUI and CSV logger](Module_5/python/p_only_tec_control_gui.py)
- [Part 4 droop comparison](Module_5/python/plot_droop_comparison.py)
- [Strip-chart traces](Module_5/python/plot_strip_chart_traces.py)
- [Controller tests](Module_5/python/test_p_only_tec_control_gui.py)

### Module 5 Data and Figures

- [Raw P-control CSVs](Module_5/data/)
- [Part 4 droop summary](Module_5/data/part_04_droop_comparison.csv)
- [Measured vs predicted droop](Module_5/figures/part_04_measured_vs_predicted_droop.svg)
- [Low-gain strip-chart trace (Kp = 0.25)](Module_5/figures/low_gain_kp0.25_trace.svg)
- [High-gain strip-chart trace (Kp = 4)](Module_5/figures/high_gain_kp4_trace.svg)

The gain sweep and droop analysis use the provisional Module 4 heating slope
(`χ_h = 0.4954 °C/PWM`) pending the Module 4 steady-state revalidation. The
instructor-approved gain range and the Part 2 cooling target are not yet
recorded in the note.

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
- Thermoelectric Cooler (TEC)
- Thermal switch (NC)
- Heat exchanger (pump and radiator fans)

## Tested Capabilities

The team uploaded and tested the Module 1, Module 2, and Module 3 programs on an Arduino Uno.

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
- Module 3 Part 2 and Part 3 successfully drove the TEC manually and calibrated heat/cool directions.
- Module 3 Part 4 displayed live temperature data in a Python strip chart.
- Module 3 Part 5 built a functional Python GUI with synchronized slider and text box.
- Module 3 Part 6 enabled serial-command control of PWM and direction from Python.
- Module 3 Part 7 completed integrated manual-control testing with real-time plotting and CSV logging.
- Module 4 software-safety tests recorded temperature-limit shutdown and continuing serial reports; the Part 1 record distinguishes firmware reports from independent electrical measurements.
- Module 4 collected ten selected HEAT/COOL PWM points and generated provisional time traces, fitted slopes, and an A2 PDF. Compliance with the revised steady-state rule remains to be established.
- Module 5 verified the low-gain HEAT and COOL feedback signs, swept five proportional gains at a 30 °C setpoint, measured droop versus gain, and compared measured droop with the Module 4 susceptibility prediction (no oscillation up to Kp = 4).

## How to Run a Sketch

1. Open the selected `.ino` file in Arduino IDE.
2. Select `Arduino Uno` as the board.
3. Select the correct serial port.
4. Click **Verify**.
5. Click **Upload**.
6. Open Serial Monitor or Serial Plotter at `9600 baud` when required.
7. For Module 3 Python scripts, ensure the Serial Monitor is closed before running the GUI.
8. For the Module 4 GUI, also set its `SERIAL_PORT` to the connected Arduino and close Serial Monitor before launch; see the [Module 4 documentation](Module_4/README.md).

### Running the Module 3 Python Programs

From the repository root, install the dependencies once:

```text
python3 -m pip install -r requirements.txt
```

Run the display-only strip chart:

```text
python3 Module_3/python/part_4_graphing.py
```

Run the final manual-control GUI:

```text
python3 Module_3/python/part_5_tec_control_gui.py
```

## AI Use

AI helped draft and debug the Arduino thermistor/serial-command code, Python
serial parser, GUI controls, plotting, CSV logging, documentation, and
repository organization. The team selected and verified the pin mapping,
thermistor constants, 1000-sample average, heat/cool direction mapping, and
low-power PWM setting, and tested the programs on the real Arduino, H-bridge,
thermistor, TEC, oscilloscope, and power supply. The code paths reviewed for
the C3 oral explanation are the measurement conversion, serial format, GUI
synchronization, command path, and plot updates; each team member must be able
to explain them without relying on the AI transcript.

For Module 4, AI also assisted with CSV validation, plotting, and the draft A2
analysis. The selected steady-state windows and physical checks remain subject
to the team's and instructor's review; generated figures are not a substitute
for the revised measurement protocol.

The Module 4 temperature-limit shutdown has serial-log evidence, but actual
output-pin voltage, disconnected-sensor behavior, and broken-serial behavior
have not been independently verified in the cited test record. The ten-point
steady-state analysis also requires review against the revised Part 3 rule.

For Module 5, AI helped draft and debug the P-control GUI, the droop
comparison and strip-chart plotting scripts, and the Part 6 one-lump
derivation. The measured droop, gain values, and the provisional Module 4
heating slope used in the prediction remain subject to the team's and
instructor's review; generated figures do not replace the physical runs or the
instructor-approved gain range.
