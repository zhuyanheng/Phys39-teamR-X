# Module 7 documentation index

`Module_7/` holds only **this module's own** artefacts. The evidence notes the course asks for live in the repository-root `docs/`, following the same convention as Modules 1-6, and are not duplicated here.

## This directory

| File | Contents |
| --- | --- |
| `README.md` (this file) | Index of Module 7 documentation: which documents live in the repository-root `docs/`, and where figures and data come from |
| `../README.md` | Module 7 experiment design, the six components, the prediction record, the software extension plan |

## Module 7 evidence in the repository-root `docs/`

| File | Contents | Status |
| --- | --- | --- |
| `docs/module_notes/module_07_state.md` | Status snapshot: what exists, what is verified, what is missing, and the known warts; read this first when picking the module up cold | Present |
| `docs/module_notes/module_07_lab_day_runbook_2026-10-26.md` | Lab-day sequence: software, geometry, calibration, step, steady state | Present |
| `docs/module_notes/module_07_step1_integration_check.md` | On-site procedure for the first power-up of the six-channel chain: wiring, expected voltages, per-channel fingerprints, fault injection | Present |
| `docs/module_notes/module_07_rod_instrument.md` | Sensor map, same-temperature check record, geometry, baseline/step, run metadata; includes the decision to skip the soak calibration and what that costs | Holes 2, 5, 7, 8, 9 and the measured distances recorded 2026-10-30; the 2026-11-02 20 °C/40 °C runs, the 45 °C interlock trip and the ≈ 30 min settling estimate recorded 2026-11-02; `sigma`, residuals and the `h` inversion still to be filled in |
| `docs/module_notes/module_07_stationary_fin.md` | Part 3 method, steady-state criteria, the two models, two-layer uncertainty, predictions for the measured geometry, open items | Method and script complete (20 tests pass); §9 records the 2026-11-02 verdict: both runs refused, no stationary profile yet |
| `docs/assessments/a4_finite_length_biot.md` | A4, parts 1-4 | Scaffold only: the four parts and the submission header are still `TODO` |

## Figures

`Module_7/figures/` is written by the analysis scripts. The file names map one-to-one onto the figure numbers used in the report:

- `part_01_sensor_map.png` - rod geometry, hole positions, probe numbering
- `part_02_step_response.png` - six-channel step response (no calibration correction curves: the soak was skipped)
- `part_03_stationary_profile.png` - stationary profile with both fits and both residual sets

Nothing in `part_*.png` exists yet. Diagnostic figures are not deliverable figures: the per-run check traces sit
in `figures/pilot_checks/<raw stem>_temperatures.png`, one file per checked run.

Every number that appears in a figure must be traceable to a fit result in `Module_7/data/processed/`, and vice versa.
