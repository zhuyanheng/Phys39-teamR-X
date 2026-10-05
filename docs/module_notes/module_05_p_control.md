# Module 5: P-only temperature control

## Part 1: controller implementation

- Python GUI: `Module_5/python/p_only_tec_control_gui.py`.
- Arduino sketch: `Module_5/arduino/p_only_tec/p_only_tec.ino`, copied from the Module 4 source on 2026-09-29. Verify that this is the version actually uploaded before a powered run.
- At startup the GUI sends PWM 0 and leaves P control off. It waits for a recent, finite 10–45 °C measurement with `Safety: OK` before enabling P control.
- For each Arduino report, Python calculates `error = setpoint - temperature`, `signed_pwm = Kp * error`, sends `HEAT` for nonnegative signed PWM or `COOL` for negative signed PWM, and rounds/clamps `abs(signed_pwm)` to an integer 0–255.
- The GUI plots measured temperature, setpoint, measured PWM by direction, and error. It writes all measurements and control values to a timestamped CSV in `Module_5/data/`.
- While P control is active, setpoint and Kp can be edited and applied with the **Apply setpoint / Kp** button (or Enter). The new command is calculated from the latest valid temperature immediately, and each subsequent CSV sample records the applied settings. Editing text alone does not change the controller. For the formal Part 3 gain sweep, stop and restart each gain from PWM 0 as the assignment requires.
- Stop requests PWM 0. A reported safety fault, temperature outside 10–45 °C, or a measurement gap over 2 seconds stops P mode and requests PWM 0. The Arduino independently checks its 60 °C software limit and invalid sensor readings. A lost Python process cannot be relied on to send a final zero command; operate only with the instructor's approved hardware precautions and supervision.

## Still to verify on the physical apparatus

- [ ] Instructor-approved wiring, current limit, live sensor reading, and firmware version.
- [x] Start with PWM 0 and confirm both firmware outputs report 0 (`module_05_p_control_20260930_105823_730888.csv`, 0.56–11.16 s; firmware reports 0/0 and `Safety=OK`).
- [x] Low-gain HEAT and COOL feedback signs (Part 2); see the raw-data assessment below. Stop if temperature moves the wrong way in any future run.

The initial implementation checks above were software-only; the subsequent physical observations are recorded below.

## Part 2: low-gain sign test, 2026-09-30

Primary raw record: `Module_5/data/module_05_p_control_20260930_105823_730888.csv`. All 432 serial rows report `Safety=OK`. The first 22 PWM-0 samples average 23.283 °C (range 23.26–23.30 °C). The provisional Module 4 slopes are 0.4954 °C/PWM for heating and 0.1414 °C/PWM in cooling magnitude, so at `Kp=0.5 PWM/°C` the estimated loop gains are about 0.248 and 0.071, respectively; the slopes still need Module 4 steady-state revalidation.

| Segment | Setpoint, Kp | Firmware direction/PWM | Temperature observation | Assessment |
| --- | --- | --- | --- | --- |
| Heating, 12.18–59.76 s | 35 °C, 0.5 PWM/°C | HEAT, PWM 5–6 | 23.30 → 24.55 °C | Positive-error command and heating response supported. |
| PWM 0, 60.27–72.91 s | — | Both outputs 0 | 24.56 → 24.28 °C | The block cooled naturally while above ambient. |
| Cooling, 73.92–218.94 s | 15 °C, 0.5 PWM/°C | COOL, PWM 4–5 | 24.26 → 22.95 °C | Negative-error command and active cooling supported: 140 samples from 148.43 s onward were below the 23.26 °C minimum of the initial PWM-0 baseline; the final 20 samples averaged 22.961 °C. |

The earlier record, `module_05_p_control_20260930_104014_764248.csv`, shows the same command directions but did not establish active cooling below ambient. The new run supplies that missing evidence. The 15 °C target remains farther below ambient than the assignment's “slightly below room temperature” instruction; instructor approval for that choice is not recorded here. **Part 2 physical direction result: both HEAT and COOL supported.** Confirm the cooling-setpoint choice with the instructor if strict adherence to “slightly below” is required.

## Part 3: original droop-versus-gain plan

Use one heating setpoint of 30 °C and a fresh PWM-0 ambient baseline before the gain sweep. With the current 23.283 °C baseline and provisional heating susceptibility `χ_h = 0.4954 °C/PWM`, the estimated open-loop PWM needed for the 6.717 °C change is `P_required ≈ 6.717/0.4954 = 13.56`. For each candidate, `P0 = Kp × 6.717`; recalculate if the actual ambient baseline changes. The following is a **candidate range requiring instructor approval before powered runs**, not recorded measurements:

| Candidate Kp (PWM/°C) | Predicted initial P0 (PWM) | Estimated loop gain L=Kpχ_h | Relative to P_required |
| ---: | ---: | ---: | --- |
| 0.25 | 1.68 | 0.124 | Well below |
| 0.5 | 3.36 | 0.248 | Below |
| 1 | 6.72 | 0.495 | About half |
| 2 | 13.43 | 0.991 | Comparable |
| 4 | 26.87 | 1.982 | Above |

For **each** approved gain: stop P mode and confirm PWM 0; start the run at the same 30 °C setpoint; wait until temperature settles or clearly fails to settle; record the actual starting temperature, final/mean temperature, error, final PWM, response shape, and raw CSV filename. Do not treat changes made with the live Apply button as separate Part 3 gain runs. Save a representative time trace and eventually plot measured droop against Kp. Keep the instructor-approved range, safety observations, and any saturation or failure to settle in the notes.

## Part 3: recorded gain sweep, 2026-09-30

The five new runs used a 30 °C heating setpoint and separate P-control starts. Each CSV begins with PWM 0 and reports `Safety=OK` throughout. The first run's PWM-0 baseline (39 samples) averaged **23.1885 °C**. Later runs began while the block was still warm, so their PWM-0 temperatures are not used as room-temperature estimates. The measured temperatures and droops below use each run's last 20 seconds of active control (40 samples).

| Kp (PWM/°C) | Last-20-s mean T (°C) | Measured droop (°C) | Last-20-s mean PWM | Raw CSV |
| ---: | ---: | ---: | ---: | --- |
| 0.25 | 24.0000 | 6.0000 | 1.700 | `module_05_p_control_20260930_110723_090850.csv` |
| 0.5 | 24.7700 | 5.2300 | 3.000 | `module_05_p_control_20260930_111214_398504.csv` |
| 1 | 25.4977 | 4.5023 | 4.275 | `module_05_p_control_20260930_112131_559827.csv` |
| 2 | 26.7695 | 3.2305 | 6.000 | `module_05_p_control_20260930_112429_084527.csv` |
| 4 | 27.7400 | 2.2600 | 9.000 | `module_05_p_control_20260930_112955_213490.csv` |

The last-20-s temperature change was about 0.01–0.02 °C per run. That supports using these windows for a preliminary comparison; a longer documented steady-state criterion would be needed to establish true equilibrium. Instructor approval for the gain range is not recorded in these files.

## Part 4: predicted versus measured droop

Use the provisional Module 4 heating susceptibility `χ_h = 0.4954 °C/PWM` and the first run's ambient reference `T_amb = 23.1885 °C`. At equilibrium, `T = T_amb + χ_h P` and `P = Kp(T_set − T)`, hence

`e_pred = T_set − T = (T_set − T_amb)/(1 + Kp χ_h)`.

Here `T_set − T_amb = 6.8115 °C`. The loop gain is `L = Kp χ_h`, so predicted fractional droop is `e_pred/(T_set − T_amb) = 1/(1 + L)`.

| Kp (PWM/°C) | L | Measured droop (°C) | Predicted droop (°C) | Measured − predicted (°C) |
| ---: | ---: | ---: | ---: | ---: |
| 0.25 | 0.124 | 6.0000 | 6.0609 | −0.0609 |
| 0.5 | 0.248 | 5.2300 | 5.4593 | −0.2293 |
| 1 | 0.495 | 4.5023 | 4.5550 | −0.0527 |
| 2 | 0.991 | 3.2305 | 3.4215 | −0.1910 |
| 4 | 1.982 | 2.2600 | 2.2845 | −0.0245 |

The measured droop decreases with gain and is 0.02–0.23 °C below the prediction across the five points. This is close agreement for this provisional comparison, but the Module 4 susceptibility was derived from windows that still need steady-state revalidation. The ambient reference came from the first run only; the later warm starts and the limited final windows are additional limitations. Recompute from the raw records if the Module 4 slope or ambient estimate is updated.

- Reproducible calculation: `Module_5/python/plot_droop_comparison.py`
- Calculated values and provenance: `Module_5/data/part_04_droop_comparison.csv`
- Comparison plot: `Module_5/figures/part_04_measured_vs_predicted_droop.svg` (also `.png`)

## Part 5: high-gain response, preliminary assessment

The recorded runs give the following Part 5 summary. “Near flat” describes the last 20 s only; it is not proof of full thermal equilibrium. No run approached the PWM limit of 255.

| Kp (PWM/°C) | Last-20-s mean T (°C) | Last-20-s T range (°C) | Maximum active PWM | Saturation? | Response observation |
| ---: | ---: | --- | ---: | --- | --- |
| 0.25 | 24.0000 | 23.99–24.02 | 2 | No | Gradual heating; near-flat end |
| 0.5 | 24.7700 | 24.76–24.78 | 3 | No | Heating; near-flat end |
| 1 | 25.4977 | 25.49–25.51 | 5 | No | Heating; near-flat end |
| 2 | 26.7695 | 26.75–26.79 | 10 | No | Heating; near-flat end |
| 4 | 27.7400 | 27.73–27.75 | 19 | No | Heating; near-flat end, no sustained oscillation evident |

The highest recorded gain in the 2026-09-30 sweep is `Kp = 4 PWM/°C` (`L ≈ 1.98` using the provisional Module 4 heating slope). Its active-control trace lasts about 273 s. Temperature rises from approximately 25.24 °C to 27.74 °C and stays within 27.73–27.75 °C in the final 20 s. The active-run PWM is at most 19 and stays at 9 in the final 20 s; the 255-count limit is never reached. The file reports `Safety=OK` throughout. No sustained temperature oscillation is evident in this record. Since none was observed, amplitude, period, and frequency are not applicable for this tested range.

At the lowest gain, `Kp = 0.25 PWM/°C`, the temperature rises gradually and ends near 24.00 °C; its final-20-s PWM alternates between 1 and 2. Thus the highest recorded gain uses a larger PWM command and has smaller droop, with no observed saturation. These runs start at different block temperatures, so their absolute rise times are not a controlled settling-time comparison.

The assignment says to continue only through the **instructor-approved** gain range. If `Kp=4` is the approved maximum, report it as the highest tested gain and state that sustained oscillations did not appear. If the instructor has approved higher gains, collect additional runs under supervision, stopping and setting PWM to zero if oscillations grow or the run becomes unsafe. Approval of a higher range is not documented in the present records.

## Part 6: interpretation — one-lump model, loop gain, and transients

### Steady droop from the one-lump balance

Treat the TEC, block, and thermistor as one object at uniform temperature `T` with thermal capacity `C = dU/dT ≈ m c_p` (J/°C). Under P-only control the energy balance is

`C dT/dt = P_u Kp (T_set − T) − H (T − T_amb)`,

where `P_u` is the TEC power per signed PWM count (W/PWM count) and `H` is the lump's total passive conductance to the room (W/°C). Setting `dT/dt = 0` gives

`H (T − T_amb) = P_u Kp (T_set − T)`.

Collecting the `T` terms and solving,

`T_set − T = H (T_set − T_amb) / (H + P_u Kp) = (T_set − T_amb) / (1 + Kp P_u/H)`.

This is identical to Part 4's `e_pred = (T_set − T_amb)/(1 + Kp χ_h)` provided `χ_h = P_u/H`. The agreement requires the one-lump idealizations: one uniform temperature, linear passive heat loss (`H` constant), instantaneous measurement and actuation, no PWM saturation, and `P_u` approximately constant over the tested PWM/temperature range.

### Susceptibility is `P_u/H`, not a thermal capacity

Open the loop (`u` an independent input). At steady state `0 = P_u u − H(T − T_amb)`, so `T − T_amb = (P_u/H) u` and

`χ_{T,u} = dT/du = P_u/H`,  units `(W/PWM)/(W/°C) = °C/PWM`.

- `P_u` doubles → `χ` doubles (same `H`).
- `H` doubles → `χ` halves.
- `C` alone doubles → `χ` and the steady droop are unchanged; only the closed-loop time constant `τ_cl = C/(H + P_u Kp)` doubles.

So `C` controls how fast the lump moves but does not enter the steady droop, which is a balance between actuator strength per count and passive coupling. This is why the Part 4 susceptibility model (which has no `C`) predicts droop correctly.

### Loop gain and fractional droop

With `χ_h = 0.4954 °C/PWM` and `T_set − T_amb = 6.8115 °C`, the loop gain is `L = Kp χ_h` and the predicted fractional droop is `1/(1+L)`. Measured fractional droop is `(measured droop)/(T_set − T_amb)`.

| Kp (PWM/°C) | L | 1/(1+L) | measured fractional droop | measured − model |
| ---: | ---: | ---: | ---: | ---: |
| 0.25 | 0.124 | 0.890 | 0.881 | −0.009 |
| 0.5 | 0.248 | 0.801 | 0.768 | −0.034 |
| 1 | 0.495 | 0.669 | 0.661 | −0.008 |
| 2 | 0.991 | 0.502 | 0.474 | −0.028 |
| 4 | 1.982 | 0.335 | 0.332 | −0.004 |

The measured fractional droop tracks `1/(1+L)` closely, falling from about 0.88 at `L≈0.12` to about 0.33 at `L≈2.0`. Only `Kp=0.25` and `Kp=0.5` (`L≈0.12`, `0.25`) genuinely qualify as small gain (`L≪1`); `Kp=1` has `L≈0.5`, and `Kp=2` (`L≈1`) and `Kp=4` (`L≈2`) are comparable and strong feedback. The measured droop is consistently a little below the prediction (the block settles slightly closer to the setpoint), consistent with `χ_h = P_u/H` being a local approximation: the Module 4 heating slope spans 0–45 PWM, whereas these runs use only about 2–19 PWM near 24–28 °C, so `P_u` and `H` are not exactly constant. A heating setpoint uses `χ_h = 0.4954`; a cooling setpoint would instead use the cooling magnitude `0.1414 °C/PWM`, so this comparison is specific to the heating branch. Different starting temperatures also prevent a controlled settling-time comparison.

### First-order (transient) expectation

The algebraic model gives only the steady droop. For time dependence, define `θ = T − T_ss`. The one-lump P-only model gives

`dθ/dt = −θ/τ_cl`,  `τ_cl = C/(H + P_u Kp)`,

so `θ(t) = θ(0) e^(−t/τ_cl)`: the response approaches steady state exponentially and cannot sustain an oscillation. The 2026-09-30 sweep shows no sustained oscillation up to `Kp=4` (`L≈1.98`), consistent with this picture. Had oscillation appeared, the one-lump model would be missing physics or implementation detail — candidates are thermal delay between the TEC and thermistor, a second thermal mass, discrete sampling, sensor noise, or PWM saturation.

This derivation is preserved for the A3 feedback-and-model memo.
