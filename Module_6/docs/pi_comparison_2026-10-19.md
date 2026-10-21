# Three retained physical PI runs — 2026-10-19

All three use Kp=20 PWM/°C, PWM limit=255, conditional anti-windup, and a
20→30→20°C sequence with integral retained across setpoint steps. Earlier
discarded measurements are excluded. Raw files are unchanged.

| Ki (PWM/(°C s)) | Source in ../data/physical/ | Retained run_id |
|---:|---|---:|
| 0.1 | pi_kp_20_ki_0p1_20261019_093424_268559.csv | 3 |
| 0.2 | pi_kp_20_ki_0p2_20261019_095648_364327.csv | 2 |
| 0.5 | pi_kp_20_ki_0p5_20261019_101544_769937.csv | 3 |

Short preliminary runs are excluded. Initial 20°C conditioning is not treated
as the downward step from 30°C.

| Ki | Heating initial T (°C) | Heating maximum (°C) | Heating settling (s) | Cooling initial T (°C) | Cooling minimum (°C) | Cooling settling (s) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.1 | 19.97 | 30.01 | 401.35 | 29.93 | 20.02 | 127.43 |
| 0.2 | 20.03 | 30.03 | 138.04 | 29.98 | 19.73 | 199.19 |
| 0.5 | 19.99 | 30.82 | 27.51 | 30.02 | 18.92 | 168.67 |

Settling: earliest sample after the step whose remaining observations stay
within target ±0.2°C, with at least 60 s of remaining observations. Step times
use first post-step measurement, giving roughly one sample timing uncertainty.
Settling times do not imply monotonic response before the settling point.
Percent overshoot should use each measured starting temperature and target
as the step amplitude; the approximate 10°C-step percentages are 0.1%, 0.3%,
8.2% upward and 0%, 2.7%, 10.8% downward, respectively. Tiny excursions near
the sensor's reported resolution are not evidence of meaningful overshoot.

| Ki | Heating last-60-s mean (°C) | Cooling last-60-s mean (°C) |
|---:|---:|---:|
| 0.1 | 29.9306 | 20.0275 |
| 0.2 | 29.9980 | 19.9580 |
| 0.5 | 30.0382 | 19.9672 |

All retained active measurements report Safety=OK and computed saturation=0.
This does not measure electrical current or independently certify hardware.
Increasing Ki produced larger target excursions, especially on cooling, while
heating settling became faster. Cooling settling is not monotonic in Ki.
The data compare approximately equal step sizes, so they do not independently
test how changing step amplitude changes overshoot. Integral memory and
thermal inertia are plausible contributors; saturation-induced windup is not
demonstrated by these runs.

Next: produce the three matched PI temperature/PWM/P/I/error plots, quantify
rise time and highest-Ki step metrics in both directions, check availability
of three matched P runs (same targets and limit), then make the corresponding
six two-lump simulations and complete A3. Do not substitute old unmatched P
traces for the required matched runs without documenting the limitation.
