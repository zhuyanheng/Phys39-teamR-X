# Module 4: Open-Loop TEC Heating and Cooling

This directory contains the Arduino and Python control programs, raw temperature records, figures, and A2 analysis for Module 4. The team selected five PWM levels in each direction and fitted steady temperature against signed PWM. The ten-point analysis is **provisional** until the measurements are checked against the professor's revised steady-state criterion: wait about three step-response time constants, then observe one additional minute with no net drift beyond ordinary short-term noise.

## Arduino Sketch

- [Part 1 TEC control and temperature safety](arudino/part_1/part_1.ino) averages 1000 thermistor readings, accepts serial PWM/direction commands, and has a 60 °C software shutdown threshold. D9 commands HEAT and D10 commands COOL. Check which sketch was actually uploaded before relying on the source file.

## Python Scripts

- [TEC control GUI and CSV logger](python/part_5_tec_control_gui.py) displays temperature, PWM, direction, and reported safety state. Each launch writes a timestamped CSV in [`data/`](data/).
- [Part 4 plotting script](python/plot_a2.py) validates the selected windows against the raw CSVs and produces the three SVG figures below.
- [Plotting tests](python/test_plot_a2.py) check the data-selection and plotting logic.
- [A2 PDF builder](python/build_a2_existing_data.py) generates [`A2_Huang_Zhu.pdf`](A2_Huang_Zhu.pdf) from the selected ten-point table.

## Experimental Data and Notes

- [Raw GUI CSVs and safety-test serial logs](data/) are preserved, including exploratory runs that are **not** ten-point calibration measurements.
- [Ten selected measurements](../data/module_04/steady_state.csv) identify each direction, PWM, temperature, source CSV, and averaging window. See the [data documentation](../data/module_04/README.md) for column definitions and limitations.
- [Part 1 software safety-test record](check/part_1_safety_check.md) links the shutdown and recovery evidence.
- [Low-PWM cooling-direction check](check/cooling_direction_test.md) documents the direction test, not a steady-state point.
- [Module 4 lab record](../docs/module_notes/module_04_open_loop_tec.md) contains the ten-point table and the revised-protocol audit. H0, H1, H4, C0, and C4 need longer or new records; the other five points need review against the one-minute noise criterion.

## Figures and A2

- [HEAT time trace](figures/heating_trace.svg)
- [COOL time trace](figures/cooling_trace.svg)
- [Steady temperature versus signed PWM](figures/steady_temperature_vs_pwm.svg)
- [Part 1 HEAT high-current diagram](Diagram/heating_high_current.png) and [Part 1 COOL high-current diagram](Diagram/cooling_high_current.png) are earlier illustrations, **not** verified as-built wiring records. Check the actual series thermal-switch location and switch state with the instructor before relying on them.
- [GUI after the temporary 30 °C limit test](figures/gui_after_30c_limit_test_20260923.png): shows recovery at PWM 0, **not** the instant of shutdown. The [Part 1 record](check/part_1_safety_check.md) identifies the actual shutdown samples.
- [Two-page A2 PDF candidate](A2_Huang_Zhu.pdf): contains the current graph and manufacturer comparison. Its selected temperatures and old 20-second steady-state description must be reviewed and updated before final submission.

The HEAT-45 and COOL-96 endpoint windows include instructor-approved exceptions to the course's 10–45 °C measurement range; their raw values have not been clipped. The plotted slopes and A2 comparison may change if the revised steady-state review changes any selected temperatures.

## Running the Programs

1. Open and upload the [Arduino sketch](arudino/part_1/part_1.ino) in Arduino IDE after the instructor-approved hardware checks. Select the correct Arduino board and serial port.
2. Set `SERIAL_PORT` near the top of the [Python GUI](python/part_5_tec_control_gui.py) to the connected board's port. The sketch and GUI use `9600 baud`; close Arduino Serial Monitor before launching the GUI.
3. From the repository root, install [Python dependencies](../requirements.txt) and run the GUI:

   ```text
   python3 -m pip install -r requirements.txt
   python3 Module_4/python/part_5_tec_control_gui.py
   ```

The plotting and PDF scripts analyze saved files; they do not operate the TEC. Recheck the selected data and figure captions before regenerating the A2 PDF. An older A2 draft was removed from the working directory and remains recoverable from Git history.
