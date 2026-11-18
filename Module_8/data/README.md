# Module 8 data

- `raw/`: actual Module 8 acquisition CSVs, exact serial logs and immutable
  plan snapshots. Recorded sessions use the names below. The acquisition GUI
  still creates exclusive timestamped `module_08_rod_*.csv` files during a live
  session; standardize a session after capture, preserving every source byte.
- `processed/`: reproducible analysis results; acquisition summaries go in `pilot_checks/`.
- `simulation/`: explicitly labelled mathematical simulation histories and their
  setup/hash receipts. Stage 2's six runs are in `simulation/s18_3/`; their
  completed worksheet and measured-fit metrics are in `processed/stage2/`.
- `calibration/`: correction tables and corrected copies from a real common-bath
  experiment, if one is performed. Never fit calibration using a heated rod's spatial gradient.
- `reference/`: historical inputs with their original qualifications. The Module 4
  steady-state table was copied byte for byte. Existing raw evidence remains in Module 4.

Do not save synthetic test data as measurements, overwrite raw files, or relabel
Module 7 runs as Module 8 experiments. Temporary test files remain outside this
directory. Purpose-based renaming at write-up must preserve raw file bytes;
regenerate derived artifacts under the new stem.

## Naming and navigation

Start with [the dataset index](DATASET_INDEX.md). The machine-readable equivalent
is [dataset_index.json](dataset_index.json). Seventeen sessions are grouped by
use: five PI rod records, OPEN/P boundary comparisons, raw-PWM experiments,
rehearsals and a setup-only connection. A filename describes the settings; it
does not certify a record as settled or complete.

Canonical raw stem:

    m08_<mode>_p<period>s[_ua<mean PWM>_ub<amplitude PWM>]_<YYYYMMDD>_<HHMMSS>_<microseconds>

Modes are `pi`, `p`, `open`, `raw_zero` and `raw_pos`. Prefixes `rehearsal_` and
`setup_` identify multi-period rehearsals and a connection with no RUNNING
measurements. Raw-PWM settings use `ua` and `ub` to distinguish the 50/100 PWM
and positive-only trials. The timestamp is the original local acquisition-file
creation time, not the controller STEP time. Its six microsecond digits are
retained to preserve identity and avoid collisions.

Each session keeps the same stem across `.csv`, `.serial.log` and
`_plan_01.json` (plus `_plan_02.json` where present). Derived artifacts use
`m08_pi_p100s_analysis.json`, for example, and
`m08_pi_five_period_summary.csv` for cross-period results. Analysis snapshots
are frozen source prefixes, not additional experiments.

[file_renames_20261118.csv](file_renames_20261118.csv) and its JSON counterpart
map every original path to its new path. Raw files and snapshot contents were
verified byte-for-byte; open files were checked against their captured prefix.
Immutable plans and historical verification receipts retain capture-time names
and hashes internally; use this mapping to resolve those historical references.

The connected November 18 GUI held two old output paths open during naming.
Those two old names remain as symbolic links to the canonical 400 s CSV/log,
so its passive DONE-state logging can continue. They are aliases to the same
files, not duplicate measurements. Keep them while that GUI session remains
open; they may be removed once the session is closed.

Figures go in `Module_8/figures/`; report PDFs go in `Module_8/output/pdf/`.
The hardware-free GUI preview does not create a CSV.

Each live connection also writes the exact incoming bytes to a sibling `.serial.log`.
Every plan upload creates an immutable `_plan_NN.json` beside the CSV, including
plan, calibration provenance, sensor map and source hashes. Keep these files with
the raw CSV. Rehearsal purpose is recorded in the plan; it is not production data.
