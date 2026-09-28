# Module 4 open-loop TEC: live lab record

Team: Ricky Huang and Xavier Zhu. Course: Phys 39, Module 4. Use this file as the **single live measurement table**. For today's ordered, click-by-click checkboxes, use the [2026-09-28 lab-day runbook](module_04_lab_day_runbook_2026-09-28.md). Check a box only after observing the result and recording its evidence; an agent may edit it in VS Code, but must not infer a physical check from code alone.

## What is already evidenced (not the Part 3 calibration)

- The current [Arduino sketch](../../Module_4/arudino/part_1/part_1.ino) averages 1000 thermistor ADC readings. It has a 60 °C software safety constant and additional 10–45 °C operating guards. D9 is HEAT; D10 is COOL. The [Python GUI](../../Module_4/python/part_5_tec_control_gui.py) records serial temperature, command, safety state and firmware-reported output PWM.
- The [Part 1 safety record](../../Module_4/part_1_safety_check.md) documents the TEC-power-off test with a temporary 20 °C threshold: commanded HEAT and COOL were rejected, both firmware PWM values stayed at 0, and serial reporting continued. It also documents restoring 60 °C. A later instructor-present 30 °C test recorded shutdown after the temperature crossed 30 °C. Neither record independently measured D9/D10 voltage.
- The [low-PWM cooling check](../../Module_4/cooling_direction_test.md) supports the COOL mapping. The six older [Module 4 GUI CSV files](../../Module_4/data/) are exploratory/safety records, **not** ten steady-state calibration points. In particular, do not import them into the table below merely because a file exists. The 10 °C and 45 °C boundaries have not been physically challenged.
- The [Module 3 instrument note](module_03_tec_gui.md) records an earlier 12 V setting, 18 AWG high-current wiring, series thermal switch, and instructor check. Record the actual Module 4 supply voltage, current limit, and reinspection here; do not assume they were unchanged. The revised A2 PDF focuses on analysis and no longer repeats apparatus/safety documentation.

## Settings to write down before the first new run

| Setting | Actual value / observation | Evidence or person who checked |
| --- | --- | --- |
| Lab date and operator(s) | 待填 | |
| Arduino sketch version / commit | `Module_4/arudino/part_1/part_1.ino` — verify actual upload | |
| Python GUI version / commit | `Module_4/python/part_5_tec_control_gui.py` — fresh run started 2026-09-28; commit not recorded | Program startup output |
| Board, port, baud | Arduino Uno (prior record); `/dev/cu.usbmodem101`; 9600 baud | Fresh GUI serial connection 2026-09-28 |
| Power-supply voltage | 待实测 / 待记录 | |
| Power-supply current limit | 待实测 / 待记录 | |
| Thermistor plausibility at PWM 0 | 23.80 °C at fresh GUI startup | `Module_4/data/module_04_tec_20260928_095700_881845.csv`; PWM 0, Safety OK, firmware outputs 0/0 |
| Maximum useful HEAT PWM | 待探索，整数 0–255 | |
| Maximum useful COOL PWM | 待探索，整数 0–255 | |
| Operational steady-state criterion | **待决定并写成可重复规则**；老师没有给固定秒数/阈值 | |

## Ten formal measurements — fill only from new supervised runs

After Part 2, replace the four `待定` PWM values in each direction with the exact integers closest to 25%, 50%, 75%, and 100% of **that direction's own** chosen maximum. For each row, record the temperature immediately before the PWM change, the eventual steady temperature, elapsed wait, a short observation, the new raw CSV filename, and the chosen steady window. PWM 0 is a real baseline measurement for each direction, not a zero-degree point. A second baseline may share a continuous run only if its direction/state and timing are unambiguous; record the provenance explicitly.

| ID | Direction | PWM magnitude (0–255) | Start T (°C) | Steady T (°C) | Wait (s) | Notes / current | Raw CSV + steady window (s) |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| H0 | HEAT | 0 | 待填 | 待填 | 待填 | 待填 | 待填 |
| H1 | HEAT | 待定≈25% HEAT max | 待填 | 待填 | 待填 | 待填 | 待填 |
| H2 | HEAT | 待定≈50% HEAT max | 待填 | 待填 | 待填 | 待填 | 待填 |
| H3 | HEAT | 待定≈75% HEAT max | 待填 | 待填 | 待填 | 待填 | 待填 |
| H4 | HEAT | 待定=HEAT max | 待填 | 待填 | 待填 | 待填 | 待填 |
| C0 | COOL | 0 | 待填 | 待填 | 待填 | 待填 | 待填 |
| C1 | COOL | 待定≈25% COOL max | 待填 | 待填 | 待填 | 待填 | 待填 |
| C2 | COOL | 待定≈50% COOL max | 待填 | 待填 | 待填 | 待填 | 待填 |
| C3 | COOL | 待定≈75% COOL max | 待填 | 待填 | 待填 | 待填 | 待填 |
| C4 | COOL | 待定=COOL max | 待填 | 待填 | 待填 | 待填 | 待填 |

## Current-session exploratory runs — not formal points

- 2026-09-28 fresh CSV `Module_4/data/module_04_tec_20260928_095700_881845.csv`: operator identifies HEAT PWM 55 as an exploratory test. It begins at Arduino `11.68 s`, `23.77 °C`. At the last checked row (`84.89 s`), PWM is still 55, temperature is `40.83 °C`, `Safety=OK`, and no steady-state conclusion is recorded. Update the end time and final status after the operator changes settings or closes the run. Do not place this segment in H0–H4.

## Reference checklist (use the lab-day runbook for live checkboxes)

### A. Before actuator power (Part 1 recheck)

- [ ] Confirm the TEC actuator supply is OFF/disconnected while inspecting wiring and uploading code; Arduino USB power alone is okay. Record who confirmed this.
- [ ] Inspect **every high-current connection** for 18 AWG stranded copper: supply → H-bridge B+/B−, bridge M+/M− → TEC path, and both thermal-switch leads. Confirm polarity and secure spade crimps; note any repair.
- [ ] With the circuit unpowered, confirm multimeter continuity through the normally closed thermal switch and verify it is in series with TEC current, so it can interrupt current independently of Arduino. Keep/record instructor approval of the actual wiring diagram; diagram updating is intentionally deferred today.
- [ ] Confirm H-bridge output direction tests from Module 3 are available. Upload the intended Arduino sketch and launch the intended GUI; record exact filenames/version, serial port, 9600 baud.
- [ ] At startup, read **both** firmware-reported heat/cool outputs as 0, commanded PWM as 0, `Safety: OK`, and a plausible room temperature. If not, stop and diagnose before power.
- [ ] Verify the 60 °C software constant is restored in the *uploaded* code. Review the existing 20 °C TEC-power-off shutdown and restoration evidence with the instructor; repeat a supervised power-off safety test only if the instructor requires it. Do not deliberately heat to 60 °C.
- [ ] Record what is and is not verified: serial evidence confirms firmware-reported outputs and continuing reports; actual pin voltages need separate instructor-approved measurement if claimed.
- [ ] Record the instructor-approved **Module 4** supply voltage and current limit; obtain instructor approval before enabling actuator power.

### B. Start-up and exploratory PWM choice (Part 2)

- [ ] Reconfirm PWM 0 and plausible live temperature, then enable the supply at the approved voltage/current limit while supervised.
- [ ] At low nonzero HEAT PWM, confirm temperature rises; at low nonzero COOL PWM, confirm temperature falls. Confirm GUI PWM color is red for HEAT, blue for COOL. If either direction is wrong or unclear, return PWM to 0 and stop.
- [ ] For HEAT, cautiously increase PWM while watching temperature **and supply current**; stop before 45 °C. Record the maximum useful HEAT integer PWM and reason it was selected.
- [ ] For COOL, repeat separately while watching temperature and supply current; stop before 10 °C. Record the maximum useful COOL integer PWM and reason it was selected.
- [ ] Calculate and write exact integer levels 0, about 25/50/75%, and max for **each** direction in the ten-row table. Confirm all intended points remain within 10–45 °C; maxima need not match.
- [ ] Agree with the instructor/partner on a reproducible steady-state criterion and write it in the settings table **before** labelling any point steady. Record window length and how slow the change must be; do not invent the rule after seeing the graph.

### C. Collect all ten steady-state points (Part 3)

- [ ] For H0–H4, at each setting record direction and exact PWM, start T, time of command, steady T, wait time, notes/current, raw CSV path, and steady averaging window. Check one row only after its data and raw trace are preserved.
- [ ] For C0–C4, record the same fields. Treat each 0-PWM baseline explicitly; do not copy a 0 point across directions without a clear shared-run explanation.
- [ ] Throughout every run, keep measured T in 10–45 °C and watch display updates, supply current, TEC, and H-bridge. On unexpected temperature, frozen display, excess current, or hot hardware: set PWM 0 / disable actuator power, alert the instructor, and document the interruption. Never leave a powered run unattended.
- [ ] Save at least one complete HEAT temperature-vs-time trace and one complete COOL trace, including the command transition and steady window. Ensure the labels and units can be reconstructed from the raw file.
- [ ] Before leaving class, check that **all ten** rows have genuine measurements and filenames, that every referenced raw file opens, and that any bad run/repeat is identified without deleting the original. If missing, ask for a supervised repeat now or at the next supervised opportunity.
- [ ] Return command PWM to 0; verify both output reports are 0; switch off the actuator supply. Record any instructor sign-off and physical anomalies.

### D. Analysis and A2 handoff (Parts 4–6; after class)

- [ ] Place **selected formal** raw time-series files in [`data/module_04/`](../../data/module_04/) with an unambiguous provenance note. Keep older exploratory files in `Module_4/data/`; do not silently mix them with calibration data or commit redundant copies.
- [ ] Create/review one labeled heating trace, one labeled cooling trace, and the red/blue steady-T-vs-**signed PWM** graph in [`docs/figures/module_04/`](../figures/module_04/). Negative x is COOL; positive x is HEAT. Add fitted lines over stated approximately linear ranges, labeled axes/units, and the actual steady criterion.
- [ ] Calculate HEAT and COOL χ_T in °C per PWM count from the stated linear ranges; report `r=m_h/|m_c|` and any visible curvature. Keep the 10–45 °C operating restriction explicit.
- [ ] Complete the revised [A2 analysis draft](../assessments/a2_open_loop_tec.md): PWM averaging proof, steady-state energy balance and ratio derivation, independently located Laird maximum-current values at hot-side 27 °C, comparison, passive-conduction explanation, and 100–150-word conclusion. The PDF is 1–2 pages; do not insert old circuit/safety/code sections.
- [ ] Review generated PDF for fitted lines and readable units. Save as `A2_Huang_Zhu.pdf` **if these are the desired surname order**; each student uploads the same team PDF separately to Moodle by Monday 2026-10-05 6:00 PM.
- [ ] Retain raw class data and working code. The revised assignment requires **no new Git checkpoint or repository A2 file** for this short submission; versioning the work remains optional.

## VS Code agent operating rule

When assisting live: read this checklist and the newest raw CSV; update only boxes whose evidence is directly visible in files/instruments or explicitly reported by the operator/instructor, write the evidence beside the item or in the table, and leave all other boxes open. Ask the human before any powered test or change to safety limits. Do not autonomously run the physical apparatus unattended.
