# Module 5 data index

Raw CSV values are unchanged; descriptive filenames replace the GUI's timestamp-only filenames. The leading date and time preserve the order in which each file was created. Each raw CSV contains elapsed Arduino time, measured temperature, firmware-reported PWM and direction, safety state, P-mode status, setpoint, gain, error, and Python's signed-PWM calculation. A firmware command shown in a row was already in effect when that temperature was reported; Python calculates the next command from that temperature.

| Date/time | Raw data | Purpose |
| --- | --- | --- |
| 2026-09-30 10:40:14 | [`20260930_104014_sign_test_preliminary.csv`](20260930_104014_sign_test_preliminary.csv) | Preliminary low-gain HEAT/COOL sign test; cooling below ambient was not established. |
| 2026-09-30 10:58:23 | [`20260930_105823_sign_test_heat_cool_confirmed.csv`](20260930_105823_sign_test_heat_cool_confirmed.csv) | Longer low-gain sign test confirming both directions. |
| 2026-09-30 11:07:23 | [`20260930_110723_droop_kp0p25.csv`](20260930_110723_droop_kp0p25.csv) | Part 3, 30 °C setpoint, fixed `Kp=0.25 PWM/°C`; ambient reference for Part 4. |
| 2026-09-30 11:12:14 | [`20260930_111214_droop_kp0p5.csv`](20260930_111214_droop_kp0p5.csv) | Part 3, 30 °C setpoint, fixed `Kp=0.5`. |
| 2026-09-30 11:21:31 | [`20260930_112131_droop_kp1.csv`](20260930_112131_droop_kp1.csv) | Part 3, 30 °C setpoint, fixed `Kp=1`. |
| 2026-09-30 11:24:29 | [`20260930_112429_droop_kp2.csv`](20260930_112429_droop_kp2.csv) | Part 3, 30 °C setpoint, fixed `Kp=2`. |
| 2026-09-30 11:29:55 | [`20260930_112955_droop_kp4.csv`](20260930_112955_droop_kp4.csv) | Part 3, 30 °C setpoint, fixed `Kp=4`. |
| 2026-10-07 10:43:14 | [`20261007_104314_kp32_short_of_30c.csv`](20261007_104314_kp32_short_of_30c.csv) | Short `Kp=32` trial; the measured temperature stayed below 30 °C during this recording. |
| 2026-10-07 10:43:46 | [`20261007_104346_mixed_kp_setpoint_exploration.csv`](20261007_104346_mixed_kp_setpoint_exploration.csv) | Exploratory run with live changes among `Kp=64, 128, 50, 250` and 20/30 °C setpoints. Do not treat as one fixed-gain run. |
| 2026-10-07 10:50:05 | [`20261007_105005_kp250_20to30c_oscillation.csv`](20261007_105005_kp250_20to30c_oscillation.csv) | Pre-cool near 20 °C, then fixed `Kp=250` toward 30 °C; overshoot and repeated oscillation. |

[`part_04_droop_comparison.csv`](part_04_droop_comparison.csv) is a **derived** table for the five September 30 fixed-gain runs, not another raw experiment. The October 7 runs are described in the [Module 5 lab note](../../docs/module_notes/module_05_p_control.md); trial 3 is plotted as [temperature and signed PWM](../figures/kp250_20to30c_oscillation.png).
