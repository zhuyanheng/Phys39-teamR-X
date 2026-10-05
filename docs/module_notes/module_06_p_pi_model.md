# Module 6, Part I: P/PI control and lumped modeling

Team: Ricky Huang and Xavier Zhu. Course: Phys 39, Module 6, Part I. This note collects the guided one-lump derivation, the numerical checks, and the simulation/analysis evidence for A3. Progress follows the [lab-06 assignment](https://sethfraden.github.io/Phys39F26-course/labs/lab-06/).

## Part 1: Algebraic droop model

### 1a. Derivation

The measured Module 4 open-loop steady-state relationship (signed PWM `u`, positive = heat) is

`T = T_amb + χ_{T,u} u`, where `χ_{T,u} = dT/du` is the signed-PWM susceptibility (°C/PWM count, positive).

P-only feedback supplies

`u = Kp (T_set − T)`.

Substitute the controller law into the open-loop relationship:

`T = T_amb + χ_{T,u} Kp (T_set − T)`.

At steady state, collect all terms containing `T`:

`(1 + χ_{T,u} Kp) T = T_amb + χ_{T,u} Kp T_set`.

Subtract this from `T_set` to isolate the droop:

`T_set − T = (T_set − T_amb) / (1 + χ_{T,u} Kp)`.

The product `L = χ_{T,u} Kp` is dimensionless — the steady-state loop gain. The numerator `e_0 = T_set − T_amb` is the initial error when the block starts at ambient. (Part 2 will derive `χ_{T,u} = P_u/H` from the dimensional one-lump balance.)

### 1b. Numerical check (one Module 5 gain sweep)

Measured inputs (2026-09-30 sweep, 30 °C heating setpoint):

- `χ_{T,u} = 0.4954 °C/PWM` (provisional Module 4 heating slope)
- `T_amb = 23.1885 °C`
- `T_set = 30.0 °C`
- `e_0 = T_set − T_amb = 6.8115 °C`

Detailed example, `Kp = 2 PWM/°C`:

- `L = 2 × 0.4954 = 0.9908`
- `predicted droop = 6.8115 / (1 + 0.9908) = 3.4215 °C`
- `predicted settled T = 30 − 3.4215 = 26.5785 °C`
- `measured droop = 3.2305 °C` (measured settled `T = 26.7695 °C`)
- difference = `−0.1910 °C` (the block settled slightly closer to the setpoint than predicted)

| Kp (PWM/°C) | L = Kp·χ | Predicted droop (°C) | Predicted settled T (°C) | Measured droop (°C) | Measured settled T (°C) | Measured − predicted (°C) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.25 | 0.124 | 6.0609 | 23.9391 | 6.0000 | 24.0000 | −0.0609 |
| 0.5 | 0.248 | 5.4593 | 24.5407 | 5.2300 | 24.7700 | −0.2293 |
| 1 | 0.495 | 4.5550 | 25.4450 | 4.5023 | 25.4977 | −0.0527 |
| 2 | 0.991 | 3.4215 | 26.5785 | 3.2305 | 26.7695 | −0.1910 |
| 4 | 1.982 | 2.2845 | 27.7155 | 2.2600 | 27.7400 | −0.0245 |

Measured droop decreases with gain and tracks the prediction to within 0.02–0.23 °C (a few hundredths of the full `e_0 = 6.81 °C`). Source values are in [`part_04_droop_comparison.csv`](../../Module_5/data/part_04_droop_comparison.csv) and the [Module 5 note](module_05_p_control.md).

### 1c. One physical reason the prediction differs

The model treats `χ_{T,u} = P_u/H` as one constant, but it is a local linearization. The Module 4 heating slope was fitted over the full 0–45 PWM range, whereas the Module 5 runs use only about 2–19 PWM near 24–28 °C, where `P_u` (TEC power per count) and `H` (passive conductance) are not exactly constant. The measured droop is consistently a little below the prediction (the block settles slightly closer to the setpoint), consistent with a locally different effective susceptibility in this low-PWM, near-ambient region. The final-20-s windows are also not a rigorous steady-state proof, which adds uncertainty.

## Parts 2–9

Pending. Part 2 expresses the model with measured parameters (`χ = P_u/H`, `τ = C/H`), Part 3 estimates `τ` from a temperature step, Parts 4–5 simulate open-loop and P-only responses with Euler integration, Part 6 solves the P-controlled model analytically, Part 7 adds integral action, Part 8 covers windup, and Part 9 is the modeling checkpoint.
