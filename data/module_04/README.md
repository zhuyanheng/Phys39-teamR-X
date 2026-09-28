# Module 4 selected steady-state data

[`steady_state.csv`](steady_state.csv) is the ten-row Part 3 summary used for the Part 4 graph. Its grain is one selected steady window per direction/PWM setting (H0–H4 and C0–C4), not one raw sensor sample. Each window contains 40 raw samples over approximately 20 seconds. The timestamped, unchanged source CSVs remain in [`Module_4/data/`](../../Module_4/data/); `source_csv` and the inclusive Arduino-time window identify the exact samples without duplicating raw files here. The [working note](../../docs/module_notes/module_04_open_loop_tec.md) records the collection history and exceptions.

The summary header is:

```text
run_id,direction,pwm,start_temperature_C,steady_temperature_C,time_waited_s,source_csv,steady_start_s,steady_end_s,range_exception_approved,notes
```

`pwm` is the nonnegative integer command magnitude; only the graph changes COOL to negative signed x. `steady_temperature_C` is the selected raw-window mean rounded to 0.01 °C. For nonzero PWM, `time_waited_s` is the elapsed time from the first sample of the final command segment to the beginning of that steady window. H0/C0 leave it blank because their earlier return-to-room-temperature wait is not in their short CSVs; the blank is unknown, not zero. `start_temperature_C` is the temperature immediately before the command change when available (C0 uses its first recorded temperature). The source and window use each raw file's Arduino `time_s` coordinate.

`range_exception_approved=yes` on H4/C4 records the instructor-approved departures from the course's 10–45 °C measurement range: every H4 window sample is above 45 °C, and 21 of 40 C4 samples are below 10 °C. These are retained as measured, not clipped or relabeled. All selected windows report `Safety=OK`, firmware PWM matching the command, and shutdown `limit_C=60`. The [plot script](../../Module_4/python/plot_a2.py) rechecks these conditions, the direction (including PWM 0), waiting-time calculation, and window means before generating the figures. Only the signed-PWM response graph belongs in the revised A2 PDF; the time traces are supporting class evidence.
