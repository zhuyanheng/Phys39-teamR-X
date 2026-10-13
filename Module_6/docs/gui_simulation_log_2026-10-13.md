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
| 1 | 0.25 | 23.94 | 6.06 | 1.52 | [Screenshot](../figures/kp0.25_simulation.png) |

The user reported a settled temperature of 23.94 °C; the screenshot independently shows 23.94 °C, error 6.06 °C, P term about 1.52 PWM and I term 0.00 PWM. The visible temperature trace is flat over approximately 560–740 simulated seconds.

With chi_h = Pu,c × r ≈ 0.495446 °C/PWM, the predicted droop is
`(30 − 23.1885)/(1 + 0.495446 × 0.25) ≈ 6.0608 °C`,
and the predicted settled temperature is `30 − 6.0608 ≈ 23.9392 °C`.
The displayed result agrees to its 0.01 °C precision.

This rolling-window screenshot preserves the settled result, not the initial transient. If response speed is to be measured, preserve the beginning of a freshly reset run as well. This single upward one-lump simulation is not a complete two-lump Goldilocks simulation or a matched physical run.

Next: keep physical parameters and initial conditions fixed; reset and repeat P control at Kp=2, then Kp=4. Record settled temperature, error, applied PWM and the transient for each case.
