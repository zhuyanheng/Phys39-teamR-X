# Module 7: Aluminium Rod Instrument, Step Response And Stationary Fin

Module 7 replaces Module 6's "one or two temperatures" model with a spatially distributed `T(x, t)`.
All three parts share one model-testing chain: predict → measure → compare → judge.

**Before doing anything, read the [lab-day runbook (S16 → S17)](../docs/module_notes/module_07_lab_day_runbook_2026-10-26.md)**:
it orders the work by dependency. This file is the background and requirement summary.
**[`docs/module_notes/module_07_state.md`](../docs/module_notes/module_07_state.md)** records where the work
currently stands (what is verified, what is missing, the known warts) — read it first if you are picking the
module up cold.

| Part | Core question | What we do | Assessed by |
|---|---|---|---|
| Part I Heat-transport foundations | How do the constitutive law and energy conservation produce the temperature equation? | Explain Fourier's law, derive the one-dimensional heat equation, establish the Biot criterion | A4 Part 1, C5 oral |
| Part II Finite/infinite rod theory | What steady profile comes out of axial conduction, side losses and the end condition? | Derive the finite-length solution and the semi-infinite limit, do two model-validity checks | A4 Parts 2–4 |
| Part III Experiment | Do these assumptions and predictions describe *our* aluminium rod? | Six-channel cross-check, step response, steady profile, fits and residuals | C5, formative record, C6 evidence |

The three parts layer on one another rather than being three separate models:

- Part I: keeps `∂T/∂t`, **no** lateral loss;
- Part II: **no** `∂T/∂t` (steady), **with** lateral loss;
- Part III: keeps both → `ρcA ∂θ/∂t = kA ∂²θ/∂x² − hPθ`.

## 0. Current timeline (most urgent first)

| Time | Event |
|---|---|
| Mon 10/26, S16 (**today**) | In class: review finite-rod theory, compare finite vs semi-infinite, compute `Bi⊥`, build the sensor map and cross-check the probes, start the baseline and the step measurement |
| Wed 10/28, S17 | In class: finish the simultaneous step response and the steady profile; run the finite and semi-infinite fits |
| **Wed 10/28 09:05** | **A4 submission** (individual, 10 marks, Moodle `A4_Lastname.pdf` + repository `docs/assessments/a4_finite_length_biot.md`) |
| **Wed 10/28 11:55** | **C5 Moodle receipt** deadline; it must cite pushed acquisition code and evidence commits |
| Wed 10/28, in class | C5 live demonstration (sensor map, calibration, simultaneous acquisition, baseline/step data, uncertainty) |

Key judgement: **A4 needs no experimental data at all** (the course-supplied rod parameters and sensor
positions are enough), so it can proceed in parallel while hardware and calibration are pending. Only C5
depends on the hardware and the calibration.

## 1. Formula sheet

Write `θ(x, t) = T(x, t) − T∞`, where `T∞` is the room temperature far from the apparatus (not a reading
taken next to the TEC).

**General governing equation (full Part III form)**

```text
ρcA ∂θ/∂t = kA ∂²θ/∂x² − hPθ
∂θ/∂t = α ∂²θ/∂x² − νθ,   α = k/(ρc),   ν = hP/(ρcA)
```

**Stationary fin equation (Part II)**

```text
d²θ/dx² − m²θ = 0,   m² = hP/(kA) = ν/α,   1/m = decay length
```

**Finite length with an insulated tip (Lienhard 4.41)**

```text
Θ(x) = θ(x)/θ(0) = cosh[m(L − x)] / cosh(mL)
Θ_tip = 1/cosh(mL)
```

**Semi-infinite limit (4.50):** `Θ∞(x) = e^(−mx)`, valid when `mL ≫ 1`.

**Finite-end error (A4 Part 3 criterion)**

```text
ε_T(x) = |Θ_finite(x) − Θ∞(x)| / |Θ_finite(x)|      starting criterion ε_T < 5 %
```

**Transverse Biot number (A4 Part 4, tube radius)**

```text
Bi⊥ = h(A/P)/k = hR/(2k) = (mR/2)² = (md/4)² ≪ 1
```

**Parallel Biot number (along the rod)**

```text
Bi∥ = hPL²/(kA) = (mL)²
```

**Boundary conditions:** `x = 0` is Dirichlet (the measured `T(0, t)` from rod thermistor 1) and `x = L` is
Neumann, insulated (`dT/dx = 0`); convection off the end face turns it into a Robin condition.

**Keep these two ideas apart:** `Bi⊥` tests whether *one temperature per cross-section* is enough (radial
direction); `mL` and `ε_T(x)` test whether *the far end can be ignored* (axial direction). **The two
conclusions must be written separately**, never merged into a single "the rod is one-dimensional".

**Why a steady-state experiment cannot separate `k` from `h`:** the fit yields only one combination,
`m² = hP/(kA)`. The Ångström periodic experiment in Module 8 supplies the second independent measurement
needed to separate `k` and `h`.

## 2. A4: Finite-Rod Model And Validity Checks (individual, 10 marks)

- Type: individual, 10 marks; due **Wed 10/28 09:05**.
- Moodle file: `A4_Lastname.pdf`; repository file: `docs/assessments/a4_finite_length_biot.md`.
- Submit both the PDF and the repository file, with name, assignment number, date, repository URL and the
  **exact Git commit hash** on the first page.
- Units and dimensional checks are required throughout.

Four parts, matching the rubric one-to-one:

| Part | Content | Marks |
|---|---|---|
| Part 1 | **Lienhard Problem 1.3** with Fourier's law (assigned in Part I): show how the law produces each result, with units, and point out the physically unreasonable result | 1 |
| Part 2 | From energy conservation + Fourier's law + Newton's law of cooling, derive the stationary fin equation; derive the finite-length insulated-tip solution following Lienhard §4.5; explain the physical meaning of both boundary conditions | 3 |
| Part 3 | Take the semi-infinite limit with **Problem 4.12**; quantify the end-condition approximation with **Example 4.8** and **Problem 4.20**; compute `mL` and `ε_T(x)` for every course-rod sensor; the conclusion must state which sensor positions and which error criterion it depends on | 3 |
| Part 4 | Compute `Bi⊥` for the course rod and give the "one temperature per cross-section" conclusion **separately** (never merged with the Part 3 length conclusion); then answer the applied question on heat sinks vs spacecraft radiators: which one allows Newton's law of cooling, why there is no convection in space, and which radiation law replaces it (Stefan–Boltzmann `q″ = εσ(T_s⁴ − T_sur⁴)`) | 2 |
| Overall | Completeness, dimensional checks, clarity, exact Git checkpoint citation | 1 |

Reading route: selected Chapter 1 of Lienhard (energy conservation, thermal resistance, heat capacity,
lumped model) plus §4.5, textbook pp. 163–173 (follow the derivation, not just the result).

## 3. C5: Rod Instrument And Data-Acquisition Chain (team)

Demonstrated in class on Wed 10/28; the receipt is due before 11:55 AM and must cite pushed commits. It has
to show:

- rod thermistors that have been calibrated or cross-checked;
- recorded sensor coordinates and wiring;
- a simultaneous six-channel record;
- baseline and first step-response data;
- files with timestamps, units, channel labels and experiment notes;
- every member able to explain the measurement chain and **one dominant uncertainty**.

## 4. Experimental sequence (Parts 1 → 2 → 3)

**Part 1 — sensor map and cross-check**

1. Rod material 6061-T6 aluminium; measure `d`, the overall length, and the analysis length `L` from the
   first thermistor hole to the rod tip; compute `A` and `P` in SI units.
2. Name the 6 thermistors and fix the channels: `A0` = TEC base, `A1`–`A5` = rod 1–5.
3. Same-temperature check: put all six probes into warm water (`20–60 °C`), let it cool slowly for ≥ 60 s
   while stirring to keep it uniform; immerse only the waterproof ends and keep the connectors dry.
4. Using `tec_C` as reference, fit `T_TEC = a_i + b_i T_i` per channel and correct
   `T_i,corrected = a_i + b_i T_i`.
5. Check `ΔT_i = T_i,corrected − T_TEC` against `T_TEC`: the starting criterion is a corrected mean offset
   < `0.2 °C` with no residual trend larger than `0.2 °C`.
6. Raw data is never overwritten; the correction coefficients are stored in a separate file and applied
   during analysis.
7. Fit rod 1 into the first hole and define that hole as `x = 0`; measure the other 4 positions and the tip
   (`x = L`), recording the uncertainty of every position and of `L`; draw or photograph the labels,
   channels, coordinate direction and positions.

> **Skip note: steps 3–5 above (the soak calibration) were decided against.** The probes are already fitted
> permanently into the TEC base and the rod holes, and the installed spread is within 1 °C.
> The cost is quantified: 0.5 °C of offset on any probe moves `m` by 5.1 % (the base probe is the most
> sensitive), so the reported `m` must carry an "uncalibrated offset ≈ 5 %" term, together with the
> substitute checks in the [field record](../docs/module_notes/module_07_rod_instrument.md) (re-fit with a
> different reference probe; compare the dimensionless shape at two temperatures).
> `Module_7/python/analysis/cross_calibration_fit.py` and `data/calibration/` therefore stay unused for now, ready
> for a real soak later.

**Part 2 — choose the positions, then the step response**

1. Start with a `T_set = 45 °C` steady-state trial (faster, but a smaller span; higher gives a larger span
   but is slower and loses more heat; **never exceed 55 °C**).
2. Move the remaining 4 probes between holes and choose positions from `ln θ` vs `x`: the farthest point
   must satisfy `0 < θ₅ ≤ θ₁/e`, the points must spread over the semilog plot instead of bunching at one
   end, and none may sit in noise or room-temperature drift.
3. Once the positions are fixed, do not move them again; record each position and its uncertainty.
4. First equilibrate the whole rod at `20 °C`, recording the room temperature and all 6 channels, and
   confirm the channel differences are inside the calibration criterion.
5. Run a **non-oscillatory** `20 → 45 °C` step with the PI controller and record continuously until the
   steady-state criterion is met.
6. Plot all temperatures on one time axis and explain why farther probes respond later and with smaller
   amplitude.
7. Save the **commanded** TEC temperature, the **measured** TEC temperature and the **measured rod 1
   `T(0, t)`** (the model boundary condition uses rod 1, not the TEC setpoint or the TEC thermistor).

**Part 3 — stationary fin profile**

1. Before the run, write down the predicted profile shape and the steady-state criterion (starting
   criterion: every probe with `|dT_i/dt| < 0.02 °C/min` for ≥ 10 min). The script implements **two
   simultaneous** conditions: a whole-window least-squares slope ≤ 0.02 °C/min and a first-third vs
   last-third mean difference ≤ 0.1 °C — which catches "the window opens inside a transient", something a
   whole-window slope alone would let through.
2. Use the trailing steady segment of the `20 → 45 °C` step above; **no second heating run is needed**.
3. Once the criterion is met, average over the longest qualifying **trailing** window: the script puts the
   window start after the last transient, averages each channel inside the window (± standard deviation)
   and writes `_stationary_profile.csv`; a run that fails is refused (exit code 2, nothing written).
4. Plot `θ` vs `x` with error bars, fit **both** the finite (cosh) and semi-infinite (exponential) models,
   plot both residual sets, and report `m` (1/m) with its uncertainty and `1/m` (m). One-line command:
   "Part 3 analysis" in §5.
5. Report how much `m` moves when the finite end is ignored, compared with the fitting uncertainty.
6. Discuss sensor position error, room-temperature drift, poor thermal contact, and the measured evidence
   for the end boundary condition.
7. Compare against the prediction record: which assumptions are supported, which model fits better, and
   what unexplained deviation remains.

## 5. Six-channel software extension (Module 6 stays as the working checkpoint)

**Rule:** Module 6's Arduino sketch and Python GUI are **left exactly as they are**; Module 7 versions are
copied and then modified. The TEC base thermistor remains the only feedback and safety sensor; the five rod
channels only measure and never enter the PI control law.

Four stages, each one working before the next starts:

**Stage 1 — Arduino six-channel acquisition (implemented)**

File: `Module_7/arduino/module_07_rod_controller/module_07_rod_controller.ino` (a copy of the Module 6
sketch; the command protocol, H-bridge pins, PWM = 0 at power-up, the 60 °C software limit and the
`!isfinite` shutdown logic are all unchanged). The sketch folder keeps the module prefix because Arduino
sketch names must be unique, and it records where the file came from.

- Channels: `A0` = TEC base (**the only** PI feedback and safety input), `A1`–`A5` = rod 1–5.
- Sampling budget: the TEC channel averages 1000 ADC readings per cycle (as in Module 6), each rod channel
  100. Reason: one AVR `analogRead` takes about 112 µs, so six channels at 1000 readings each would take
  ~670 ms, break the 500 ms cycle and add phase lag to the controller; one full scan currently takes ~168 ms.
- A rod reading outside `-20…90 °C` is sent as `nan` and does not count towards `rod_ok`, but it does **not**
  trigger an actuator shutdown — a loose rod probe must not abort a 40 min steady run. The TEC channel keeps
  the original shutdown rule.
- Exactly **one** complete record per cycle, with a fixed field order:

```text
#DATA,time_s,tec_C,rod1_C,rod2_C,rod3_C,rod4_C,rod5_C,pwm,heat_cool,heat_pwm,cool_pwm,limit_C,safety,rod_ok
DATA,12.50,23.41,23.38,23.36,23.34,23.31,23.29,120,1,120,0,60.00,OK,5
```

- At startup the firmware prints four header lines `#firmware`, `#channels`, `#pins`, `#DATA,...`. Every
  header or diagnostic line starts with `#`; only lines starting with `DATA,` are data. `heat_pwm`/`cool_pwm`
  are the outputs the firmware reports (not a substitute for measuring the pins), and `limit_C` is the
  on-record evidence of the software limit.
- `setpoint_C` is not part of the firmware (it is the PI target) and is appended to the CSV by Python.
- Compile check (2026-10-26): `arduino-cli compile --fqbn arduino:avr:uno` → 7844 B flash (24 %), 545 B RAM
  (26 %).

**Stage 2 — Python display and raw logging (implemented)**

Files: `Module_7/python/rod_acquisition_gui.py` (a copy of the Module 6 GUI) +
`Module_7/python/rod_protocol.py` (a Qt-free parser) + `Module_7/run_rod_acquisition.command`.

- `PIController` is imported straight from `Module_6/python/` and **not** copied — the same approach as
  Module 6 reusing Module 5's `parse_measurement`, so the control arithmetic exists in exactly one place.
- The parser and the firmware header are cross-checked by `Module_7/python/test_rod_protocol.py` (21 tests,
  `python3 Module_7/python/test_rod_protocol.py`, no Qt, serial port or Arduino needed).
- CSV: `Module_7/data/raw/module_07_rod_<timestamp>.csv` — the GUI's scratch name, because only the operator
  knows what a run is for; it is renamed to its purpose name when the run is written up (see the naming rules
  below). The first 14 measurement columns have the **same
  names and order** as the `DATA` line
  (`time_s, tec_C, rod1_C, rod2_C, rod3_C, rod4_C, rod5_C, pwm, heat_cool, heat_pwm, cool_pwm, limit_C,
  safety, rod_ok`, generated by `rod_protocol.py`; editing the names by hand makes the tests fail), followed
  by the control columns (`setpoint_C`, `error_C`, `p_term_pwm`, `i_term_pwm`, `sent_signed_pwm`, …), so one
  CSV row still explains the actuator command at that instant.
- Two plots, not one: the TEC base with its dashed setpoint, then rods A1–A5 on their own
  auto-ranged axis (fixed colour per channel, probe distance in the legend). A single shared
  y-axis would draw the rods as one flat line — the TEC spans 15–45 °C while the rods sit
  within a degree or two of each other, and the difference between them is the measurement.
  The two plots share one x-axis (zooming either zooms both); PWM and P/I terms are in the CSV
  and in the readout line, not in a panel.
- The x axis always spans the **whole run from t = 0** (no sliding window — the rod settles over tens
  of minutes, so Module 6's 180 s window would hide everything the run is about). Early rows are never
  discarded, only the oldest beyond `HISTORY_LIMIT` (50 000 rows ≈ 6.9 h at the 500 ms report period),
  so zooming back out to t = 0 always works. To look at a detail, zoom with the wheel and pan by
  dragging: the first zoom unticked "X axis: whole run" so the next sample does not pull the view away,
  and **Fit x** (or re-ticking the box) returns to the full run. The y axis rescales to the visible
  x-window (`setAutoVisible(y=True)`), so zooming into the 30 min hold re-expands the rod spread
  instead of fitting the 20–40 °C warm-up.
- Malformed lines are counted and skipped without crashing (`rows ok/bad`); lines starting with `#` are not
  counted as bad; the file is opened in `'x'` mode so it is never overwritten; every row is flushed.
- A `Mark event` button writes a commented event into the CSV (steady-state verdict, probe moved, calibration
  started, …).
- End-to-end verification (2026-10-26, `QT_QPA_PLATFORM=offscreen` with a fake serial port): headers and bad
  lines ignored, 20 CSV rows written (including `connect`/`stop`/`operator_mark` event rows), a 25→45 °C step
  emitting `SET PWM … DIR HEAT`, a `nan` rod channel **not** shutting down, and both `SHUTDOWN` and a 46 °C
  TEC reading shutting the actuator down — all passing.

How to run (needs the project `.venv` with `PySide6`/`pyqtgraph`/`pyserial` installed from
`requirements.txt`):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
Module_7/run_rod_acquisition.command --preview   # no serial port, just checks the window
Module_7/run_rod_acquisition.command             # live: choose port → Connect (PWM 0) → Start P / PI
```

The first power-up, step by step, is in the
[Step 1 on-site procedure](../docs/module_notes/module_07_step1_integration_check.md) (wiring diagram,
expected voltage at each temperature, per-channel fingerprint table, fault injection, troubleshooting table).

**Stage 3 — cross-calibration analysis (stand-alone script)**

```bash
.venv/bin/python Module_7/python/analysis/cross_calibration_fit.py \
    Module_7/data/raw/module_07_rod_stationary_40C.csv   # without an argument the newest file in raw/
```

- Reads the raw CSV only (the bytes in `raw/` are unchanged, and a test guards that), fits
  `T_TEC = a_i + b_i T_i` per rod channel, and by default uses only rows with `event=measurement` where both
  `tec_C` and that rod channel are finite (a few hundred rows).
- Plots `T_i` vs `T_TEC` (identity line and fitted line) and the corrected residual
  `(a_i + b_i T_i) − T_TEC` vs `T_TEC`; the figure goes to `figures/calibration/<raw file>_fit.png`.
- Writes the calibration table to `data/calibration/<raw file>_calibration_table.csv`: channel, `a_i`, `b_i`,
  number of points, temperature range, residual mean/standard deviation/maximum magnitude, `before` (mean
  offset without correction), the three criteria and the overall verdict.
- Also saves "original columns + `rod1_corrected_C`…`rod5_corrected_C`" to
  `data/calibration/<raw file>_corrected.csv`; original columns are untouched and `nan` stays `nan` in the
  corrected columns.
- Criteria (matching the runbook, adjustable with `--criterion-*`): `|residual mean| ≤ 0.2 °C`, residual
  curvature ≤ 0.2 °C, `max|residual| ≤ 0.2 °C`. If any channel fails, the exit code is 2 and the message asks
  for a new soak.
- **How to read the criteria:** the fit has an intercept, so the residual mean is zero by construction (it is
  only a self-check that the intercept came out right); a straight residual tilt is absorbed by `b` as well,
  so "trend" is measured as **curvature** (mean of the middle half minus the mean of the two end quarters);
  what really detects a lagging or detached probe is `max|residual|` plus the curvature term.
- The reference is itself an uncalibrated A0 probe (nominal β = 4540 K; a 1 % error in β is ≈ 0.6 °C), so this
  is a **relative-consistency** calibration, not an absolute-accuracy one — the report must say so. **This
  module decided against the soak calibration** (see the skip note in §4 Part 1 and the
  [field record](../docs/module_notes/module_07_rod_instrument.md)), so the script is kept here only as a
  backfill tool.

**Part 3 analysis — steady-profile fit (stand-alone script, standard library only, matplotlib for figures)**

```bash
.venv/bin/python Module_7/python/analysis/stationary_fin_fit.py \
    Module_7/data/raw/<run>.csv --ambient <room temperature far from the apparatus, °C>
```

- Criteria first: the script looks for the longest qualifying **trailing** window (whole-window
  `|dT/dt| ≤ 0.02 °C/min` and a first-third/last-third mean difference ≤ 0.1 °C, window ≥ `--hold 600` s).
  If there is none it **refuses** (exit code 2, nothing written) and prints where the closest window falls
  short (which channel, how many °C/min, how many °C).
- Profile: per-channel mean ± sample standard deviation inside the window (with the sample count),
  `θ = T − T∞`; `T∞` comes from a measured `--ambient`, otherwise the script fits `T∞` **together with** the
  profile (`m` and `T∞`, profile likelihood, `σ` not reported).
- Fits: the finite model `Θ = cosh[m(L−x)]/cosh(mL)` takes its amplitude from the measured `θ(0)` and fits
  only `m`; the semi-infinite `Θ = e^(−mx)` is a log-linear regression on the same data as a control. Both
  residual sets go into the CSV and the figure.
- Uncertainty: `σ_m` comes from the curvature of SSR in `m` (`dof = N − 1`) and the output states "1 fitted
  parameter"; the **per-probe uncalibrated offset (≈ 5 %, from the skipped soak) must be added on top** and is
  given by the `probe_offset_sensitivity` table: raise one probe by `--sensitivity-offset` (default 0.5 °C) and
  re-fit to see how far `m` moves.
- Outputs (default directories are the repository convention):
  - `Module_7/data/processed/<run>_stationary_fit.json` — criteria, window, per-point profile, both models,
    `σ`, the `ε_T` table, `Bi∥`/`Bi⊥`, the sensitivity table, the source SHA-256 (strict JSON, non-finite
    floats written as `null`);
  - `Module_7/data/processed/<run>_stationary_profile.csv` — `label, x_m, temperature_C, std_C, samples,
    theta_C` plus both model values and residuals;
  - `Module_7/figures/part_03_stationary_profile.png` — profile, both models and both residual sets
    (rename with `--figure-name`).
- The default geometry is the hole layout from the
  [field record](../docs/module_notes/module_07_rod_instrument.md) (`x = 0, 3.85, 8.95, 14.05, 19.15 cm`,
  `L = 27.15 cm`), overridable with `--positions` / `--length`; add `--diameter-is-measured` only after the
  diameter has really been measured, otherwise the output states that the diameter is nominal.
- 20 hardware-free tests: `.venv/bin/python Module_7/python/test_stationary_fin_fit.py` (recovering a known
  `m` from a synthetic profile, the semi-infinite bias, the closed-form `ε_T`, the refusal logic, an unchanged
  raw-file hash, strict and portable JSON).

**Stage 4 — pre-calibration integration check**

- Heat one probe on its own and confirm that only its Arduino and Python channel changes;
- Confirm that "one `DATA` line = one set of displayed values = one CSV row";
- Unplug one rod probe and confirm the fault is visible and does **not** break the TEC base safety shutdown;
- Restart both programs and confirm PWM starts at 0 and a new data file is created;
- Write the sketch/GUI/analysis file names and the commit hash into the sensor map.

## 6. Prediction record (must be written down before the first heating run)

What has to be recorded:

1. the response order of the probes;
2. how the response amplitude changes with distance;
3. the qualitative shape of the stationary profile;
4. whether the finite end should be visible inside the measured range.

The numbers below are a **rough estimate from the course geometry plus literature orders of magnitude**,
written only to form an expectation; they must be replaced once the measured `d`, `L`, positions and `m` exist.

Assumptions: 6061-T6 `k ≈ 167 W/(m·K)`, `d = 12.7 mm`, natural convection `h = 5–10 W/(m²·K)`,
`L = 0.30 m` (**to be measured**).

| `h` (W/m²K) | `m` (1/m) | `1/m` (m) | `mL` | `Θ_tip` | `Bi⊥` |
|---|---|---|---|---|---|
| 5 | 3.07 | 0.326 | 0.92 | 0.69 | 9.5×10⁻⁵ |
| 7 | 3.63 | 0.275 | 1.09 | 0.60 | 1.3×10⁻⁴ |
| 10 | 4.34 | 0.230 | 1.30 | 0.51 | 1.9×10⁻⁴ |

Corresponding finite-end error `ε_T(x)` under the same assumptions:

| `x` (m) | 0.05 | 0.10 | 0.15 | 0.20 | 0.25 |
|---|---|---|---|---|---|
| `ε_T` (h=5) | 4.7% | 10% | 17% | 25% | 33% |
| `ε_T` (h=7) | 4.3% | 9.8% | 17% | 25% | 34% |
| `ε_T` (h=10) | 3.6% | 8.7% | 16% | 24% | 35% |

Two **testable** predictions follow:

- `Bi⊥ ~ 10⁻⁴ ≪ 1`: the one-dimensional radial approximation is almost certainly valid (large `k`, small `d`).
- `mL ~ 1` and the tip still carries 50–70 % of the base excess, so **the semi-infinite approximation already
  misses the 5 % criterion at `x ≳ 5 cm`**. A4 Part 3 must therefore keep the finite-length cosh solution and
  state explicitly that "the conclusion depends on the sensor positions and on the criterion". This agrees
  with Lienhard's empirical thresholds (`mL ≳ 5` for temperatures, `mL ≳ 3` for base heat flow) in pointing to
  "the finite end cannot be ignored".

## 7. Directory and naming conventions

Repository habits from Modules 4–6 (lower case with underscores, a decimal point written as `p`) plus the
evidence paths the course requires. One rule per layer:

- **Python code** lives in `Module_7/python/`: code is `<subject>.py`, tests are `test_<subject>.py`, and
  scripts that read `data/raw/` live in `analysis/<subject>_<verb>.py` (`_fit` produces fitted results,
  `_check` produces diagnostics). **No `module_07_` prefix inside the module directory** — the path already
  scopes the name, and Modules 4–6 do the same (`p_only_tec_control_gui.py`, `pi_controller.py`,
  `test_pi_control.py`, `analyze_model_baseline.py`).
- **Arduino sketches** live in `arduino/<sketch>/<sketch>.ino`: the folder name must equal the sketch name and
  must be unique across the repository, so this one keeps the module prefix.
- **Raw data** keeps the prefix and is named for its purpose, not for its clock time:
  `data/raw/module_07_rod_<role>_<programme>.csv` — `pilot_20C_30C_20C`, `pi_check_20C`,
  `interlock_trip_45C_40C`, `stationary_40C` — because raw files are quoted in reports and handed in outside
  this directory, and their rows are never edited. The GUI cannot know the purpose, so it opens the file as
  `module_07_rod_<YYYYmmdd_HHMMSS_microseconds>.csv`; that scratch name is replaced by the purpose name once the
  run is written up. When the run happened is not in the name: every row carries `host_time`, and the run table
  in `docs/module_notes/module_07_rod_instrument.md` carries the wall clock and the commanded sequence. The
  rename leaves the bytes untouched and the derived files are regenerated under the new stem, never renamed by
  hand (`data/README.md` rule 6).
- **Derived files** are `<raw file stem>_<artifact>.<ext>`: `_stationary_fit.json`, `_stationary_profile.csv`,
  `_quality.json`, `_calibration_table.csv`, `_corrected.csv`, `_fit.png`.
- **Deliverable figures** are `figures/part_<NN>_<subject>.png`; diagnostic figures sit in a named
  subdirectory (`figures/pilot_checks/`, `figures/calibration/`) using `<raw stem>_<subject>.png`.
- **Entry points** are `run_<thing>.command` at the module root, as in Modules 5 and 6 (`run_gui.command`,
  `run_pi_control.command`).
- **Documents are in English**, matching every note in `docs/module_notes/`, the Module 4/5 READMEs and
  `Module_6/python/analysis/README.md`.

```text
Module_7/
├── README.md                             this file
├── run_rod_acquisition.command           Stage 2 launcher (add --preview for a dry run)
├── arduino/
│   └── module_07_rod_controller/
│       └── module_07_rod_controller.ino  Stage 1 (copy of the Module 6 sketch)
├── python/
│   ├── rod_acquisition_gui.py            Stage 2 (copy of the Module 6 GUI)
│   ├── rod_protocol.py                   serial format and parser (Qt-free, unit-testable)
│   ├── test_rod_protocol.py              21 hardware-free tests
│   ├── test_rod_acquisition_gui.py        12 hardware-free tests (fake serial port, offscreen Qt)
│   ├── test_cross_calibration_fit.py     24 hardware-free tests (synthetic six-channel data)
│   ├── test_stationary_fin_fit.py        20 hardware-free tests (synthetic profile, refusal, portability)
│   └── analysis/
│       ├── cross_calibration_fit.py      Stage 3 cross-calibration (standard library; matplotlib for figures)
│       ├── stationary_fin_fit.py         Part 3 fit: steady criteria + finite/semi-infinite + residuals + uncertainty
│       └── pilot_run_check.py            quality check of a pilot run (not a fit)
├── data/
│   ├── raw/                              raw CSV (never overwritten)
│   ├── calibration/                      calibration table + corrected data CSV (empty: the soak was skipped)
│   ├── processed/                        fit results (Part 3: `<run>_stationary_fit.json`, `<run>_stationary_profile.csv`)
│   └── README.md                         data directory rules
├── figures/                              Parts 1–3 figures (written when the scripts run)
└── docs/
    └── README.md                         documentation index
```

Evidence files the course asks for live in `docs/module_notes/`, like the notes for Modules 1–5:

- `docs/module_notes/module_07_rod_instrument.md` — sensor map, cross-check record, geometry, baseline/step,
  run metadata, and the decision to skip the soak calibration with its quantified cost
- `docs/module_notes/module_07_stationary_fin.md` — stationary-fit method, criteria, two-layer uncertainty and
  the open items
- `docs/assessments/a4_finite_length_biot.md` — the four A4 parts

**Hardware-free tests (run all four after touching any script; no Qt window, serial port or Arduino needed)**

```bash
.venv/bin/python Module_7/python/test_rod_protocol.py             # 21: parser = firmware header
.venv/bin/python Module_7/python/test_rod_acquisition_gui.py      # 12: GUI with a fake serial port
.venv/bin/python Module_7/python/test_cross_calibration_fit.py    # 24: synthetic six-channel calibration
.venv/bin/python Module_7/python/test_stationary_fin_fit.py       # 20: steady criteria, fit recovery, portability
```

## 8. Action list (in priority order)

**P0 — today/tomorrow, independent of data (A4 needs no measurements)**

- [ ] Read Lienhard §4.5 (pp. 163–173) and follow (4.27)–(4.51) with `fin-design-derivation`
- [ ] Lienhard Problem 1.3 (A4 Part 1)
- [ ] Derive the stationary fin equation and the insulated-tip cosh solution with both boundary conditions
      (A4 Part 2)
- [ ] Problem 4.12 / Example 4.8 / Problem 4.20 plus `mL` and `ε_T(x)` for every sensor (A4 Part 3)
- [ ] `Bi⊥` with the radial conclusion, and the heat-sink / radiator question (A4 Part 4)
- [ ] Write it into `docs/assessments/a4_finite_length_biot.md`, export `A4_Lastname.pdf`, and put the commit
      hash on the first page

**P1 — in class, S16**

- [ ] Measure `d`, the overall length, `L` and the hole positions, recording their uncertainties
- [ ] Six-probe same-temperature check (≥ 60 s) — *skipped by decision; keep as a backfill item*
- [ ] Modify Stage 1 + Stage 2 and run the Stage 4 integration check
- [ ] Write the baseline and the first step data to disk

**P2 — in class, S17, and before the deadlines**

- [ ] Fix the five rod probe positions (`θ₅ ≤ θ₁/e`)
- [ ] Complete the `20 → 45 °C` step into steady state
- [ ] Run both fits (finite and semi-infinite) with residuals
- [ ] Write `module_07_rod_instrument.md` and `module_07_stationary_fin.md`
- [ ] Demonstrate C5 and submit the receipt before 11:55, citing pushed commits

**Suggested division of labour (two people):** the four A4 parts are individual work, but you can check each
other's units and boundary conditions; on site at S16/S17 one person runs the hardware and calibration while
the other runs the software and the logging, then swap and cross-check.

## 9. Reference links

- [Module 7 Part I: Thermal Transport Foundations](https://sethfraden.github.io/Phys39F26-course/labs/theory-bridge-chapter-1/)
- [Module 7 Part II: Finite And Infinite Rod Theory (fin-design-derivation)](https://sethfraden.github.io/Phys39F26-course/labs/fin-design-derivation/)
- [Module 7 Part III: Rod Instrument, Step Response, And Stationary Fin](https://sethfraden.github.io/Phys39F26-course/labs/lab-08/)
- [TEC + finite-rod simulator](https://sethfraden.github.io/Phys39F26-course/simulators/tec-rod-control/)
- [Lienhard & Lienhard, A Heat Transfer Textbook](https://sethfraden.github.io/Phys39F26-course/references/lienhard-heat-transfer-v6.pdf)

## Simulator notes (worth poking at before S16)

- The rod is split into 24–100 finite-difference cells advanced in `0.01 s` substeps; the controller updates
  every `0.1 s`.
- The end is **zero heat flux**; the driven end carries a dynamic TEC (cold face `T_c`, hot face `T_h`,
  `C_c = 12 J/K`, `C_h = 180 J/K`, `S = 0.0513 V/K`, `R = 1.861 Ω`, `K_TEC = 0.560 W/K`,
  `R_hs = 0.55 K/W`, 12 V).
- The thermistors have a 2 s first-order response; PWM is clipped at ±100 %.
- High-gain exercise: put the probe at `x = 0`, use pure P, and raise `Kp = 8 → 80 → 800` to find the
  transition "monotonic → decaying oscillation → sustained oscillation", watching whether the PWM sits at the
  limit most of the time (bang-bang).
- Fix `Kp = 800` and move the probe down the rod: the oscillation gets **slower** (the feedback uses an older,
  weaker signal).
- This oscillation comes from the two-state TEC actuator plus distributed diffusion, sensor and sampling lag —
  a one-lumped P model cannot produce it. That is the key new physics of Module 7 relative to Module 6.







