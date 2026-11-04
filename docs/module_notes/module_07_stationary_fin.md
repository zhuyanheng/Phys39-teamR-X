# Module 7 stationary-fin analysis (Part 3): method, criteria, uncertainty

**Status:** the analysis script `Module_7/python/analysis/stationary_fin_fit.py` (22 hardware-free tests) and its
diagnostic companion `Module_7/python/analysis/stationary_diagnostics.py` (11) both pass. **Three runs were
recorded on 2026-11-02 — 20 °C, 40 °C, and a 31-minute 40 °C hold — and the longest one still misses the
pre-registered steady-state criterion, so Part 3 has no certified `m`.** §9 records the measured shortfall and
what it would take to clear it; §10 reports what the drifting 31-minute record *does* support: a trailing-window
diagnostic fit `m = 4.83 ± 0.07 1/m` together with the four systematics a drifting record puts on it, both
committed as `data/processed/<run>_stationary_fit.json` and `<run>_stationary_diagnostics.json`. Neither file is
the Part 3 result and neither may be quoted without saying so. The rest of this note describes *how the numbers
are computed, what counts as acceptable, and how the error is reported*; every cell that still needs a steady
profile is marked `to fill in`. Raw-data conventions are in
[Module_7/data/README.md](../../Module_7/data/README.md); geometry, hole positions and run metadata are
in [module_07_rod_instrument.md](module_07_rod_instrument.md).

## 1. What this analysis has to answer

| Output | Symbol | Unit | Used for |
| --- | --- | --- | --- |
| Decay constant | `m` | 1/m | Main Part 3 result; feeds `(mR/2)²` in Part 4 |
| Decay length | `1/m` | m | Compared with `L` and the hole spacing: finite or semi-infinite? |
| Tip remainder | `Θ_tip = 1/cosh(mL)` | — | Is the finite end visible? (course threshold `Θ_tip > 0.1`) |
| Finite-rod Biot number | `Bi∥ = (mL)²` | — | Part 4: the cross-check for `(mR/2)²` |
| Transverse Biot number | `Bi⊥ = (mR/2)²` | — | Part 4: does the one-dimensional radial approximation hold? |
| Semi-infinite error | `ε_T(x) = abs(Θ_fin − Θ_inf) / Θ_fin` | — | Part 3: how far out can the exponential be used? |

Three things are fixed before the run and cannot be adjusted afterwards: **the boundary condition
uses the measured rod 1** (not the TEC setpoint, not the measured TEC), **`T∞` is the measured room
temperature far from the apparatus** (the fit only takes over when that was not recorded), and **the
steady window is selected by the criteria written down in §2**.

## 2. Criteria first: what "steady" means

The script implements two conditions that must hold **simultaneously** (`steady_window()`):

1. whole-window least-squares slope `|dT/dt| ≤ 0.02 °C/min`, for all six channels `tec_C` and
   `rod1_C … rod5_C`;
2. the difference between the mean of the first third and the mean of the last third of the window
   is `≤ 0.10 °C`, channel by channel (`--drift-budget`).

**Why condition 2 is needed:** if the window opens inside a still-converging transient, the
whole-window slope averages "steep at the start, flat at the end" to something that looks acceptable,
while the window mean is pulled off — and the profile uses one mean per probe, so that bias never
enters `σ`. `test_the_drift_budget_rejects_a_window_that_opens_inside_a_transient` builds exactly this
data: the slope condition passes, the drift condition does not.

The window is the **longest qualifying trailing segment**, at least `--hold 600 s` (Arduino seconds)
long. If there is none the run is refused and **nothing is written**:

| Exit code | Meaning |
| --- | --- |
| 0 | Fit complete; JSON, CSV and figure all written |
| 2 | Criteria not met (nothing written; the closest window is reported with the channel, the °C/min and the °C by which it misses) |
| 3 | Otherwise unusable (too few rows, raw file changed during the analysis, ...) |
| 4 | Illegal geometry (`--positions` not five values, first value not 0, a position beyond `--length`) |

**The limits can be relaxed for a diagnosis, and the script says so.** `--slope-limit` / `--drift-budget`
exist so that a record that misses the criterion can still be looked at, but any run made with non-default
limits writes `criterion.relaxed: true` into the JSON, prints `*** CRITERION RELAXED` above the numbers, and
stamps `CRITERION RELAXED: this record is not a certified steady profile` into the figure title. A relaxed fit
is a **diagnostic**, and §10 is the only place where one is quoted.

A hole in the data (`nan`, a malformed row) does not split the run into two separate fits; it
invalidates every window that crosses it. The analysis also truncates at the **last row where all six
channels are valid** (`rows_used` and `measurement_rows` are both reported in the JSON), so unplugging
a probe *after* the soak is tolerated while losing one *during* the soak is refused.

## 3. Two models, one free parameter (one exception: fitting `T∞`)

- **Finite (main result):** `Θ = cosh[m(L − x)] / cosh(mL)`. The amplitude is fixed by the measured
  `θ₀ = T_rod1 − T∞` at `x = 0`, so only `m` is fitted (`dof = N − 1 = 4`). This matches the
  experimental boundary condition: the base temperature is *measured*, not an ideal heat source.
- **Semi-infinite (control):** `Θ = e^(−mx)`, an ordinary least-squares line through the origin on
  `ln(θ/θ₀)` vs `x` — closed form, no iteration. Its residual scale is logarithmic, so only its
  **temperature-residual column** is compared with the finite model, never the SSR value itself.
- **Fitting `T∞` (only when the room temperature was not recorded):** two parameters `(m, T∞)`,
  `dof = 3`, solved by **profile likelihood** (re-optimising `m` for each trial `T∞`) rather than by
  alternating relaxation — the two parameters are strongly correlated (raising `T∞` shrinks `θ₀` and
  demands a smaller `m`), so alternating relaxation stalls in the valley between them. On this path
  `sigma_m_per_m` is always **`null`**: five points for two parameters do not give a trustworthy error
  bar, and the fitted `T∞` must **never** be quoted as a measured room temperature.

**Why `k` and `h` cannot both be determined:** a steady profile only gives
`m² = hP/(kA) = 2h/(kR)` — one number, two unknowns. Either `h` is measured separately (independent
convection experiment or a literature order of magnitude), or aluminium's `k` is assumed and `h` is
inverted, `h = m²kR/2`. Example: with `k = 167 W/(m·K)`, `R = 6.35 mm` and a fitted `m = 3.63 1/m`,
`h ≈ 7.0 W/(m²·K)`, consistent with the literature order of magnitude — but that is an **inference
made after assuming `k`**, not two independent measurements. The report has to say it that way.

## 4. Two uncertainty layers, reported separately

1. **Statistical term `σ_m`:** from the curvature of `SSR(m)` at its minimum,
   `σ = sqrt(2·SSR/dof / (d²SSR/dm²))`, with `dof = N − 1` (N = 5). It only says how consistent these
   five points are; it contains **no sensor error at all**.
2. **Uncalibrated-bias term** (because the soak cross-calibration was skipped, see
   [rod_instrument §decision](module_07_rod_instrument.md)): `probe_offset_sensitivity` raises one
   probe at a time by `--sensitivity-offset` (default 0.5 °C) and re-fits `m`. The table below is
   computed at the expected operating point `m = 3.63 1/m`, `θ₀ = 20 °C` (45 °C setpoint ⇒ rod1 ≈
   41 °C at a ≈ 21 °C room):

| Probe raised | `x` (m) | Δm/m |
| --- | ---: | ---: |
| rod1 (`x = 0`, also sets `θ₀`) | 0.0000 | **+5.1 %** |
| rod2 | 0.0385 | −0.8 % |
| rod3 | 0.0895 | −1.6 % |
| rod4 | 0.1405 | −2.1 % |
| rod5 | 0.1915 | −2.4 % |

Reporting convention: `m = <value> ± <σ_m> (statistical) ± 5 % (uncalibrated bias, dominant)`, with
the statement that the bias term comes from the six probes agreeing at 20 °C (0.48 °C worst case) and
not from a span calibration, and that it is **not** reduced by more data points or a better fitting
algorithm.

## 5. Predictions from the measured geometry

`L = 0.2715 m`, hole positions `x = 0, 3.85, 8.95, 14.05, 19.15 cm`, `d = 12.7 mm` (nominal),
`k = 167 W/(m·K)`:

| `h` (W/m²K) | `m` (1/m) | `1/m` (m) | `mL` | `Θ_tip` | `Bi∥` | `Bi⊥` |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 3.07 | 0.326 | 0.834 | 0.731 | 0.70 | 9.5×10⁻⁵ |
| 7 | 3.63 | 0.275 | 0.986 | 0.655 | 0.97 | 1.3×10⁻⁴ |
| 10 | 4.34 | 0.230 | 1.178 | 0.562 | 1.39 | 1.9×10⁻⁴ |

Error of the semi-infinite approximation at the **measured hole positions** (`m = 3.63 1/m`):

| Hole | `x` (m) | `ε_T` |
| --- | ---: | ---: |
| rod1 | 0.0000 | 0 % |
| rod2 | 0.0385 | 3.8 % |
| rod3 | 0.0895 | 10.1 % |
| rod4 | 0.1405 | 17.8 % |
| rod5 | 0.1915 | 26.9 % |

Conclusion, written down before the measurement and to be checked against the real data: `mL ≈ 1`, so
the tip still carries 65 % of the base excess, and **the semi-infinite approximation exceeds 5 % from
`x ≳ 4 cm`**. Part 3 therefore has to keep the finite cosh solution, and `m` has to come from the
finite fit; the semi-infinite fit is only the "what happens if you ignore the end" control.
`Bi⊥ ~ 10⁻⁴ ≪ 1`, so the one-dimensional radial approximation holds. These tables are produced by the
script's own functions (`1/cosh(mL)`, `(mL)²`, `(mR/2)²`, `epsilon_table()`), not by hand.

## 6. Two substitute checks that remain possible without the soak calibration

2026-11-04 clarification: these are optional robustness checks. The current
course uses raw readings after a common-temperature spread below 1 C and does
not require a second stationary setpoint. The instructor-authorized raw-data
route is retained. Differences between profiles at two temperatures would not
uniquely diagnose sensor gain: changing heat loss or contact can also contribute.

1. **Re-fit with a different reference probe.** Treat rod2 as `x = 0` (shifting the other positions by
   the relative distances) and fit the same window again. If the two `m` agree within 5 %, the
   per-probe bias is not concentrated on the base probe; this is a *relative*-bias test and needs no
   soak.
2. **Shape comparison at two temperatures.** Normalise the 45 °C and 35 °C steady profiles to
   `θ(x)/θ(0)`: the same `m` must give the same dimensionless curve. If the shape changes with
   temperature there is a gain error (`b_i ≠ 1`) — this is the replacement for a span check, costing one
   extra steady point and no rewiring.

Neither has been done yet (both need the real steady run). When writing the report, state explicitly:
**same-temperature consistency was verified, span linearity was not.**

## 7. Reproducing

```bash
# fit (reads the default raw path, writes data/processed/ and figures/)
.venv/bin/python Module_7/python/analysis/stationary_fin_fit.py \
    Module_7/data/raw/<run>.csv --ambient <measured room temperature, °C>

# the same fit with relaxed limits = a diagnostic of a drifting record, flagged as such
.venv/bin/python Module_7/python/analysis/stationary_fin_fit.py \
    Module_7/data/raw/module_07_rod_stationary_40C.csv --ambient 23.95 \
    --slope-limit 0.06 --drift-budget 0.4

# systematics of that diagnostic fit (§10): window slide, extrapolation, ambient, geometry, origin swap
.venv/bin/python Module_7/python/analysis/stationary_diagnostics.py \
    Module_7/data/raw/module_07_rod_stationary_40C.csv --ambient 23.95

# hardware-free tests (22 + 11) and the two Part 1/Part 2 figures
.venv/bin/python Module_7/python/test_stationary_fin_fit.py
.venv/bin/python Module_7/python/test_stationary_diagnostics.py
.venv/bin/python Module_7/python/analysis/sensor_map_figure.py --out Module_7/figures/part_01_sensor_map.png
.venv/bin/python Module_7/python/analysis/step_response_figure.py
```

Outputs: `data/processed/<run>_stationary_fit.json` (criteria, window, per-point profile, both models,
`σ`, `ε_T`, `Bi∥`/`Bi⊥`, sensitivity table, source SHA-256),
`data/processed/<run>_stationary_profile.csv` (with both model values and residuals),
`data/processed/<run>_stationary_diagnostics.json` (the five systematics of §10, with
`worst_change_percent`), and `figures/part_03_stationary_profile.png` (profile plus both residual sets).
Both JSONs are strict JSON (non-finite floats are written as `null`), carry the source SHA-256 and a
`raw_unchanged` flag, and their paths are relative to the repository root, so a rerun on another machine does
not depend on absolute paths.

## 8. To fill in once the real steady run exists

- [x] Attempted on 2026-11-02 with a 20 °C hold, a 40 °C hold and a 31-minute 40 °C hold: **the script refused
      all three** (exit code 2); the 45 °C setpoint trips the firmware interlock before it is reached. Details in
      §9, the diagnostic fit that the longest record still supports in §10.
- [x] `m`, `σ_m`, `1/m`, `Θ_tip`, `Bi∥`, `Bi⊥`, `h` inversion and the maximum of both residual sets — computed
      **for the diagnostic window only** (§10.1); they go into the run metadata of
      `docs/module_notes/module_07_rod_instrument.md` once a steady run exists.
- [x] Finite vs semi-infinite: `m` shifts by 29.5 % (14 `σ_m`), which is far outside both the statistical and the
      5 % bias term — the finite cosh has to be kept (§10.1).
- [x] ±1 mm in `L`, in all `x` and in the tip probe alone: worst change ±0.4 %, so the ruler geometry is not what
      limits this fit (§10.2). The *caliper* uncertainty is still unmeasured.
- [x] §6 check 1 (rod2 as the origin): `m = 4.57 1/m`, −4.9 % from the rod1-origin fit (§10.2).
- [ ] §6 check 2 (shape at a second temperature): needs a second steady point, so it is blocked with the rest.
- [ ] Line-by-line comparison with the [runbook §8 prediction record](module_07_lab_day_runbook_2026-10-26.md#8-prediction-record-write-it-before-applying-heat):
      supported / not supported / cannot determine. §10.1 already answers the two predictions that only need the
      *shape* (`mL ≈ 1`: `Θ_tip = 0.50`; `ε_T > 5 %` from `x ≈ 9 cm`), but the profiled `m` itself stays open.

## 9. Measured status 2026-11-02: no stationary profile yet

Three runs were recorded and committed (field record, timings and the interlock trip:
[module_07_rod_instrument.md](module_07_rod_instrument.md#2026-11-02-10001017-a-20-c-hold-and-a-40-c-hold-and-the-45-c-interlock-trip)):

| Raw file | What it is | Script verdict |
| --- | --- | --- |
| `module_07_rod_pi_check_20C.csv` | 188 s at 20 °C, `Kp=20`, `Ki=0.1` | refuse, exit 2: record only 239.4 s, `tec_C` at 0.934 °C/min |
| `module_07_rod_interlock_trip_45C_40C.csv` | 294 s at 20 °C, 45 °C step → interlock trip, then 389 s at 40 °C | refuse, exit 2 (defaults **and** `--hold 300`) |
| `module_07_rod_stationary_40C.csv` | 31 min at 40 °C, `Kp=100`, `Ki=0.3` — the run the shortfall note asked for | refuse, exit 2: `rod5_C` at **0.052 °C/min** (2.6 × the limit) and **0.340 °C** third-to-third drift (3.4 × the budget) |

The third run is the honest test of the §9 planning estimate: 31 min of holding, three times the 10 min that
the 300 s record had made look plausible, and the far probe is *still* creeping. It is also what makes §10
possible at all, because its trailing window is long enough to be worth diagnosing.

The second verdict at `--hold 300` is the informative one, because 300 s is what the operator judged
sufficient: over the trailing 300 s of the 40 °C hold, `rod4_C` still moves at **0.741 °C/min** (37 × the
0.02 °C/min limit) and the first/last-third means differ by **2.466 °C** (25 × the 0.1 °C budget). The base
probe, by contrast, is settled (`tec_C` at 0.029 °C/min, 0.11 °C below setpoint) — so the criteria fail on the
rod, not on the controller. `rod5_C` at `x = 19.15 cm` is still moving at 0.57 °C/min when the record ends (it
peaked at 0.85 °C/min about 3 min into the hold); see the block-slope decay table in the field record, which puts
the needed hold at **≈ 30 min**, not 5.

### Why a "snapshot fit" is not a substitute

Fitting the trailing part of the 40 °C hold anyway (`analyse()` on rows truncated to the last *L* seconds,
`ambient=None`, criterion relaxed to 5 °C/min with the drift budget off, nothing written to disk) gives:

| Window | `m` (finite) | rms | `T∞` fitted |
| --- | ---: | ---: | ---: |
| last 60 s | 5.347 1/m | 0.114 °C | 19.40 °C |
| last 120 s | 5.377 1/m | 0.114 °C | 19.09 °C |
| last 240 s | 5.620 1/m | 0.114 °C | 18.85 °C |
| whole 389 s hold (mean) | 7.864 1/m | 0.103 °C | 21.53 °C |

The cosh shape does describe a single snapshot (rms 0.11 °C), but the fitted `T∞` lands 2.5–3 °C below the
21.9–22.0 °C that the probes read at rest, i.e. the fit is partly absorbing the ongoing drift into the offset,
and `m` moves by **46 %** between the 240 s snapshot and the segment mean. That spread is the bias, and it is
far larger than any `σ_m` the fit could quote. **`m` therefore stays `to fill in`; 5.4 1/m is not a result and
must not be quoted as one.**

### The 20 °C runs cannot be fitted even in principle

With the base at 20.5–21.5 °C and the room at ≈ 22 °C, `θ = T − T∞ < 0` along the whole rod, and the script
refuses a negative-`θ` profile on purpose (`status: unusable-profile`). A cooling profile is the same equation
with the sign flipped, but that is not implemented; for Part 3 the profile must be taken at a **heated**
setpoint.

### What would clear it

1. Setpoint **40 °C** (43 °C at most; 45 °C is impossible, see the field record), PI `Kp = 100`, `Ki = 0.3`.
2. Record **≈ 45 min** without touching anything, then stop; the criteria are applied to the trailing window, so
   a longer record never hurts. How long is enough is now measured, not guessed: the 31-minute record still had
   `rod5_C` at 0.052 °C/min and 0.340 °C drift, and the probe's fitted time constant is `τ = 591 s` (§10.2), so
   the slope has to fall by 2.6× (`τ·ln 2.6 ≈ 9.4 min`) and the drift by 3.4× (`τ·ln 3.4 ≈ 12 min`). **≈ 15 more
   minutes of holding** on top of the 31 already recorded would clear both; nothing else about the run changes.
3. Measure the room temperature far from the apparatus with a separate thermometer and pass it as `--ambient`;
   a fitted `T∞` is a fallback, and §9 above shows how much drift it can hide.

   **Status of this one:** item 1 was done and item 2 was done (31 min); item 3 was **not** — no separate
   thermometer was placed, and the `--ambient` value used in §10 is the probes' own pre-heat reading (§10.0).

## 10. What the 31-minute record does support: a diagnostic fit with its systematics

The `module_07_rod_stationary_40C.csv` record (31 min, `Kp = 100`, `Ki = 0.3`) misses the pre-registered
criterion and is therefore **not** a stationary profile. Its trailing window does describe the cosh shape well
(rms 0.127 °C on five points, `dof = 4`), and that shape is worth quantifying so that the report can say what
the rod looks like *if it is fitted anyway* — provided every number carries the diagnosis with it. Nothing in
this section is the Part 3 result.

Two committed artefacts, both regenerated from that raw file (SHA-256 `70aaaec4…`, re-checked inside both
scripts: `raw_unchanged: true`):

| File | What it holds |
| --- | --- |
| `data/processed/module_07_rod_stationary_40C_stationary_fit.json` (+ `_stationary_profile.csv`, `figures/part_03_stationary_profile.png`) | the fit on the **674 s window** (1175–1849 s) that the relaxed limits (0.06 °C/min, 0.40 °C) accept, with `criterion.relaxed: true` |
| `data/processed/module_07_rod_stationary_40C_stationary_diagnostics.json` | the same fit on the **trailing 600 s** (1249–1849 s) plus the five systematics below, summarised in `worst_change_percent` |

### 10.0 Where `T∞ = 23.95 °C` comes from

It is the six-channel mean of the 36 measurement rows recorded **before the heater was enabled** (Arduino
`time_s` 0.55–18.56 s; the `start` event is at 11:14:02): 23.962, 24.005, 23.801, 24.044, 24.067, 23.836 °C →
**23.9527 °C**. This is the probes' *own* isothermal reading, not an independent thermometer — the separate
room thermometer that item 3 above asks for was never placed, so the value is a **self-ambient**, and its cost
is the `ambient` row of §10.2. It is reproducible from the raw file alone:

```bash
.venv/bin/python -c "import csv;r=[x for x in csv.DictReader(open('Module_7/data/raw/module_07_rod_stationary_40C.csv')) if x['event']=='measurement' and float(x['time_s'])<=19];k=['tec_C','rod1_C','rod2_C','rod3_C','rod4_C','rod5_C'];print(round(sum(sum(float(x[j]) for x in r)/len(r) for j in k)/6,4))"
```

Feeding the fitted value instead (`T∞` free) is possible but forbidden as a result: see the `ambient` bullet of
§10.2.

### 10.1 The number, with every qualifier

| Quantity | Value | Note |
| --- | ---: | --- |
| `m` (finite cosh, window 1175–1849 s) | **4.826 ± 0.068 1/m** | `σ_m` from the SSR curvature, `dof = 4` |
| `1/m` | 0.207 m | 76 % of `L = 0.2715 m` |
| `Θ_tip = 1/cosh(mL)`, `mL = 1.310` | 0.503 | far above the 0.1 threshold: the end is not negligible |
| `θ₀ = T_rod1 − T∞` | 12.21 °C | measured, not fitted |
| rms of the finite fit | 0.127 °C | five points, four dof |
| `Bi∥ = (mL)²` | 1.72 | Part 4 cross-check for `(mR/2)²` |
| `Bi⊥ = (mR/2)²` | 2.35 × 10⁻⁴ | the 1-D radial approximation holds |
| semi-infinite control `m` | 3.401 1/m | rms 0.280 °C; **29.5 % below** the finite fit = 14 `σ_m` |
| `h = m²kR/2` with `k = 167 W/(m·K)` | 12.3 W/(m²·K) | assumes `k` (§3); slightly above the 5–10 W/(m²·K) prior |
| `ε_T` at rods 2–5 | 3.0 / 8.5 / 16.3 / 26.6 % | the 5 % criterion is broken from `x = 8.95 cm` |

The finite/semi-infinite gap (29.5 %) reproduces the §5 prediction (`mL ≈ 1`, so the tip matters) far outside
both uncertainty layers — the course requirement "compare the model shift with `σ_m` and with the bias term" is
answered as 29.5 % ≫ 1.4 % (`σ_m/m`) and ≫ 5 % (bias). The inverted `h = 12.3 W/(m²·K)` sits a little above the
natural-convection prior; part of that is the still-rising far probes (§10.2), part would be an effective `k`
below 167 W/(m·K).

### 10.2 The five systematics a drifting record puts on that number

From `..._stationary_diagnostics.json`, all in per cent of the trailing-600 s base `m = 4.804 1/m` — the fit
above uses 674 s and gives 4.826, i.e. −0.4 % for the longer window:

| Term | What was varied | Range of `m` | Worst change |
| --- | --- | ---: | ---: |
| `window_slide` | 600 s windows walked back from the record end in 13 steps of 100 s | 7.749 … 4.804 1/m | **+61 %** (window 49–649 s) |
| `extrapolation` | each probe's exponential approach (`τ = 591–739 s`, rms 0.035–0.068 °C) extrapolated to its own asymptote, then the profile fitted | 4.580 1/m | **−4.7 %** |
| `ambient` | `T∞ = 23.95 ± 0.25 / ± 0.5 / ± 1.0 °C` | 4.51 … 5.17 1/m | **+7.6 %** (+1.0 °C) |
| `geometry` | ±1 mm in `L`, in all `x`, and in the tip probe alone | 4.785 … 4.824 1/m | **±0.4 %** |
| `origin_swap` (§6 check 1) | rod2 as the origin, four probes, `L` shortened to 0.233 m | 4.571 1/m | **−4.9 %** |

How to read it:

- **`window_slide` dominates, and it is not an uncertainty bar** — it is the drift made visible. Every 600 s
  window of the hold is fitted by the same cosh with almost the same rms (0.114–0.128 °C), so a small residual
  says nothing about steadiness; only the criterion does. Inside the last 900 s `m` still falls by ≈ 1 % per
  100 s step (4.860 → 4.804 1/m). A single quoted value therefore inherits a spread of tens of per cent from the
  choice of window alone.
- **`extrapolation` (−4.7 %) points the same way as the drift**: waited out to each probe's own asymptote the
  profile is slightly flatter, `m = 4.58 1/m`. The fitted time constants (591–739 s) also explain why the
  operator's 300 s was hopeless: the slowest probe drops its slope by `e` every `τ`, so 300 s is only 0.5 `τ`,
  and the 31-minute hold (3.1 `τ`) still misses the 0.02 °C/min limit by 2.6×. Resolving it needs `ln 2.6 = 0.96 τ`
  more (≈ 9 min), and the drift limit `ln 3.4 = 1.22 τ` more (≈ 12 min) — the ≈ 15 min of extra holding in §9.
- **`ambient` is the largest genuinely epistemic term** (+7.6 % per +1 °C). It is large because five points with
  `mL ≈ 1.3` cannot separate `θ₀` from `m`: raising `T∞` shrinks `θ₀` and the whole profile with it. §3 forbids
  fitting `T∞` for this reason, and doing it anyway on this record returns `T∞ = 26.98 °C` — 3 °C above the
  probes' own rest reading — with `m = 6.29 1/m` (+30 %). The free fit spends its freedom on the drift, which is
  why `stationary_diagnostics.py` makes `--ambient` **required** rather than optional.
- **`geometry` is negligible** at the ruler's resolution (±1 mm ⇒ ±0.4 %), so the caliper item in §8 is not what
  limits this fit.
- **`origin_swap` (−4.9 %) passes the 5 % test of §6**: moving the origin from rod1 to rod2 shifts `m` about as
  much as the extrapolation term and far less than the window slide, so no single probe carries a pathological
  bias. It is a *relative* check; span linearity remains unverified because the soak was skipped.

### 10.3 How to quote it in the report

> The 31-minute 40 °C record does not reach steady state (worst channel `rod5_C`: 0.052 °C/min against a
> pre-registered 0.02 °C/min, and 0.34 °C third-to-third drift against a 0.10 °C budget), so no certified decay
> constant exists. A diagnostic fit to its trailing window gives `m = 4.83 ± 0.07 (statistical) 1/m`; the
> record's own drift moves that number by −4.7 % (extrapolation to each probe's asymptote) and spans 60 % across
> the hold, a ±1 °C error in the self-read ambient moves it by +7.6 %, the choice of origin by −4.9 %, and
> ±1 mm of geometry by ±0.4 %, on top of the ±5 % uncalibrated-probe bias of §4. The systematic spread, not
> `σ_m`, is the honest error bar.

`m` itself stays `to fill in` in the Part 3 table, and the figure that carries these numbers
(`figures/part_03_stationary_profile.png`) says `CRITERION RELAXED` in its title so that it cannot be mistaken
for a steady profile.




## 11. Nov. 4 selected final interval

At the operator request, the final 600.29 s of the completed Nov. 4 40 C run
are analyzed as a stationary approximation. Full provenance and numbers are
in the final section of the field record and in
`Module_7/data/processed/module_07_rod_20261104_095908_593628_selected_stationary.json`.
The original gate still fails (0.02671 C/min, 0.1853 C); m=6.7844 /m is
conditional on jointly fitted T_inf=29.9759 C, not independent room thermometry.
This is the user-selected analysis result; the earlier Nov. 2 relaxed diagnostic
remains historical evidence and is not overwritten. Neither is labelled as
passing the preregistered gate. A4 remains a separate literature/h=10 prediction.
