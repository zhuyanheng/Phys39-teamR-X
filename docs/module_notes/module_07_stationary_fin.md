# Module 7 stationary-fin analysis (Part 3): method, criteria, uncertainty

**Status:** the analysis script `Module_7/python/analysis/stationary_fin_fit.py` and its 20
hardware-free tests are complete and passing. **Two step runs were recorded on 2026-11-02 (20 °C and
40 °C) and neither is stationary, so there is still no steady profile and `m` is not yet determined**;
§9 records the measured shortfall and what it would take to clear it. Until then this note describes
*how the numbers are computed, what counts as acceptable, and how the error is reported*; every cell
that needs real data is marked `to fill in`. Raw-data conventions are in
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

# hardware-free tests (20)
.venv/bin/python Module_7/python/test_stationary_fin_fit.py
```

Outputs: `data/processed/<run>_stationary_fit.json` (criteria, window, per-point profile, both models,
`σ`, `ε_T`, `Bi∥`/`Bi⊥`, sensitivity table, source SHA-256),
`data/processed/<run>_stationary_profile.csv` (with both model values and residuals), and
`figures/part_03_stationary_profile.png` (profile plus both residual sets). The JSON is strict JSON
(non-finite floats are written as `null`) and its paths are relative to the repository root, so a rerun
on another machine does not depend on absolute paths.

## 8. To fill in once the real steady run exists

- [x] Attempted on 2026-11-02 with a 20 °C hold and a 40 °C hold: **the script refused both times** (exit
      code 2); the 45 °C setpoint trips the firmware interlock before it is reached. Details in §9.
- [ ] `m`, `σ_m`, `1/m`, `Θ_tip`, `Bi∥`, `Bi⊥` and the maximum of both residual sets — into the run
      metadata of `docs/module_notes/module_07_rod_instrument.md`.
- [ ] Finite vs semi-infinite: the relative shift in `m`, compared in the same sentence with `σ_m` and
      with the 5 % bias term (course requirement).
- [ ] Caliper uncertainty of the hole positions and of `L` → one sensitivity run with `--positions` /
      `--length`, stating which geometric term dominates.
- [ ] The two substitute checks of §6.
- [ ] Line-by-line comparison with the [runbook §8 prediction record](module_07_lab_day_runbook_2026-10-26.md#8-prediction-record-write-it-before-applying-heat):
      supported / not supported / cannot determine.

## 9. Measured status 2026-11-02: no stationary profile yet

Two runs were recorded and committed (field record, timings and the interlock trip:
[module_07_rod_instrument.md](module_07_rod_instrument.md#2026-11-02-10001017-a-20-c-hold-and-a-40-c-hold-and-the-45-c-interlock-trip)):

| Raw file | What it is | Script verdict |
| --- | --- | --- |
| `module_07_rod_pi_check_20C.csv` | 188 s at 20 °C, `Kp=20`, `Ki=0.1` | refuse, exit 2: record only 239.4 s, `tec_C` at 0.934 °C/min |
| `module_07_rod_interlock_trip_45C_40C.csv` | 294 s at 20 °C, 45 °C step → interlock trip, then 389 s at 40 °C | refuse, exit 2 (defaults **and** `--hold 300`) |

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
2. Record **≈ 30 min** without touching anything, then stop; the criteria are applied to the trailing window, so
   a longer record never hurts.
3. Measure the room temperature far from the apparatus with a separate thermometer and pass it as `--ambient`;
   a fitted `T∞` is a fallback, and §9 above shows how much drift it can hide.


