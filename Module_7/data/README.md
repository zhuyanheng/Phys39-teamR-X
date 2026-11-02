# Module 7 data conventions

Only **measured** things live here, never derived things. The subdirectories never overwrite each other:

| Directory | Contents | Written by |
| --- | --- | --- |
| `raw/` | Raw CSV written straight by the GUI, named `module_07_rod_<YYYYmmdd_HHMMSS_microseconds>.csv`, with an optional chronological setpoint tag after the timestamp (`..._T20C.csv`, `..._T20C_trip45C_T40C.csv`) | `Module_7/python/rod_acquisition_gui.py` (opened in `'x'` mode, never overwritten); the tag is added by hand when a run is written up |
| `calibration/` | Cross-calibration coefficient table (`a_i`, `b_i`, temperature range, residual statistics) + corrected data CSV | `python/analysis/cross_calibration_fit.py` |
| `processed/` | Stationary-profile and step-response fits (`m`, `1/m`, chi-squared, criterion table): `<run>_stationary_fit.json` + `<run>_stationary_profile.csv` | `python/analysis/stationary_fin_fit.py` (figure goes to `figures/part_03_stationary_profile.png`) |
| `processed/pilot_checks/` | Quality check of one pilot run (row counts, gaps, per-channel slopes): `<run>_quality.json` | `python/analysis/pilot_run_check.py` |

Rules:

1. **Raw columns are never rewritten.** Corrected values are stored as new `rod1_corrected_C` ... `rod5_corrected_C` columns or in a separate file, and the calibration-table version that was applied is written down next to them.
2. Every file in `raw/` corresponds to one real run; do not hand-edit, merge or "clean" them. `Module_7/data/raw/**` is marked `-text` in the repository `.gitattributes`, so these files are checked out byte for byte and the SHA-256 quoted in a `_quality.json` always matches the working copy. The GUI writes LF line endings; the two 2026-11-02 files predate that and are CRLF, which is why the attribute exists.
3. The first line of every CSV is the header. The first 14 measurement columns have the same names and the same order as the firmware `DATA` line (see `Module_7/python/rod_protocol.py`); the `event` column separates `measurement`, `start`, `stop`, `setpoint_step`, `operator_mark`, `connect`, `disconnect`.
4. Analysis scripts only ever read `raw/`; their outputs may only be written to `calibration/` or `processed/`.
5. Derived file names are `<raw file stem>_<artifact>.<ext>`, so every processed artefact points back to exactly one raw run. Only the raw file itself keeps the `module_07_` prefix, because it travels into reports where the module number is no longer implied by the path.
6. A raw name may gain a **setpoint tag** after the timestamp once the run is written up (`T20C` = held at 20 °C, `trip45C` = the 45 °C attempt the interlock cut short, `T40C` = held at 40 °C). The tag is chronological and lower case except the unit, the timestamp keeps meaning "when the GUI opened the file", the rows are never touched, and the SHA-256 recorded in `<raw stem>_quality.json` still identifies the same bytes. This is the only part of a raw name that may change after the fact.
7. What gets committed is the handful of runs that support the report's conclusions (together with the run metadata in `docs/module_notes/module_07_rod_instrument.md`), not every raw file. That file is also the inventory: it says what each committed run was commanded to do.
