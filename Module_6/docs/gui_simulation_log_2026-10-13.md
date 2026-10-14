# GUI simulation log — 2026-10-13

These are user-operated mathematical simulations, not physical TEC measurements.

## Shared settings visible in Run 1 screenshot

- Process: `one_lump`; controller: `p`; parameter source: `direct constants`.
- Ambient and initial temperature: 23.1885 °C; setpoint: 30 °C.
- C = 73.0274 J/K; H = 1 W/K (arbitrary equivalent normalization).
- Cooling Pu,c = 0.1414167 W/PWM; heating/cooling ratio r = 3.50345.
- PWM limit: 255; Euler dt = 0.1 s; rolling window = 180 s.
- Anti-windup checked. The disabled Ki field reads 0.08, but I action is inactive in P mode; the displayed I term is zero.

## Recorded results

| Run | Kp (PWM/°C) | Displayed settled T (°C) | Displayed droop (°C) | Applied PWM (approximately) | Evidence |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 | 0.25 | 23.94 | 6.06 | 1.52 | [Screenshot](../figures/P_kp0.25_simulation.png) |
| 2 | 2 | 26.58 | 3.42 | not transcribed | [Screenshot](../figures/P_kp2_simulation.png); operator-reported settled temperature |
| 3 | 4 | 27.72 | 2.28 | not transcribed | [Screenshot](../figures/P_kp4_simulation.png); operator-reported settled temperature |

The user reported a settled temperature of 23.94 °C; the screenshot independently shows 23.94 °C, error 6.06 °C, P term about 1.52 PWM and I term 0.00 PWM. The visible temperature trace is flat over approximately 560–740 simulated seconds.

With chi_h = Pu,c × r ≈ 0.495446 °C/PWM, the predicted droop is
`(30 − 23.1885)/(1 + 0.495446 × 0.25) ≈ 6.0608 °C`,
and the predicted settled temperature is `30 − 6.0608 ≈ 23.9392 °C`.
The displayed result agrees to its 0.01 °C precision.

This rolling-window screenshot preserves the settled result, not the initial transient. If response speed is to be measured, preserve the beginning of a freshly reset run as well. This single upward one-lump simulation is not a complete two-lump Goldilocks simulation or a matched physical run.

## Operator-reported PI observations, 2026-10-14

| Kp (PWM/°C) | Ki (PWM/(°C s)) | Reported final temperature | Observation | Saved image |
| ---: | ---: | ---: | --- | --- |
| 2 | 0.01 | 30 °C | Approaches setpoint | [Screenshot](../figures/PI_kp2_ki0.01.png) |
| 2 | 0.08 | 30 °C | Faster approach; operator confirms no observed overshoot | [Screenshot](../figures/PI_kp2_ki0.08.png) |

These are reported observations of the user's GUI runs, not new physical measurements.
No full raw transient, peak temperature, or quantitative settling time has been
provided. The previously scripted reset-from-ambient Ki=0.08 case predicts an
overshoot; do not silently substitute that predicted peak for the user's
observation. A complete fresh-reset trace and confirmed initial integral state
would be needed to resolve the difference.

Next: prepare the physical PI controller for instructor review and matched P/PI experiments.
