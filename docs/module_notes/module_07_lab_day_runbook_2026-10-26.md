# Module 7 lab-day runbook (S16 2026-10-26 → S17 2026-10-28)

**Work in dependency order, not in clock order.** Step 1 is the only step that holds up everything
else: without the six-channel acquisition chain there is no `T(x, t)` in class time, and C5 has nothing
to demonstrate. Plan and formula summary: [Module 7 README](../../Module_7/README.md). A4 scaffold:
[a4_finite_length_biot.md](../assessments/a4_finite_length_biot.md).

> **Stop condition (safety):** if the temperature moves in the wrong direction, approaches the 10 °C /
> 45 °C boundaries of the course working range (this round runs 20–45 °C, and a steady-state trial must
> not exceed 55 °C), if the display or serial stream freezes, the supply current rises unexpectedly, or
> the TEC / H-bridge / heat exchanger becomes unusually hot or smells abnormal: enter `0` in the GUI,
> verify the firmware reports `0/0`, switch off actuator power and tell the instructor. If the GUI or the
> serial link fails, cut actuator power directly instead of waiting for the software. Never leave a
> powered run unattended and do not touch live terminals or hot parts.

## 0. Why this order

| Step | Depends on | Blocks | Can it be done after class? |
|---|---|---|---|
| 1 six-channel measurement chain | code only (works with the TEC unpowered) | calibration, step, all of C5 | yes, but it wastes class time |
| 2 geometry + sensor map | caliper / ruler | A4 Part 3/4, `mL`, `ε_T` | yes, but C5 needs it demonstrated live |
| 3 cross-calibration | six-channel chain + warm water | validity of the profile gradient | **no** — skipped by decision: installed spread < 1 °C, cost ≈ 5 % in `m`; see the decision box in §3 |
| 4 step response | calibration + chosen positions | the Part 3 steady profile, C5 | **no** (needs a full-rod 20 °C initial state) |
| 5 A4 Part 2 derivation | textbook only | 6/10 of A4 | yes, but the deadline is 10/28 09:05 |
| 6 A4 Part 3/4 + position choice | steps 2 and 4 | 5/10 of A4 | yes, after class |

**In one sentence:** spend 2–3 hours getting the software working (step 1), use class time for the
calibration and the step that expire immediately (steps 3 and 4), and run the derivation-heavy work
(steps 5 and 6) in parallel in the evening.

## 1. First: the six-channel measurement chain (verifiable with the TEC unpowered)

> **On-site procedure:** [module_07_step1_integration_check.md](module_07_step1_integration_check.md) —
> wiring, expected divider voltages, upload command, per-channel fingerprint table, fault injection,
> troubleshooting table. This section is only the summary checklist.

- [ ] Inventory the probes: **6** usable thermistors, at least 5 of which fit into rod holes and one that
      can be fixed to the TEC base. If not, solder leads and insulate with heat-shrink first; fix the
      labels `TEC`, `1`–`5` and leave them on until the end of term.
- [x] Copy rather than modify Module 6 (done 2026-10-26): `Module_6/arduino/p_only_tec/p_only_tec.ino` →
      `Module_7/arduino/module_07_rod_controller/module_07_rod_controller.ino`;
      `Module_6/python/pi_tec_control_gui.py` → `Module_7/python/rod_acquisition_gui.py`. **Both Module 6
      files stay untouched** and act as the working checkpoint.
- [x] Channel mapping: `A0` = TEC base, `A1`–`A5` = rod 1–5. `A0` remains the only source for the PI
      feedback and the software temperature limit; the five rod channels only measure and never enter the
      control law.
- [x] Sampling budget: TEC 1000 readings per cycle (as in Module 6), rod channels 100 per cycle (one
      `analogRead` ≈ 112 µs, full scan ≈ 168 ms < 500 ms cycle).
- [x] Serial record format (at startup the firmware prints `#firmware`/`#channels`/`#pins`/`#DATA,...`
      headers, then one `DATA` line per cycle; every other line starts with `#`):

```text
#DATA,time_s,tec_C,rod1_C,rod2_C,rod3_C,rod4_C,rod5_C,pwm,heat_cool,heat_pwm,cool_pwm,limit_C,safety,rod_ok
DATA,12.50,23.41,23.38,23.36,23.34,23.31,23.29,120,1,120,0,60.00,OK,5
```

- [x] The Python side parses complete `DATA` lines only (`Module_7/python/rod_protocol.py`); malformed
      lines, headers and replies are skipped without crashing; the window shows `rows ok/bad` counters;
      the six traces keep fixed colours and the TEC trace is bolder.
- [x] CSV measurement columns share the `DATA` names and order, hold the **raw readings** and no corrected
      values; the file name carries a timestamp, is opened in `'x'` mode so it is never overwritten, and
      flushed after every row.
- [x] Static verification: `arduino-cli compile --fqbn arduino:avr:uno` passes (7844 B flash / 545 B RAM);
      `python3 Module_7/python/test_rod_protocol.py` passes all 21 tests, including the cross-check that
      the parser field names equal the firmware header.
- [ ] Integration check with the TEC unpowered: heat one probe at a time with a fingertip and confirm that
      **only** its Arduino column and its Python trace change; confirm that one `DATA` line equals one set
      of displayed values equals one CSV row; confirm that PWM starts at 0 after power-up and responds to
      a zero-power command; unplug one rod probe and confirm that only its column becomes `nan`, that
      `rod_ok` drops, and that the TEC safety shutdown still works.
- [ ] Close the Serial Monitor after testing, **before** opening the Python GUI (only one program can own
      the port).
- [ ] Commit at this point and note the hash: the C5 receipt must cite pushed acquisition code and
      evidence commits.

## 2. Next: geometry and the sensor map (about 15 min, no power needed)

- [ ] Record the material as 6061-T6 aluminium; measure the diameter `d`, the overall physical length,
      and the analysis length `L` **from the first thermistor hole to the rod tip**, each with its
      uncertainty. The nominal `d = 12.7 mm` must be measured.
- [ ] Compute `A = πR²`, `P = πd`, `A/P = R/2` in SI units and write them into the record.
- [ ] Fit rod 1 into the first chosen hole and define that hole as `x = 0` (it is **not** the physical end
      of the rod and **not** the thermistor inside the TEC); measure the other 4 positions and the tip
      `x = L`, recording the uncertainty of each.
- [ ] Draw or photograph one figure: permanent labels, Arduino channels, positive coordinate direction,
      measured positions. Save as `Module_7/figures/part_01_sensor_map.png`.
- [ ] First prediction: with the measured `d`, `L`, `h = 5–10 W/(m²·K)` and `k ≈ 167 W/(m·K)`, update `m`,
      `1/m`, `mL`, `Θ_tip`, `Bi⊥` and the per-sensor `ε_T(x)` and write them into the prediction record in
      [§8](#8-prediction-record-write-it-before-applying-heat).

## 3. In class, S16: cross-calibration (one-shot, expires immediately)

> **Decided: skipped** (the reasoning and the cost are in
> [module_07_rod_instrument.md](module_07_rod_instrument.md), section "Decision: skip the six-probe soak
> cross-calibration").
> Reason: with the probes installed the six channels already agree within 1 °C (0.48 °C worst case across
> the 20 °C baseline), and the probes are already fitted in the TEC base and the rod holes, so a soak would
> mean dismantling and re-installing them.
> The cost is quantified: 0.5 °C of offset on any probe moves `m` by **5.1 %** (the base probe rod1 is the
> most sensitive), so the reported `m` must carry an "uncalibrated offset ≈ 5 %" term.
> The rest of this section stays as a **backfill checklist**: come back to it if a probe is removed and
> re-fitted, or if the profile fit leaves residuals that cannot be explained.

It had to be done **before** the probes were permanently fitted into the TEC base and the rod, otherwise
the six probes can never be at the same temperature.

- [ ] With the wiring and sampling rate of step 1, put all six probes into a Styrofoam cup of warm water
      covering roughly `20 °C < T < 60 °C`; immerse only the waterproof ends, keep the connectors dry, and
      keep the probes off the cup walls and floor.
- [ ] Stir gently and continuously so that all six probes follow **the same** cooling curve; record all
      channels for ≥ 60 s.
- [ ] Using `tec_C` as the reference, fit `T_TEC = a_i + b_i T_i` channel by channel; plot `T_i` vs `T_TEC`
      with the identity line and the fitted line.
- [ ] Plot the corrected residual `(a_i + b_i T_i) − T_TEC` vs `T_TEC`; **write the criterion before
      evaluating it**. The starting criterion is a corrected mean offset < 0.2 °C with no residual trend
      larger than 0.2 °C over the span. If the noise levels differ clearly, rewrite the criterion and say
      why.
- [ ] Save the calibration table (channel, `a_i`, `b_i`, number of points, temperature range, residual
      mean/standard deviation/maximum magnitude) into `Module_7/data/calibration/`; leave the raw CSV
      untouched.
- [ ] Conclusion: are the channel differences smaller than the measured temperature difference along the
      rod? If not, fix the hardware or the wiring before starting the profile measurement.

## 4. Later in S16: baseline + the `20 → 45 °C` step (the longest item, start it early)

> **Read this before starting a 45 °C trial.** On 2026-11-02 a `45 °C` setpoint tripped the firmware safety
> interlock at a TEC reading of `45.22 °C` (allowed window 10–45 °C), so a 45 °C steady state cannot be produced
> at all. Use **40 °C** (43 °C at most), and budget **≈ 30 min of hold**, not 300 s: see the
> [2026-11-02 field record](module_07_rod_instrument.md#2026-11-02-10001017-a-20-c-hold-and-a-40-c-hold-and-the-45-c-interlock-trip).

The rod time constant is tens of minutes, so a late start never reaches steady state.

- [ ] Steady-state trial: `T_set = 45 °C` (never above 55 °C). Move the other 4 probes between holes and
      choose positions from `ln θ` vs `x`. Requirements: the farthest point satisfies `0 < θ₅ ≤ θ₁/e`, the
      points spread out on the semilog plot instead of bunching at one end, and none of them sits in noise
      or room-temperature drift.
- [ ] Once the positions are chosen, **do not move them again**; record each position and its uncertainty
      and add them to the sensor map.
- [ ] Bring the whole rod back to `T_set = 20 °C` to equilibrate, record the room temperature (measured far
      from the apparatus) and all six channels, and confirm the rod-to-rod differences are inside the
      calibration criterion. This segment is the baseline.
- [ ] Run a **non-oscillatory** `20 → 45 °C` step with the PI controller and record continuously until the
      steady-state criterion is met. Save the commanded TEC temperature, the measured TEC temperature and
      the **measured rod 1 `T(0, t)`** (the model boundary condition uses rod 1).
- [ ] Steady-state criterion, written down before the run: every probe with `|dT_i/dt| < 0.02 °C/min` for
      ≥ 10 min. The implementation in `Module_7/python/analysis/stationary_fin_fit.py` requires both a
      whole-window least-squares slope and a first-third/last-third mean difference ≤ 0.1 °C; a run that
      fails is refused outright (exit code 2, no fit written), because "not moving at the instant the
      window opens" slips past a whole-window slope while it biases the profile mean.
- [ ] Record observations along the way: which probe responds first and how the amplitude decays with
      distance. They are compared against the predictions in §8.

## 5. Tonight: the A4 Part 2 derivation (the core 6/10, no more postponing)

Six of the A4 ten marks sit in Part 2 (3 marks, derivation) and Part 3 (3 marks, error assessment). Both
are pure theory and depend on none of today's data.

- [ ] Read Lienhard §4.5 (pp. 163–173) alongside
      [fin-design-derivation](https://sethfraden.github.io/Phys39F26-course/labs/fin-design-derivation/)
      and follow (4.28) → (4.30) → (4.31b) → (4.41).
- [ ] Energy balance on a slice (every symbol with its unit):

```text
−kA (dT/dx)|_{x+δx} + kA (dT/dx)|_x + hP δx (T − T∞) = 0        [W]
δx → 0  ⇒  d²θ/dx² − m²θ = 0,    m² = hP/(kA)                     [1/m², m in 1/m]
θ(0) = θ₀ (Dirichlet); dθ/dx|_{x=L} = 0 (Neumann, insulated end)
⇒  Θ(x) = cosh[m(L − x)] / cosh(mL),   Θ_tip = 1/cosh(mL)
```

- [ ] State the physical meaning of both boundary conditions: the base temperature is measured at rod 1
      (not an ideal heat source, not the TEC setpoint); the insulated end means no net heat flow through
      the end face.
- [ ] Part 1: Lienhard Problem 1.3, giving units in every line and pointing out the physically unreasonable
      result.
- [ ] Write it all into [a4_finite_length_biot.md](../assessments/a4_finite_length_biot.md), ticking boxes
      as you go.

## 6. Tuesday: A4 Part 3/4 + position analysis + C5 rehearsal

- [ ] Part 3: the semi-infinite limit from Problem 4.12; end-condition approximations from Example 4.8 /
      Problem 4.20; `mL` and per-point `ε_T(x)` from the **measured** `L` and positions; the conclusion must
      name the positions it depends on and the criterion used. If `ε_T > 5 %`, keep the finite cosh
      solution and say so.
- [ ] Part 4: compute `Bi⊥ = hR/(2k)` and the self-consistent form `(mR/2)²` separately; give the radial
      conclusion **on its own** without merging it into the Part 3 length conclusion; answer the heat-sink
      vs spacecraft-radiator application question (no convection in space, so use
      `q″ = εσ(T_s⁴ − T_sur⁴)`).
- [ ] Write `docs/module_notes/module_07_rod_instrument.md`: sensor map, calibration outcome, geometry,
      baseline, step traces, run metadata, code file names and commit hash.
- [ ] Run `Module_7/python/analysis/stationary_fin_fit.py`, fill `m`, `σ_m`, `1/m`, `Θ_tip`, `Bi∥`, `Bi⊥`
      and both residual maxima into §8 of [module_07_stationary_fin.md](module_07_stationary_fin.md), and run
      `Module_7/python/test_stationary_fin_fit.py` (22 hardware-free tests) and
      `Module_7/python/analysis/stationary_diagnostics.py` (11 more) for the systematics of a record that does not
      reach steady state.
- [ ] C5 rehearsal: each member explains one link of the measurement chain plus **one dominant
      uncertainty** (candidates: sensor position, contact resistance, room-temperature drift, residual
      calibration offset, the fitting uncertainty of `m`). Be ready to answer "why is the boundary
      condition rod 1 and not the TEC?" and "why can a steady-state experiment not separate `k` from `h`?"
- [ ] Export `A4_Lastname.pdf` with name, A4, date, repository URL and the **exact commit hash** on the
      first page (commit first, then fill the hash in).

## 7. Wednesday 10/28: two hard deadlines

- [ ] Before **09:05**: submit `A4_Lastname.pdf` on Moodle; confirm that
      `docs/assessments/a4_finite_length_biot.md` is pushed.
- [ ] Before **11:55**: submit the C5 Team Checkoff receipt on Moodle, citing the pushed acquisition code
      and evidence commits.
- [ ] Demonstrate C5 in class: the rod probes after their cross-check, sensor coordinates and wiring, the
      six-channel simultaneous record, baseline + first step data, and files with timestamps, units,
      labels and notes.

## 8. Prediction record (write it before applying heat)

Four sentences first, numbers second; replace the table below with numbers recomputed from the measured
geometry.

1. Response order: `rod1 → rod2 → …` (farther from the TEC means later and smaller).
2. Amplitude decay: roughly `e^{−mΔx}` per segment.
3. Stationary profile shape: `cosh[m(L − x)]`, convex upwards, flattening at the tip (`dθ/dx = 0`).
4. Will the finite end be visible? Quote the predicted `Θ_tip = 1/cosh(mL)` and state that "> 0.1 means the
   finite end is visible".

Rough estimate for the course geometry plus literature orders of magnitude (`k = 167 W/(m·K)`,
`d = 12.7 mm`, `L = 0.30 m`), only to form expectations:

| `h` (W/m²K) | `m` (1/m) | `1/m` (m) | `mL` | `Θ_tip` | `Bi⊥` |
|---|---|---|---|---|---|
| 5 | 3.07 | 0.33 | 0.92 | 0.69 | 9.5×10⁻⁵ |
| 7 | 3.63 | 0.28 | 1.09 | 0.60 | 1.3×10⁻⁴ |
| 10 | 4.34 | 0.23 | 1.30 | 0.51 | 1.9×10⁻⁴ |

- Prediction A: `Bi⊥ ~ 10⁻⁴ ≪ 1`, so the one-dimensional radial approximation holds (large `k`, small `d`).
- Prediction B: `mL ≈ 1`, the tip still carries 50–70 % of the base excess, and the semi-infinite
  approximation passes 5 % error from `x ≳ 5 cm` — so A4 Part 3 must keep the finite-length solution. This
  is also the direction of Lienhard's empirical threshold (temperature needs `mL ≳ 5`).

After fitting, annotate each prediction "supported / not supported / cannot determine" and write down the
residual deviations that remain unexplained.

## 9. Pre-submission checklist

- [ ] The Module 6 sketch and GUI are **unmodified** (`git diff` on them is empty).
- [ ] No raw CSV was overwritten; corrections exist only in `*_corrected*` columns or separate files.
- [ ] Every figure has axis labels and units; `m` in m⁻¹, `1/m` in m, `Bi⊥` and `ε_T` dimensionless.
- [ ] Both fits were done (finite and semi-infinite), both residual sets are plotted, and the shift in `m`
      from ignoring the finite end is reported next to the fitting uncertainty (the script produces all of
      it at once: `data/processed/<run>_stationary_fit.json`, `<run>_stationary_profile.csv`,
      `figures/part_03_stationary_profile.png`).
- [ ] The A4 first page carries the exact commit hash; the hash cited in the C5 receipt matches what was
      actually pushed.

## VS Code agent instructions (for use on site)

> Read `docs/module_notes/module_07_lab_day_runbook_2026-10-26.md` and `Module_7/README.md` first. Advance
> one unfinished step at a time. Code, CSV column names and the serial format may be checked directly;
> wiring, temperature readings, instructor approval and apparatus state must be confirmed on site by the
> operator. After each step, record the numbers and the evidence, tick the box, and state the exact next
> action or reading. Never rewire, power the TEC, raise the PWM, change a safety threshold, or leave a
> powered run unattended on your own initiative. If anything looks wrong, have the operator cut actuator
> power and tell the instructor. Never mix trial or safety CSVs into the formal steady-state data.

References: [Module 7 Part I](https://sethfraden.github.io/Phys39F26-course/labs/theory-bridge-chapter-1/) ·
[Part II](https://sethfraden.github.io/Phys39F26-course/labs/fin-design-derivation/) ·
[Part III](https://sethfraden.github.io/Phys39F26-course/labs/lab-08/) ·
[TEC + rod simulator](https://sethfraden.github.io/Phys39F26-course/simulators/tec-rod-control/)



