# Module 4 formal raw data

This folder is reserved for the **selected, supervised Part 3 steady-state time-series** supporting A2. No formal Part 3 dataset has been collected here yet.

The GUI currently writes timestamped source CSVs into [`Module_4/data/`](../../Module_4/data/). Those six 2026-09-23 files record software-safety, direction, and exploratory actions; they do not supply ten verified steady-state points. Preserve them there. After new runs, identify the exact source file(s), confirm the 10–45 °C limits and `Safety: OK` in each selected interval, then place the canonical Module 4 formal raw file(s) here without keeping redundant committed copies. Record original filename, acquisition date, run IDs, and any excluded/repeated intervals in the [working note](../../docs/module_notes/module_04_open_loop_tec.md). The revised A2 PDF presents analysis, not the raw files themselves, but those files must remain available for later modules.

For plotting, create `steady_state.csv` **only after measurement** with one row for each of H0–H4 and C0–C4 and this header:

```text
run_id,direction,pwm,start_temperature_C,steady_temperature_C,time_waited_s,source_csv,steady_start_s,steady_end_s,notes
```

Use `HEAT`/`COOL`; `pwm` is the exact integer **magnitude** sent to the Arduino. The revised Part 4 graph converts COOL to **negative signed x**, HEAT to positive signed x; do not put negative PWM in this raw summary column. `source_csv` is a path relative to the repository root, e.g. `data/module_04/<actual-filename>.csv`. Times are the Arduino `time_s` values in that source file. `steady_start_s` and `steady_end_s` bound the actual steady interval. Never enter blank/estimated temperatures as measured values. The [plot script](../../Module_4/python/plot_a2.py) checks the schema and creates three figures from completed data; only the signed-PWM response graph is required in the revised A2 PDF, while the time traces remain retained class evidence.
