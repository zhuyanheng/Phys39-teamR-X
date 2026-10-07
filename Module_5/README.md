# Module 5: P-Only Temperature Control

This directory contains the Arduino and Python control programs, raw temperature records, figures, and the P-control analysis for Module 5. Python closes the feedback loop by computing the signed PWM `u = Kp (T_set − T)`, sending HEAT/COOL direction and a clamped 0–255 magnitude to the Arduino, which keeps the independent 60 °C software shutdown. The team verified the feedback signs, swept five gains (`Kp = 0.25, 0.5, 1, 2, 4` PWM/°C at a 30 °C heating setpoint), and compared measured droop with the Module 4 susceptibility model.

## Arduino Sketch

- [P-only TEC sketch](arduino/p_only_tec/p_only_tec.ino) is the Module 4 source: it averages 1000 thermistor readings, parses `SET PWM <n> DIR <HEAT|COOL>` commands, drives the H-bridge (D9 HEAT, D10 COOL), and enforces the 60 °C software limit. Python performs the P-control arithmetic; the Arduino only applies commands and retains its independent shutdown authority. Verify the actually uploaded version before a powered run.

## Python Scripts

- [P-control GUI and CSV logger](python/p_only_tec_control_gui.py) reads serial temperature, computes `e = T_set − T`, `u = Kp e`, sends direction and rounded/clamped PWM, and stops P mode (PWM 0) on a safety fault, temperature outside 10–45 °C, or a measurement gap over 2 seconds. Each launch writes a timestamped CSV in [`data/`](data/).
- [Part 4 droop comparison](python/plot_droop_comparison.py) computes measured and predicted droop `(T_set − T_amb)/(1 + Kp χ_h)`, writes [`part_04_droop_comparison.csv`](data/part_04_droop_comparison.csv), and produces the comparison figure.
- [Strip-chart traces](python/plot_strip_chart_traces.py) draws representative low- and high-gain temperature/PWM traces with a pure-stdlib SVG generator (no GUI dependency).
- [Controller tests](python/test_p_only_tec_control_gui.py) check the signed-command logic, saturation, and safety stop without hardware.
- [GUI launcher](run_gui.command) is a convenience script for starting the GUI.

## Experimental Data and Notes

- [Raw P-control CSVs](data/) preserve every 2026-09-30 run, including the low-gain sign test and the five-gain droop sweep. Each file records time, temperature, commanded PWM, direction, safety state, the P-active flag, setpoint, and gain.
- [Part 4 droop summary](data/part_04_droop_comparison.csv) lists measured and predicted droop per gain and the source CSV for each point.
- [Module 5 lab note](../docs/module_notes/module_05_p_control.md) contains the Part 2 sign test, the selected Part 3 gain range and sweep table, the Part 4 droop comparison, the Part 5 high-gain assessment, and the Part 6 one-lump derivation. The team accepts the comparison using the provisional Module 4 heating slope `χ_h = 0.4954 °C/PWM` for Module 5; its underlying Module 4 steady-state limitation remains documented. Instructor approval for the gain range and the 15 °C cooling target is not recorded.

## Figures

- [Measured vs predicted droop](../docs/figures/module_05/part_04_measured_vs_predicted_droop.png).
- [Low-gain strip-chart trace (Kp = 0.25)](../docs/figures/module_05/low_gain_kp0.25_trace.png)
- [High-gain strip-chart trace (Kp = 4)](../docs/figures/module_05/high_gain_kp4_trace.png)

## Running the Programs

1. Open and upload the [Arduino sketch](arduino/p_only_tec/p_only_tec.ino) in Arduino IDE after the instructor-approved hardware checks. Select the correct board and serial port.
2. Set `SERIAL_PORT` near the top of the [Python GUI](python/p_only_tec_control_gui.py) to the connected board's port (`9600 baud`); close Arduino Serial Monitor before launching.
3. From the repository root, install dependencies and run the GUI:

   ```text
   python3 -m pip install -r requirements.txt
   python3 Module_5/python/p_only_tec_control_gui.py
   ```

   or use the [launcher](run_gui.command).

The plotting and test scripts analyze saved files; they do not operate the TEC.
