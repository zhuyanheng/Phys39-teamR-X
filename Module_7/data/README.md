# Module 7 data conventions

Only **measured** things live here, never derived things. The subdirectories never overwrite each other:

| Directory | Contents | Written by |
| --- | --- | --- |
| `raw/` | Raw CSV written straight by the GUI, which opens it as `module_07_rod_<YYYYmmdd_HHMMSS_microseconds>.csv` — a scratch name. Once a run is written up the file is renamed to its **purpose name** `module_07_rod_<role>_<programme>.csv`, e.g. `module_07_rod_stationary_40C.csv` | `Module_7/python/rod_acquisition_gui.py` (opened in `'x'` mode, never overwritten); the rename is by hand when a run is written up |
| `calibration/` | Cross-calibration coefficient table (`a_i`, `b_i`, temperature range, residual statistics) + corrected data CSV | `python/analysis/cross_calibration_fit.py` |
| `processed/` | Stationary-profile and step-response fits (`m`, `1/m`, chi-squared, criterion table): `<run>_stationary_fit.json` + `<run>_stationary_profile.csv` | `python/analysis/stationary_fin_fit.py` (figure goes to `figures/part_03_stationary_profile.png`) |
| `processed/pilot_checks/` | Quality check of one pilot run (row counts, gaps, per-channel slopes): `<run>_quality.json` | `python/analysis/pilot_run_check.py` |

Rules:

1. **Raw columns are never rewritten.** Corrected values are stored as new `rod1_corrected_C` ... `rod5_corrected_C` columns or in a separate file, and the calibration-table version that was applied is written down next to them.
2. Every file in `raw/` corresponds to one real run; do not hand-edit, merge or "clean" them. `Module_7/data/raw/**` is marked `-text` in the repository `.gitattributes`, so these files are checked out byte for byte and the SHA-256 quoted in a `_quality.json` always matches the working copy. The GUI writes LF line endings; the `pi_check` and `interlock_trip` runs (recorded on 2026-11-02) predate that and are CRLF, which is why the attribute exists.
3. The first line of every CSV is the header. The first 14 measurement columns have the same names and the same order as the firmware `DATA` line (see `Module_7/python/rod_protocol.py`); the `event` column separates `measurement`, `start`, `stop`, `setpoint_step`, `operator_mark`, `connect`, `disconnect`.
4. Analysis scripts only ever read `raw/`; their outputs may only be written to `calibration/` or `processed/`.
5. Derived file names are `<raw file stem>_<artifact>.<ext>`, so every processed artefact points back to exactly one raw run. Only the raw file itself keeps the `module_07_` prefix, because it travels into reports where the module number is no longer implied by the path. An artefact that records where it came from stores that path **relative to the repository root** (`Module_7/data/raw/<raw stem>.csv`), never an absolute path: a committed JSON must not carry one machine's home directory.
6. A raw name says what the run is **for**, not when it ran. The GUI can only write a timestamp, so its name is a scratch name; once the run is written up it becomes `module_07_rod_<role>_<programme>.csv`:

   | Element | Meaning | Values in use |
   | --- | --- | --- |
   | `module_07_rod_` | module prefix, kept because raw files are quoted outside this directory | |
   | `<role>` | why the run exists | `pilot` (function and propagation trial), `pi_check` (gains and controller behaviour), `interlock_trip` (safety demonstration), `stationary` (input to the fin fit), `step` (step response) |
   | `<programme>` | the commanded setpoint sequence, chronological, one `<value>C` segment per hold | `20C_30C_20C`, `20C`, `45C_40C`, `40C` |

   Lower case except the unit. **When** the run happened is deliberately absent from the name: every row carries `host_time`, the quality JSON carries the timestamps and the SHA-256, and the run table in `docs/module_notes/module_07_rod_instrument.md` carries the wall clock and the commanded sequence. Rows and bytes never change in the rename — the file hashes the same before and after — and the derived artefacts are **regenerated under the new stem** (rule 5) instead of being renamed by hand, so their `source` field also points at the new name. This purpose name is the only part of a raw file name that may change after the fact.
7. What gets committed is the handful of runs that support the report's conclusions (together with the run metadata in `docs/module_notes/module_07_rod_instrument.md`), not every raw file. That file is also the inventory: it says what each committed run was commanded to do.
