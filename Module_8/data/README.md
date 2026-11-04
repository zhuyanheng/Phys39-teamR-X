# Module 8 data

- `raw/`: only actual Module 8 acquisition CSVs. The GUI opens an exclusive,
  timestamped `module_08_rod_*.csv` here regardless of its working directory.
- `processed/`: reproducible analysis results; acquisition summaries go in `pilot_checks/`.
- `calibration/`: correction tables and corrected copies from a real common-bath
  experiment, if one is performed. Never fit calibration using a heated rod's spatial gradient.
- `reference/`: historical inputs with their original qualifications. The Module 4
  steady-state table was copied byte for byte. Existing raw evidence remains in Module 4.

Do not save synthetic test data as measurements, overwrite raw files, or relabel
Module 7 runs as Module 8 experiments. Temporary test files remain outside this
directory. Purpose-based renaming at write-up must preserve raw file bytes;
regenerate derived artifacts under the new stem.

Figures go in `Module_8/figures/`; report PDFs go in `Module_8/output/pdf/`.
The hardware-free GUI preview does not create a CSV.

Each live connection also writes the exact incoming bytes to a sibling `.serial.log`.
Every plan upload creates an immutable `_plan_NN.json` beside the CSV, including
plan, calibration provenance, sensor map and source hashes. Keep these files with
the raw CSV. Rehearsal purpose is recorded in the plan; it is not production data.
