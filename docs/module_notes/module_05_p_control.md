# Module 5: P-only temperature control

## Part 1: controller implementation

- Python GUI: `Module_5/python/p_only_tec_control_gui.py`.
- Arduino sketch: `Module_5/arduino/p_only_tec/p_only_tec.ino`, copied from the Module 4 source on 2026-09-29. Verify that this is the version actually uploaded before a powered run.
- At startup the GUI sends PWM 0 and leaves P control off. It waits for a recent, finite 10–45 °C measurement with `Safety: OK` before enabling P control.
- For each Arduino report, Python calculates `error = setpoint - temperature`, `signed_pwm = Kp * error`, sends `HEAT` for nonnegative signed PWM or `COOL` for negative signed PWM, and rounds/clamps `abs(signed_pwm)` to an integer 0–255.
- The GUI plots measured temperature, setpoint, measured PWM by direction, and error. It writes all measurements and control values to a timestamped CSV in `data/module_05/`.
- Stop requests PWM 0. A reported safety fault, temperature outside 10–45 °C, or a measurement gap over 2 seconds stops P mode and requests PWM 0. The Arduino independently checks its 60 °C software limit and invalid sensor readings. A lost Python process cannot be relied on to send a final zero command; operate only with the instructor's approved hardware precautions and supervision.

## Still to verify on the physical apparatus

- [ ] Instructor-approved wiring, current limit, live sensor reading, and firmware version.
- [ ] Start with PWM 0 and confirm both firmware outputs report 0.
- [ ] Low-gain HEAT and COOL feedback signs (Part 2). Stop if temperature moves the wrong way.

No physical run or safety sign test is claimed in this note.
