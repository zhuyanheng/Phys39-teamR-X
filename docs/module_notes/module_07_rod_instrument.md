# Module 7 rod instrument: field record

## 2026-10-30: chosen holes and sensor positions

Source: the mounting choices and the distances measured with a ruler, as reported by the operator in
this session. The rod material is recorded as Aluminium 6061; whether it is 6061-T6 has not been
confirmed on the bench.

The physical holes used in this build are **2, 5, 7, 8, 9**, replacing the earlier 1, 3, 5, 7, 9
proposal. Physical hole numbers run from the TEC end towards the rod tip.

Channels follow the fixed mapping A0 = TEC, A1–A5 = T1–T5; the table maps the chosen holes onto those
five rod channels in order, and the labels must be checked against the CSV columns once installed. A0
stays at the TEC base and does not take one of the five rod holes.

### Coordinate convention

- The **first chosen measurement hole (physical hole 2)** is taken as the analysis origin `x = 0`, with
  the positive direction towards hole 9 and the rod tip.
- This origin is an analysis convention for this build. The course instructions start from the physical
  first rod hole; all later analysis must use the installed layout recorded here, and physical hole 2
  must not be re-labelled as physical hole 1.
- Operator report: physical hole 2 is **3 cm** from the "lowest point, near the A0 position". That point
  is recorded as the *bottom reference point*; it is not a surveyed position of the A0 sensing bead.
- The uncertainty of these distances, and the way hole centres and bead positions were taken, are still
  to be recorded.

### Raw distance record

| Between | Reported distance | Unit and note |
| --- | ---: | --- |
| bottom reference point → hole 2 | 3 | cm, stated explicitly by the operator |
| hole 2 → hole 5 | 3.85 | cm, stated explicitly by the operator |
| hole 5 → hole 7 | 5.1 | assumed cm; the operator did not repeat the unit |
| hole 7 → hole 8 | 5.1 | assumed cm; the operator did not repeat the unit |
| hole 8 → hole 9 | 5.1 | assumed cm; the operator did not repeat the unit |
| hole 9 → top end (rod tip) | 8 | cm, added by the operator afterwards |

### Cumulative position table

The cumulative values below are direct sums of the table above; no measurement uncertainty has been
estimated, and the digits kept do not imply verified precision.

| Arduino channel | Software temperature column | Probe | Physical hole | From bottom reference point (cm) | x relative to hole 2 (cm) | x (m) |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| A0 | `tec_C` | TEC | — | only known to be near the bottom, not surveyed | — | — |
| A1 | `rod1_C` | T1 | 2 | 3.00 | 0.00 | 0.0000 |
| A2 | `rod2_C` | T2 | 5 | 6.85 | 3.85 | 0.0385 |
| A3 | `rod3_C` | T3 | 7 | 11.95 | 8.95 | 0.0895 |
| A4 | `rod4_C` | T4 | 8 | 17.05 | 14.05 | 0.1405 |
| A5 | `rod5_C` | T5 | 9 | 22.15 | 19.15 | 0.1915 |
| — | — | rod tip, no probe | — | 30.15 | 27.15 | 0.2715 |

The measured boundary condition `T(0, t)` of the rod model uses T1 / A1 in hole 2; the PI feedback and
the safety path still use TEC / A0.

The analysis length runs from hole 2 to the rod tip:
`L = 3.85 + 5.1 + 5.1 + 5.1 + 8 = 27.15 cm = 0.2715 m`. Hole 9 is at `x = 19.15 cm`, still 8 cm from
the tip, so it is not an end point. The cumulative distance from the bottom reference point to the tip
is 30.15 cm; that can only be used as the overall physical length of the rod once the reference point is
confirmed to be the physical bottom end.

### Still to complete

- Confirm the actual channel → probe → hole assignment.
- Confirm that the unit of the last three 5.1 segments is cm.
- Rod diameter, overall physical length, how the geometry was measured, and the uncertainties.
- A photo of the installation with hole numbers, channel labels, the ruler and the positive coordinate
  direction.
- The same-temperature check over a temperature *span*: the 2026-10-30 and 2026-11-02 records give 0.48 °C
  agreement at one temperature only, which constrains an offset but never a gain.
- A stationary profile at a setpoint the interlock allows (40 °C, at most 43 °C — see the 2026-11-02 entry) and
  long enough for the far probes (≈ 30 min of hold, not 300 s).

## 2026-10-30 15:23–15:29: short 20 → 30 → 20 °C trial

Raw data: `Module_7/data/raw/module_07_rod_20261030_152300_037075_T20C_T30C_T20C.csv`. The tag was added on
2026-11-02 together with the others: `T20C → T30C → T20C` is the commanded setpoint sequence, the timestamp
is still the moment the GUI opened the file, and the rows and bytes are untouched (the SHA-256 in the quality
JSON below was recomputed from the renamed file and matches the pre-rename value).
Check script: `Module_7/python/analysis/pilot_run_check.py`; the numerical check and the SHA-256 of the
source file are stored in
`Module_7/data/processed/pilot_checks/module_07_rod_20261030_152300_037075_T20C_T30C_T20C_quality.json`; the
temperature traces are in
`Module_7/figures/pilot_checks/module_07_rod_20261030_152300_037075_T20C_T30C_T20C_temperatures.png`.

- 774 measurement rows, Arduino time 0.55–399.76 s (about 6 min 39 s), largest sampling interval 0.52 s,
  no duplicate or non-monotonic timestamps.
- All six temperature columns are valid; every row has `rod_ok=5`, `safety=OK`, `backlog_sample=0`. The
  event record shows a manual stop, not a software fault.
- PI settings `Kp=20 PWM/°C`, `Ki=0.1 PWM/(°C·s)`. By measurement rows: 62.31–225.54 s controlled to
  20 °C; 226.06–304.11 s controlled to 30 °C; 304.63–398.22 s back to 20 °C.
- During the first ≈ 60 s, before the controller acts, the six channels span at most 0.48 °C. This is the
  installed baseline and does **not** replace a common-temperature check over several bath temperatures.
- Last row of the heating phase (304.11 s): TEC 29.23 °C; T1–T5 at 24.76, 23.03, 22.25, 21.84, 21.47 °C,
  warmer near the base and cooler towards the tip.
- After returning to 20 °C, the observed peaks of T1, T2, T3, T4 occur at 308.26, 322.76, 337.75 and
  371.86 s respectively; T5 is still warming overall when the record ends. This ordering is what delayed
  thermal diffusion predicts; nothing so far suggests swapped or open probes, but contact error cannot be
  ruled out this way.
- Linear slopes over the last 60 s (°C/min): TEC −1.301, T1 −1.564, T2 −1.138, T3 −0.388, T4 +0.023,
  T5 +0.166. That fails the starting steady-state criterion of |dT/dt| < 0.02 °C/min on every probe, so
  the run cannot be used for the stationary-fin fit.
- The 30 °C hold lasted only about 78 s and the TEC peaked at 29.24 °C, so no steady-state control offset
  can be claimed from it. This was a small functional and propagation test, not the final 45 °C steady
  profile.
- Next step: freeze hole positions and channels, open a new data file, and record the full settling
  process from the initial state at a constant setpoint with the validated PI settings; record the room
  temperature far from the apparatus independently. The raw data stays untouched.

## 2026-11-02 10:00–10:17: a 20 °C hold and a 40 °C hold, and the 45 °C interlock trip

This session was meant to produce the final `20 → 45 °C` steady profile. It produced two transient step
records instead, and it established that the 45 °C setpoint cannot be reached by this firmware at all: the
safety interlock trips first.

### Raw files and their new names

The two files gained a setpoint tag on 2026-11-02, so that a file name says what was commanded instead of only
when the writer opened it. The tags are chronological: `T20C` = held at 20 °C, `trip45C` = the 45 °C attempt
the safety cut short, `T40C` = held at 40 °C. The timestamp in the name is still the moment the GUI created the
file, the rows and bytes are unchanged, and the SHA-256 of the file as checked is stored in the matching quality
JSON.

| Raw file | Wall clock | Rows | Arduino span | Commanded sequence |
| --- | --- | ---: | ---: | --- |
| `module_07_rod_20261102_100034_422916_T20C.csv` | 10:00:34–10:04:36 | 465 | 0.6–240.0 s | P for 51 s, then PI at **20 °C** (`Kp = 20` PWM/°C, `Ki = 0.1` PWM/(°C·s)), 52–240 s |
| `module_07_rod_20261102_100448_913799_T20C_trip45C_T40C.csv` | 10:04:48–10:17:22 | 1454 | 0.6–751.0 s | P for 19 s; PI at **20 °C** 20–314 s; setpoint step to **45 °C** at 314 s → **trip**; PI at **40 °C** (`Kp = 100`, `Ki = 0.3`) 362–751 s |

Both files pass `pilot_run_check.py`: largest sampling interval 0.52 s, no repeated or non-monotonic
timestamps, `rod_ok=5` on every measurement row, `safety=OK` on every measurement row (event rows leave the
column empty; the trip appears only in a `stop` event's note), raw hash unchanged after the check.
Machine-readable check: `Module_7/data/processed/pilot_checks/<raw stem>_quality.json`;
traces: `Module_7/figures/pilot_checks/<raw stem>_temperatures.png`.

The two runs do **not** use the same PI gains (`20 / 0.1` in the first, `100 / 0.3` in the second), and the
40 °C hold was restarted rather than stepped to from 20 °C, so the two files are two separate experiments, not
one experiment in two parts. Both are CRLF files (the GUI wrote the `csv` default `\r\n` at the time);
`Module_7/data/raw/**` is marked `-text`, so the committed bytes are exactly the bytes the SHA-256 was computed
on.

### The 45 °C setpoint cannot be reached: the interlock fires first

The second file records this sequence verbatim (host times):

| Host time | Event | Note |
| --- | --- | --- |
| 10:10:04 | `setpoint_step` → 45.0 °C | `Integral retained for a within-run setpoint step` |
| 10:10:19 | `stop` at 45.0 °C | `Unsafe report (TEC channel 45.22 C outside 10-45 C)` |

The TEC channel peaked at **45.22 °C** 15 s after the step. The firmware admits readings in 10–45 °C, so a
setpoint of exactly 45 °C on the channel that has to *reach* 45 °C always trips as soon as the reading
overshoots by any amount — 0.22 °C here. **A 45 °C steady state is therefore not producible by this build.**
The course's upper working point has to be re-planned at 40 °C (what was used here, ≈ 5 °C of margin) and at
most 43 °C. The trip itself behaved as designed: output cut, offending channel and value logged, no data lost,
nothing overheated.

### What the two holds do establish

| | 20 °C hold, first file | 40 °C hold, second file |
| --- | --- | --- |
| Length of the hold | 188 s (52–240 s) | 389 s (362–751 s) |
| `tec_C` at the end | 21.52 °C (minimum 20.48 °C at 215.8 s) | 39.89 °C, i.e. 0.11 °C below setpoint (peak 41.76 °C) |
| `tec_C` slope, last 60 s | +0.877 °C/min: the loop had *not* settled, it dipped below setpoint and came back | +0.029 °C/min: the base *is* steady |
| `rod1_C` … `rod5_C` at the end | 22.00, 22.12, 22.75, 23.04, 22.96 °C | 34.18, 31.64, 29.52, 27.93, 26.66 °C |
| Rod slopes, last 60 s | −0.162, −0.259, −0.258, −0.204, −0.151 °C/min (still cooling) | +0.374, +0.467, +0.501, +0.541, +0.545 °C/min (still heating) |

- The base is controllable: at 40 °C it sits 0.11 °C below setpoint after 6.5 min, with a residual slope at the
  measurement floor (0.03 °C/min). `Kp = 100`, `Ki = 0.3` are usable; `Kp = 20`, `Ki = 0.1` were not (the 20 °C
  hold oscillated and left the base 1.5 °C above setpoint after 3 min).
- The rod responds with the expected ordering: near-base probes move first and furthest, the tip probe last and
  least, and in the 40 °C hold every probe is still rising monotonically when the operator stops. That is the
  propagation signature the step-response part needs.
- The 20 °C holds are cooling steps with a base *colder* than the room, so `θ = T − T∞ < 0` there; the
  stationary-fin script refuses a negative-`θ` profile on purpose (see `module_07_stationary_fin.md`).

### What the holds do not establish: 300 s of recording is not 300 s of steady state

Both holds are far from the course starting criterion for a stationary profile (`|dT/dt| ≤ 0.02 °C/min` on every
channel for ≥ 600 s, plus a 0.1 °C first-third/last-third limit). The committed script on this data:

- `stationary_fin_fit.py <second file>` (defaults): **refuses**, exit code 2 — worst slope 2.418 °C/min on
  `tec_C` and third-to-third drift 16.721 °C in the closest 600 s window (that window reaches back into the 45 °C
  excursion).
- `stationary_fin_fit.py <second file> --hold 300`: **refuses**, exit code 2 — over the trailing 300 s the worst
  channel is `rod4_C` at **0.741 °C/min**, 37 × the 0.02 °C/min limit, and the first/last-third means differ by
  **2.466 °C**, 25 × the 0.1 °C budget.
- `stationary_fin_fit.py <first file>`: **refuses**, exit code 2 — the usable record lasts 239.4 s, shorter than
  any hold, with a 0.934 °C/min slope on `tec_C`.

Recorded length is not the binding limit; the rod's diffusion time is. For the 40 °C hold, the 60 s block slopes
of the five probes decay as follows (C/min, six blocks from 362 s to 751 s):

| Probe | Block slopes | Decay time constant | `0.02 °C/min` reached |
| --- | --- | ---: | ---: |
| `rod1_C` (x = 0) | 3.73, 1.40, 0.73, 0.52, 0.39, 0.32 | ≈ 130 s | ≈ 11 min after the step |
| `rod2_C` (3.85 cm) | 3.06, 1.62, 0.94, 0.66, 0.48, 0.41 | ≈ 150 s | ≈ 13 min |
| `rod3_C` (8.95 cm) | 1.97, 1.52, 1.02, 0.76, 0.57, 0.49 | ≈ 210 s | ≈ 16 min |
| `rod4_C` (14.05 cm) | 1.07, 1.17, 0.99, 0.78, 0.64, 0.55 | ≈ 390 s | ≈ 27 min |
| `rod5_C` (19.15 cm) | 0.42, 0.79, 0.85, 0.79, 0.68, 0.57 | peaks at 0.85, then falls too slowly to fit | > 27 min; plan ≥ 30 min |

**Planning figure: budget ≈ 30 min of hold after the step at 40 °C**, i.e. 4–5× what these two runs recorded.
The decay fit above was made outside the repository (log-linear regression of the 60 s block slopes); it is a
planning estimate, not a committed result — see the open item in `module_07_state.md`.

## Decision: skip the six-probe soak cross-calibration

The operator decided **not** to run the planned warm-water soak cross-calibration (runbook §3). The
reason: with the probes installed, the six channels already agree within 1 °C (0.48 °C worst case across
the 20 °C baseline above), and the probes are now permanently fitted in the TEC base and the rod holes,
so dismantling and re-installing them costs more than the check would recover.

### What this decision gives up

- **No per-channel `a_i`, `b_i`:** `Module_7/data/calibration/` will stay empty and the criteria in
  `cross_calibration_fit.py` get no measured input.
- The 0.48 °C baseline is **agreement at one temperature**, not a **linearity check over a span**: it
  constrains the offset `a_i` only, never the gain `b_i`. A 1 % gain error is 0.2 °C at `θ = 20 °C` and
  only 0.05 °C at the tip where `θ = 5 °C` (both as 1 % of `θ`), i.e. it scales with temperature and
  therefore acts exactly like a temperature-dependent offset — and a single steady profile **cannot
  detect this from its own data**.
- So every `θ(x)` in the profile carries up to ≈ 0.5 °C of per-probe offset, and that offset propagates
  straight into `m`.

### Quantified cost (recomputable with the script, not a feeling)

`probe_sensitivity()` in `Module_7/python/analysis/stationary_fin_fit.py` raises one probe at a time by
`--sensitivity-offset` (default 0.5 °C) and re-fits `m`. On the predicted profile (`m = 3.63 1/m`,
`θ₀ = 20 °C`, using the `L = 0.2715 m` and the hole positions recorded here):

| Probe raised | `x` (m) | Δm/m (+0.5 °C) | Δm/m (+1.0 °C) |
| --- | ---: | ---: | ---: |
| rod1 (`x = 0`, also sets θ₀) | 0.0000 | **+5.1 %** | **+10.0 %** |
| rod2 | 0.0385 | −0.8 % | −1.6 % |
| rod3 | 0.0895 | −1.6 % | −3.1 % |
| rod4 | 0.1405 | −2.1 % | −4.2 % |
| rod5 | 0.1915 | −2.4 % | −4.9 % |

- The most sensitive probe is the **base probe**: it sets both `θ₀` and the normalisation amplitude, so
  0.5 °C of offset is 2.5 % of `θ₀` and 5.1 % of `m`.
- The sensitivity scales as `offset/θ₀`: halve `θ₀` (10 °C) and every entry above doubles. **The formal
  profile therefore needs a large temperature span** (45 °C setpoint, `θ₀ ≈ 20 °C); do not fit the 30 °C
  trial point.
- Reporting convention: the uncertainty of `m` must be split into a statistical fitting term (`σ` from
  the script) and an **uncalibrated-offset term (≈ 5 %)**, the latter dominating. The main risk sits in
  rod1's hole and thermal contact, not at the far end of the rod.

### Checks that are still possible after this decision

- Cross-check within the same steady run: **treat rod2 as `x = 0`** (rod1 moves to `x = 3.85 cm`) and
  re-fit; the two `m` must agree within 5 %. This is a *relative*-offset test and needs no soak.
- Compare `θ(x)/θ(0)` between the 45 °C and 35 °C steady profiles: the same `m` must give the same
  dimensionless shape. If the shape depends on temperature there is a gain error (`b_i ≠ 1`). This is the
  substitute for a span check, needing one extra steady point and no rewiring.
- Both are written up in §6 of [module_07_stationary_fin.md](module_07_stationary_fin.md).

