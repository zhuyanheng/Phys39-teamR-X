# Low-PWM cooling direction check — 2026-09-23

Used the existing Module 4 Arduino firmware (60 °C upper shutdown threshold) and Python GUI. Changed COOL PWM from 0 to 10, observed a falling temperature, then returned PWM to 0. No steady-state claim is made.

Source: [GUI CSV](data/module_04_tec_20260923_114300_656698.csv).

- Before command: approximately 22.35 °C, COOL, PWM 0.
- Arduino time 288.21 s: 22.34 °C, COOL PWM 10, firmware heat/cool outputs 0/10, Safety OK.
- Arduino time 304.50 s: approximately 22.01 °C, COOL PWM 10, Safety OK (GUI observation).
- Arduino time 307.54–310.08 s: PWM 0 confirmed in CSV, firmware outputs 0/0, Safety OK; temperature 22.02–22.05 °C.

The roughly 0.33 °C fall over this short interval supports the configured cooling direction. This is a startup direction check, not a steady-state calibration point or a measurement of temperature susceptibility. Supply voltage/current settings and physical output measurements were not recorded by this check.
