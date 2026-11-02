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
| `python/rod_acquisition_gui.py` | Complete: six traces, one CSV column per channel, `rod_ok` counter, event marks | 8 hardware-free tests (fake serial port, offscreen Qt) |
| `python/analysis/cross_calibration_fit.py` | Complete: criterion, calibration table, corrected CSV, fit figure | 24 tests on synthetic six-channel data; **no measured input exists** |
| `python/analysis/stationary_fin_fit.py` | Complete: steady-state criteria, finite and semi-infinite fit, residual sets, two-layer uncertainty, refusal on a bad run | 20 tests |
| `python/analysis/pilot_run_check.py` | Complete, diagnostic only (not a fit) | Run by hand on a pilot file |
| `run_rod_acquisition.command` | Works; `--preview` for a dry run | Manual |

Run the whole hardware-free suite after touching any script (no Arduino, serial port or Qt window needed):

```bash
.venv/bin/python -m unittest discover -s Module_7/python -t Module_7/python   # 73 tests, expect OK
```

## Data and figures

| Path | State |
| --- | --- |
| `Module_7/data/raw/` | Eight runs: six from 2026-10-30 and two from 2026-11-02, the latter tagged `..._T20C.csv` and `..._T20C_trip45C_T40C.csv` (setpoint tags, rows untouched); never modified or overwritten |
| `Module_7/data/calibration/` | **Empty by decision** — the soak cross-calibration was skipped; the cost is quantified in the [rod instrument record](module_07_rod_instrument.md) |
| `Module_7/data/processed/pilot_checks/` | Three `<raw stem>_quality.json`, one per checked run (2026-10-30 pilot and both 2026-11-02 runs) |
| `Module_7/data/processed/` | No `<raw stem>_stationary_fit.json` — both 2026-11-02 runs were **refused** by the steady-state criteria (exit 2); see [stationary fin note §9](module_07_stationary_fin.md) |
| `Module_7/figures/` | Three `pilot_checks/<raw stem>_temperatures.png`; no `part_*.png` deliverable figure yet |

## Documents

| File | State |
| --- | --- |
| [lab-day runbook](module_07_lab_day_runbook_2026-10-26.md) | Complete, §§0–9, current |
| [Step 1 integration check](module_07_step1_integration_check.md) | Complete: wiring, expected voltages, per-channel fingerprints, fault injection |
| [rod instrument record](module_07_rod_instrument.md) | Partial: holes 2, 5, 7, 8, 9, the measured distances, the skip decision and the 2026-11-02 runs (incl. the 45 °C interlock trip and the ≈ 30 min settling estimate) are in; `sigma`, residuals and the `h` inversion are not |
| [stationary fin note](module_07_stationary_fin.md) | Method, criteria and two-layer uncertainty complete; §9 records why there is still no steady profile (300 s of recording ≠ 300 s of steady state; 45 °C is unreachable) |
| [`a4_finite_length_biot.md`](../assessments/a4_finite_length_biot.md) | **Scaffold only** — all four parts still `TODO` |
| `Module_7/README.md`, `Module_7/data/README.md`, `Module_7/docs/README.md` | Current, English |

## What is actually missing

- **A4 (individual):** the four parts, then `A4_Lastname.pdf` with the commit hash on the first page. Needs no
  measurements, so it is the only work that can proceed with the rod unavailable.
- **On site, done 2026-11-02:** six-channel sketch running and logging; two runs written to disk at 20 °C and
  40 °C. What that proves and what it does not is in the [rod instrument record](module_07_rod_instrument.md).
- **On site, still open:** remaining geometry with uncertainties (diameter, `L`, probe distances) and the Step 4
  integration check write-up; a **40 °C hold of ≈ 30 min** for the stationary profile (45 °C trips the
  interlock, and 300 s leaves the far probes at 0.5 °C/min); the two substitute checks of
  [stationary fin note §6](module_07_stationary_fin.md).
- **Then:** both fits with residual sets, fill the two record documents, the two `part_*.png` figures, and the C5
  demonstration plus receipt.

The ordered checklist with deadlines is [README §8](../../Module_7/README.md#8-action-list-in-priority-order).

## Known warts

- `data/processed/pilot_checks/<raw stem>_quality.json` stores an absolute `source` path from the machine that
  produced it. Harmless as evidence (the SHA-256 is the identity of the file), but not portable; re-running
  `pilot_run_check.py` on the raw file rewrites it with a local path. All three current files carry the path of
  the machine that checked them.
- `stationary_fin_fit.py --hold` is a **minimum**, and `steady_window()` returns the longest trailing window that
  passes, so `--hold 120` does *not* select the last 120 s of a 12-min run — with a relaxed criterion it selects
  the whole run. A genuine snapshot has to be made by truncating the rows before calling `analyse()`.
- The ≈ 30 min settling estimate in the rod instrument record comes from a log-linear fit of 60 s block slopes
  made outside the repository. It is a planning figure; promoting it to a committed `_check` script (with tests)
  is the way to make it citable.
- `stationary_fin_fit.py` deliberately writes repository-relative paths. Keep that behaviour when editing it,
  and keep the portability test green.

## Conventions

Deliberately not repeated here: naming and file layout are in
[Module 7 README §7](../../Module_7/README.md#7-directory-and-naming-conventions), and the rules for what may be
written into `data/` are in [`Module_7/data/README.md`](../../Module_7/data/README.md). Documents are in
English, like every other note in `docs/module_notes/`.
