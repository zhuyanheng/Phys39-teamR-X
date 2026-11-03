# Module 7 status snapshot

One-page handover for Module 7 Part III. The *detail* lives in the linked documents; this page records only
**where the work stands**, so that picking the module up cold does not mean reading everything again. Update
it by editing the tables in place at the end of a working session — do not append a diary.

## Read in this order

1. this page — what exists, what is verified, what is missing (about 5 minutes)
2. [lab-day runbook, S16 → S17](module_07_lab_day_runbook_2026-10-26.md) — what to do next, ordered by dependency
3. [Module 7 README](../../Module_7/README.md) — theory, A4/C5 requirements, and §7 conventions
4. [rod instrument record](module_07_rod_instrument.md) and [stationary fin note](module_07_stationary_fin.md) —
   only the sections the current task needs

## Code

| File | State | Verified by |
| --- | --- | --- |
| `arduino/module_07_rod_controller/module_07_rod_controller.ino` | Six channels (A0 = TEC, A1–A5 = rod); A0 remains the only PI and safety input | On-site six-channel runs recorded 2026-11-02: all six columns finite, `rod_ok=5` on every row. The Step 4 integration check write-up is still open |
| `python/rod_protocol.py` | Complete: header line, parser, per-channel validity | 21 hardware-free tests |
| `python/rod_acquisition_gui.py` | Complete: two linked plots (TEC+setpoint, rods A1–A5 on their own axis), x axis always spans the whole run from t=0 with wheel-zoom / drag-pan / `Fit x`, one CSV column per channel, `rod_ok` counter, event marks, LF-only raw CSV | 12 hardware-free tests (fake serial port, offscreen Qt) |
| `python/analysis/cross_calibration_fit.py` | Complete: criterion, calibration table, corrected CSV, fit figure | 24 tests on synthetic six-channel data; **no measured input exists** |
| `python/analysis/stationary_fin_fit.py` | Complete: steady-state criteria, finite and semi-infinite fit, residual sets, two-layer uncertainty, refusal on a bad run; relaxed limits self-identify (`criterion.relaxed`, console banner, figure title) | 22 tests |
| `python/analysis/stationary_diagnostics.py` | Complete, **diagnostic only**: the systematics of a drifting record (`window_slide`, `extrapolation`, `ambient`, `geometry`, `origin_swap`), strict JSON with `source_sha256` / `raw_unchanged` / `worst_change_percent`; `--ambient` is required | 11 tests |
| `python/analysis/sensor_map_figure.py` | Complete: Part 1 figure from the ruler geometry (`d` is drawn as nominal, said so in the figure) | 11 tests, shared with the next row |
| `python/analysis/step_response_figure.py` | Complete: Part 2 figure from a raw CSV, event rows placed on the Arduino axis through `host_time`, commanded regions shaded, PI limit cycle measured on the trace | `python/test_module_figures.py`, 11 tests (offscreen matplotlib) |
| `python/analysis/pilot_run_check.py` | Complete, diagnostic only (not a fit) | Run by hand on a pilot file |
| `run_rod_acquisition.command` | Works; `--preview` for a dry run | Manual |

Run the whole hardware-free suite after touching any script (no Arduino, serial port or Qt window needed):

```bash
.venv/bin/python -m unittest discover -s Module_7/python -t Module_7/python   # 101 tests, expect OK
```

Per file: 21 protocol + 12 GUI + 24 cross-calibration + 22 stationary fit + 11 diagnostics + 11 figures.

## Data and figures

| Path | State |
| --- | --- |
| `Module_7/data/raw/` | Four runs, each named for its purpose and commanded programme: `module_07_rod_pilot_20C_30C_20C`, `module_07_rod_pi_check_20C`, `module_07_rod_interlock_trip_45C_40C`, `module_07_rod_stationary_40C` (31 min at 40 °C, `Kp = 100`, `Ki = 0.3` — the longest record and the input to §10 of the stationary note). The GUI's timestamped name is only a scratch name, replaced at write-up; the seven few-second UI-check runs and one uncontrolled 2-minute passive record were deleted on 2026-11-02; rows are never modified or overwritten |
| `Module_7/data/calibration/` | **Empty by decision** — the soak cross-calibration was skipped; the cost is quantified in the [rod instrument record](module_07_rod_instrument.md) |
| `Module_7/data/processed/pilot_checks/` | Three `<raw stem>_quality.json`, one per checked run (2026-10-30 pilot and both short 2026-11-02 runs) |
| `Module_7/data/processed/` | **No certified `<raw stem>_stationary_fit.json`**: all three runs were refused by the pre-registered steady-state criteria (exit 2), see [stationary fin note §9](module_07_stationary_fin.md). What does exist is the **diagnostic pair** for `module_07_rod_stationary_40C`: `_stationary_fit.json` + `_stationary_profile.csv` for the relaxed 674 s window (`criterion.relaxed: true`) and `_stationary_diagnostics.json` with the five systematics and `worst_change_percent` |
| `Module_7/figures/` | The three Part 1–3 deliverables exist: `part_01_sensor_map.png`, `part_02_step_response.png`, `part_03_stationary_profile.png` (the last one is titled `CRITERION RELAXED`, because it is a diagnostic profile, not a certified steady state). Diagnostic traces stay in `figures/pilot_checks/<raw stem>_temperatures.png` |

## Documents

| File | State |
| --- | --- |
| [lab-day runbook](module_07_lab_day_runbook_2026-10-26.md) | Complete, §§0–9, current |
| [Step 1 integration check](module_07_step1_integration_check.md) | Complete: wiring, expected voltages, per-channel fingerprints, fault injection |
| [rod instrument record](module_07_rod_instrument.md) | Partial: holes 2, 5, 7, 8, 9, the measured distances, the skip decision and the 2026-11-02 runs (incl. the 45 °C interlock trip, the ≈ 30 min settling estimate and the 31 min confirmation run) are in; residuals and the `h` inversion are not |
| [stationary fin note](module_07_stationary_fin.md) | Method, criteria and two-layer uncertainty complete. §9: all three runs refused, so **no certified steady profile**. §10: the diagnostic fit the 31-minute record supports (`m = 4.83 ± 0.07 1/m` on its trailing window) with the five systematics, the `T∞ = 23.95 °C` self-ambient derivation, and a ready-to-quote paragraph that keeps the diagnosis attached |
| [`a4_finite_length_biot.md`](../assessments/a4_finite_length_biot.md) | Four-part theoretical draft completed 2026-11-03 for Yanheng Zhu, with exact textbook problem checks and installed geometry. Diameter is explicitly nominal. PDF: `Module_7/output/pdf/A4_Zhu.pdf`. Student review and submission are not confirmed |
| `Module_7/README.md`, `Module_7/data/README.md`, `Module_7/docs/README.md` | Current, English |

## What is actually missing

- **A4 (individual):** all four parts and the PDF are prepared for Yanheng Zhu, using the user-authorized nominal
  12.7 mm diameter and the recorded positions. Numerical verification is in
  `Module_7/data/processed/a4_predictions/`; the source checkpoint is embedded by the PDF builder. Still open:
  student review, a diameter measurement and geometry uncertainties if available, and Moodle submission.
- **On site, done 2026-11-02:** six-channel sketch running and logging; three runs written to disk at 20 °C, 40 °C
  and 31 min at 40 °C. What that proves and what it does not is in the
  [rod instrument record](module_07_rod_instrument.md); the certified Part 3 fit is still refused
  ([§9](module_07_stationary_fin.md)).
- **Part figures, done:** `part_01_sensor_map.png`, `part_02_step_response.png` and
  `part_03_stationary_profile.png` are generated by committed scripts and regenerated by rerunning them. The
  2026-11-02 documentation pass reran all three commands plus both fits and got byte-identical PNG, JSON and CSV
  files, so the committed artefacts are exactly what the committed scripts emit.
- **On site, still open:** remaining geometry with uncertainties (diameter, `L`, probe distances) and the Step 4
  integration check write-up; a **steady** 40 °C hold — the 31 min run still moved 0.052 °C/min at `rod5_C`, and the
  fitted `τ ≈ 591 s` for that probe puts the remaining wait at ≈ 12 min for the drift and ≈ 9 min for the slope,
  i.e. ≈ 15 min of *additional* holding (≈ 45 min in total), not another 31-minute attempt from cold; a separate
  room thermometer for `--ambient` (the current value is a self-ambient,
  [§10.0](module_07_stationary_fin.md)); and §6 check 2 (shape at a second temperature).
- **Then:** fill the two record documents with the certified numbers, and the C5 demonstration plus receipt.

The ordered checklist with deadlines is [README §8](../../Module_7/README.md#8-action-list-in-priority-order).

## Known warts

- **The only `m` in the repository is a diagnostic one.** `module_07_rod_stationary_40C_stationary_fit.json`
  carries `criterion.relaxed: true` and `part_03_stationary_profile.png` is titled `CRITERION RELAXED`. Quoting
  `m = 4.83 1/m` without that sentence, or dropping the words "trailing-window diagnostic", would present a
  drifting record as a steady profile. The systematics that must travel with it are in
  [stationary fin note §10](module_07_stationary_fin.md).
- **`T∞ = 23.95 °C` is a self-ambient**, the six-channel mean of the pre-heat rest rows, not an independent room
  thermometer ([§10.0](module_07_stationary_fin.md)). It is required rather than optional in
  `stationary_diagnostics.py` on purpose; its ±1 °C cost is +7.6 % in `m`.
- The diagnostic JSON fits the **trailing 600 s**, while
  `stationary_fin_fit.py` writes the **674 s** window its relaxed criterion accepts. The two bases differ by
  0.4 % (4.804 vs 4.826 1/m), and every percentage in the diagnostics JSON is relative to the 600 s base; that
  is stated in the note, but it is a trap when comparing the two files by eye.
- `step_response_figure.limit_cycle` has to tolerate rows whose `time_s` is blank (event rows). It does now, with
  a test; anything else that reads a raw CSV must do the same, because event rows carry `host_time` only.
- `data/processed/pilot_checks/<raw stem>_quality.json` stores an absolute `source` path from the machine that
  produced it. Harmless as evidence (the SHA-256 is the identity of the file), but not portable; re-running
  `pilot_run_check.py` on the raw file rewrites it with a local path. All three current files carry the path of
  the machine that checked them.
- `stationary_fin_fit.py --hold` is a **minimum**, and `steady_window()` returns the longest trailing window that
  passes, so `--hold 120` does *not* select the last 120 s of a 12-min run — with a relaxed criterion it selects
  the whole run. A genuine snapshot has to be made by truncating the rows before calling `analyse()`.
- The ≈ 30 min settling estimate in the rod instrument record comes from a log-linear fit of 60 s block slopes
  made outside the repository. The 31 min run then showed that estimate to be ≈ 15 min short, and the *committed*
  replacement is now the `extrapolation` block of the diagnostics JSON (`τ = 591–739 s` per probe, rms
  0.035–0.068 °C), which is what the note quotes. The original planning fit still lives only in the record; the
  committed JSON is the citable version.
- Raw CSV line endings are mixed: the two 2026-11-02 files are CRLF (the GUI then used the `csv` default), later
  ones will be LF (`lineterminator='\n'`). `Module_7/data/raw/**` is marked `-text` in `.gitattributes`, so every
  raw file is checked out byte for byte and the SHA-256 in its quality JSON stays valid; do not drop that rule.
- The **processed** CSVs are written **LF-only** (`stationary_fin_fit.py` passes `lineterminator="\n"`, with a
  test). They are not marked `-text`, so `* text=auto` normalises them on commit; CRLF from the `csv` default
  would therefore make every rerun show the committed file as modified. Keep new writers LF-only for the same
  reason, and keep the two kinds of CSV distinct: raw = evidence (byte-exact, `-text`), processed = regenerable
  (normalised, LF).
- `stationary_fin_fit.py` deliberately writes repository-relative paths. Keep that behaviour when editing it,
  and keep the portability test green.

## Conventions

Deliberately not repeated here: naming and file layout are in
[Module 7 README §7](../../Module_7/README.md#7-directory-and-naming-conventions), and the rules for what may be
written into `data/` are in [`Module_7/data/README.md`](../../Module_7/data/README.md). Documents are in
English, like every other note in `docs/module_notes/`.
