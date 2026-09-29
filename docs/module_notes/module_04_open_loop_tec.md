# Module 4 open-loop TEC: live lab record

Team: Ricky Huang and Xavier Zhu. Course: Phys 39, Module 4. Use this file as the **single live measurement table**. For today's ordered, click-by-click checkboxes, use the [2026-09-28 lab-day runbook](module_04_lab_day_runbook_2026-09-28.md). Check a box only after observing the result and recording its evidence; an agent may edit it in VS Code, but must not infer a physical check from code alone.

## What is already evidenced (not the Part 3 calibration)

- The current [Arduino sketch](../../Module_4/arudino/part_1/part_1.ino) averages 1000 thermistor ADC readings. Its current source stops at 60 °C or an invalid sensor reading; the earlier 10–45 °C firmware guards have been removed. Verify which version was actually uploaded. D9 is HEAT; D10 is COOL. The [Python GUI](../../Module_4/python/part_5_tec_control_gui.py) records serial temperature, command, safety state and firmware-reported output PWM.
- The [Part 1 safety record](../../Module_4/part_1_safety_check.md) documents the TEC-power-off test with a temporary 20 °C threshold: commanded HEAT and COOL were rejected, both firmware PWM values stayed at 0, and serial reporting continued. It also documents restoring 60 °C. A later instructor-present 30 °C test recorded shutdown after the temperature crossed 30 °C. Neither record independently measured D9/D10 voltage.
- The [low-PWM cooling check](../../Module_4/cooling_direction_test.md) supports the COOL mapping. The six older [Module 4 GUI CSV files](../../Module_4/data/) are exploratory/safety records, **not** ten steady-state calibration points. In particular, do not import them into the table below merely because a file exists. The 10 °C and 45 °C boundaries have not been physically challenged.
- The professor's [Module 4 instructions as checked 2026-09-28](https://sethfraden.github.io/Phys39F26-course/labs/lab-04/) now define Part 3 steady state by estimating the step-response time constant, waiting about three time constants, then observing one additional minute with net drift no greater than ordinary short-term noise. The ten-row table below predates this rule and is **provisional**, not a claim that all ten points meet the current protocol.
- The [Module 3 instrument note](module_03_tec_gui.md) records an earlier 12 V setting, 18 AWG high-current wiring, series thermal switch, and instructor check. Record the actual Module 4 supply voltage, current limit, and reinspection here; do not assume they were unchanged. The revised A2 PDF focuses on analysis and no longer repeats apparatus/safety documentation.

## Settings to write down before the first new run

| Setting | Actual value / observation | Evidence or person who checked |
| --- | --- | --- |
| Lab date and operator(s) | 2026-09-28, Ricky Huang and Xavier Zhu | |
| Arduino sketch version / commit | `Module_4/arudino/part_1/part_1.ino` — verify actual upload | |
| Python GUI version / commit | `Module_4/python/part_5_tec_control_gui.py` — fresh run started 2026-09-28; commit not recorded | Program startup output |
| Board, port, baud | Arduino Uno (prior record); `/dev/cu.usbmodem101`; 9600 baud | Fresh GUI serial connection 2026-09-28 |
| Power-supply voltage | **12 V**（原始设定，记录一次即可） | 操作者 2026-09-28 报告；老师表示无需逐步记录 |
| Power-supply current limit | **10 A**（原始设定，记录一次即可） | 操作者 2026-09-28 报告；老师表示无需逐步记录 |
| Thermistor plausibility at PWM 0 | 23.80 °C at fresh GUI startup | `Module_4/data/module_04_tec_20260928_095700_881845.csv`; PWM 0, Safety OK, firmware outputs 0/0 |
| Maximum useful HEAT PWM | **45**（操作者选定；报告约 45 °C、波动约 0.3 °C） | 2026-09-28 操作者报告；`Module_4/data/module_04_heating_max_pwm45_20260928_100550_571289.csv` 中 HEAT 45 的较长一段为 192.67–240.51 s、45.31–45.45 °C |
| Maximum useful COOL PWM | **96**（操作者选定；报告约 10 °C 稳定） | 2026-09-28 操作者报告；`Module_4/data/module_04_cooling_max_pwm96_20260928_101439_464642.csv` 中 COOL 96 片段为 461.52–488.47 s、9.83–10.17 °C |
| Original operational steady-state criterion (superseded) | 操作者当时依据温度不再持续单向变化、在局部区间波动判断稳态，并以末约 20 s 均值记录。此标准**不再足以证明**符合教授现行的约 3τ＋额外 1 分钟判据。H4/C4 的课程 10–45 °C 范围例外仍单独标注。 | 操作者 2026-09-28 确认；教授网页随后更新 |

## Revised steady-state protocol audit

The following is a retrospective **screen**, not an instructor sign-off. For nonzero PWM, `τ` is estimated as the time from the first sample of the final constant-command segment to the first sample reaching 63.2% of the change from that sample to the mean of the segment's last 40 samples. This rough estimate is unreliable if a segment starts very near its final temperature (especially H4/C4). The last-minute net drift below compares the mean of the first 10 seconds of that minute with the mean of the last 10 seconds; it is not yet an agreed quantitative noise threshold. The raw CSVs and original selected values remain unchanged.

| Run | Final constant-PWM segment (s) | Rough τ (s) | Last-minute drift (°C) | Current assessment |
| --- | ---: | ---: | ---: | --- |
| H0 | 23 | not estimable (no meaningful step) | unavailable | Needs a ≥60 s zero-PWM observation; prior room-temperature wait is undocumented. |
| H1 | 230 | 69 | +0.33 | Ends before about `3τ+60 ≈ 266 s` and still drifts; repeat/extend. |
| H2 | 395 | 61 | +0.04 | Has enough duration; review the trace and ordinary noise with instructor. |
| H3 | 500 | 73 | +0.06 | Has enough duration; review the trace and ordinary noise with instructor. |
| H4 | 48 | not reliable (began near final T) | unavailable | Needs a ≥60 s PWM-45 observation after settling; current segment too short. |
| C0 | 21 | not estimable (no meaningful step) | unavailable | Needs a ≥60 s zero-PWM observation; prior room-temperature wait is undocumented. |
| C1 | 424 | 76 | −0.08 | Has enough duration; review the trace and ordinary noise with instructor. |
| C2 | 331 | 66 | −0.12 | Has enough duration but visible net drift may exceed ordinary wiggles; review/extend. |
| C3 | 353 | 61 | −0.05 | Has enough duration; review the trace and ordinary noise with instructor. |
| C4 | 27 | not reliable (began near final T) | unavailable | Needs a ≥60 s PWM-96 observation after settling; current segment too short. |

At minimum, H0, H1, H4, C0, and C4 require new or extended supervised recordings to **document** the revised criterion. H2/H3/C1/C2/C3 are candidates for retrospective acceptance only after checking their post-3τ one-minute intervals against ordinary short-term noise, with C2 especially questionable. Reuse of the maximum-search endpoint temperatures and their instructor-approved range exceptions does not substitute for the new one-minute steady-state evidence. Do not replace the Part 4 graph's provisional values silently; if repeats change values, update `steady_state.csv`, regenerate figures, and recompute Part 5.

## Ten selected measurements — traceable to supervised raw CSVs

The chosen integer levels are 0/11/23/34/45 for HEAT and 0/24/48/72/96 for COOL. For each row, record the temperature immediately before the PWM change when available, the eventual steady temperature, elapsed wait when recorded, a short observation, the raw CSV filename, and the chosen steady window. PWM 0 is a real baseline measurement for each direction, not a zero-degree point. The two baseline CSVs begin after the operator reported the block had returned to room temperature, so the earlier warm-up wait cannot be reconstructed. On 2026-09-28 the operator chose to **adopt H4/C4** from the maximum-search CSVs as measurement points despite their selected windows extending outside the course's 10–45 °C range. The instructor accepted this course-range exception on 2026-09-28.

| ID | Direction | PWM magnitude (0–255) | Start T (°C) | Steady T (°C) | Wait (s) | Notes | Raw CSV + steady window (s) |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| H0 | HEAT | 0 | 23.40（切换到 HEAT 前） | 23.44 | 未记录（采集前已接近常温） | HEAT 方向、PWM 0；末约 20 s 的 40 行为 23.39–23.51 °C，固件输出 0/0，`Safety=OK` | `Module_4/data/module_04_heating_0pct_pwm0_20260928_112039_906848.csv`；5.10–24.82 |
| H1 | HEAT | 11（约 25% × 45） | 21.89 | 28.31 | 约 210（至窗口开始） | 操作者报告约 28.3 °C 稳定；末约 20 s 的 40 行均 `Safety=OK`、固件 HEAT PWM=11 | `Module_4/data/module_04_heating_25pct_pwm11_20260928_102552_858326.csv`；218.12–237.97 |
| H2 | HEAT | 23（约 50% × 45） | 25.38（设 23 前一行；此前短暂 PWM 233） | 34.62 | 约 375（至窗口开始） | 末约 20 s 的 40 行为 34.55–34.67 °C、`Safety=OK`、固件 HEAT PWM=23；此前有 3 行 PWM 233，原始异常保留，不属于所选稳态窗口 | `Module_4/data/module_04_heating_50pct_pwm23_20260928_103051_243607.csv`；402.29–422.14 |
| H3 | HEAT | 34（约 75% × 45） | 25.12 | 40.42 | 约 480（至窗口开始） | 末约 20 s 的 40 行为 40.33–40.50 °C、`Safety=OK`、固件 HEAT PWM=34 | `Module_4/data/module_04_heating_75pct_pwm34_20260928_103941_134734.csv`；519.31–539.16 |
| H4 | HEAT | 45（HEAT max） | 45.44（从 PWM 47 切到 45 前） | 45.37（操作者采用；超出上界） | 约 28（至窗口开始） | 最大值探索文件的最后一个 HEAT 45 段；末约 20 s 的 40 行均为 45.31–45.41 °C、全部高于 45 °C；固件输出 45/0，`Safety=OK`。如实标注为课程范围例外；老师 2026-09-28 已接受。 | `Module_4/data/module_04_heating_max_pwm45_20260928_100550_571289.csv`；220.66–240.51 |
| C0 | COOL | 0 | 23.43（CSV 首行） | 23.44 | 未记录（回温过程不在此 CSV） | COOL 方向、PWM 0；末约 20 s 的 40 行为 23.33–23.54 °C，固件输出 0/0，`Safety=OK` | `Module_4/data/module_04_cooling_0pct_pwm0_20260928_112013_141346.csv`；2.08–21.78 |
| C1 | COOL | 24（25% × 96） | 29.33 | 20.44 | 约 404（至窗口开始） | 末约 20 s 的 40 行为 20.40–20.50 °C、`Safety=OK`、固件 COOL PWM=24 | `Module_4/data/module_04_cooling_25pct_pwm24_20260928_104957_896611.csv`；408.97–428.82 |
| C2 | COOL | 48（50% × 96） | 22.64 | 16.99 | 约 311（至窗口开始） | 末约 20 s 的 40 行为 16.87–17.12 °C、`Safety=OK`、固件 COOL PWM=48 | `Module_4/data/module_04_cooling_50pct_pwm48_20260928_105744_249371.csv`；358.90–378.75 |
| C3 | COOL | 72（75% × 96） | 17.39 | 13.40 | 约 333（至窗口开始） | 末约 20 s 的 40 行为 13.37–13.44 °C、`Safety=OK`、固件 COOL PWM=72 | `Module_4/data/module_04_cooling_75pct_pwm72_20260928_110449_677478.csv`；336.72–356.57 |
| C4 | COOL | 96（COOL max） | 9.82（从 PWM 98 切到 96 前） | 9.99（操作者采用；部分低于下界） | 约 7（至窗口开始） | 最大值探索文件的最后一个 COOL 96 段；末约 20 s 的 40 行为 9.85–10.17 °C，其中 21 行低于 10 °C；固件输出 0/96，`Safety=OK`。如实标注为课程范围例外；老师 2026-09-28 已接受。 | `Module_4/data/module_04_cooling_max_pwm96_20260928_101439_464642.csv`；468.64–488.47 |

## Current-session exploratory files and reused H4/C4 segments

- 2026-09-28 CSV `Module_4/data/module_04_tec_20260928_095700_881845.csv`: operator identified HEAT PWM 55 as exploratory. It ran from Arduino 11.68 s (23.77 °C) through 128.54 s (44.98 °C); the older firmware reported `Safety=SHUTDOWN` at 45.02 °C and PWM 0 at 129.10 s. Do not place this segment in H0–H4.
- 2026-09-28 CSV `Module_4/data/module_04_heating_max_pwm45_20260928_100550_571289.csv`: exploratory HEAT maximum search; this file also contains PWM 55, 48 and 47, not only 45. Operator selected HEAT maximum PWM 45 and described a temperature near 45 °C with about 0.3 °C variation. The final HEAT-45 segment spans Arduino 192.67–240.51 s. H4 above uses only its last 40 records, not the earlier PWM values. The operator chose to adopt H4 while preserving the fact that all selected records exceed 45 °C; the instructor accepted this course-range exception on 2026-09-28.
- 2026-09-28 CSV `Module_4/data/module_04_cooling_max_pwm96_20260928_101439_464642.csv`: exploratory COOL maximum search; this file also contains several other COOL PWM levels. Operator selected COOL maximum PWM 96 and reported stability near 10 °C. The final COOL-96 segment spans Arduino 461.52–488.47 s. C4 above uses only its last 40 records. The operator chose to adopt C4 while preserving the fact that 21 of 40 selected records are below 10 °C; the instructor accepted this course-range exception on 2026-09-28.

## Reference checklist (use the lab-day runbook for live checkboxes)

**Current priority after the professor's revision:** Keep the original CSVs and provisional analysis, but do not check Part 3 or call A2 submission-ready yet. At the next supervised lab opportunity, review H2/H3/C1/C2/C3 traces against the new one-minute noise criterion, then collect longer H0/H1/H4/C0/C4 records (and repeat any reviewed point that still drifts). Record a documented 3τ estimate and one-minute observation for each accepted point. After that, replace only genuinely changed summary rows, regenerate the three figures, and recalculate Part 5. The Laird values and final PDF remain separate student tasks.

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

- [ ] For H0–H4, at each setting record direction and exact PWM, start T, time of command when captured, steady T, wait time when captured, notes, raw CSV path, and steady averaging window. Check one row only after its data and raw trace are preserved; flag any course-range exception explicitly.
- [ ] For C0–C4, record the same fields. Treat each 0-PWM baseline explicitly; do not copy a 0 point across directions without a clear shared-run explanation.
- [ ] Throughout every run, keep measured T in 10–45 °C and watch display updates, supply current, TEC, and H-bridge. On unexpected temperature, frozen display, excess current, or hot hardware: set PWM 0 / disable actuator power, alert the instructor, and document the interruption. Never leave a powered run unattended.
- [ ] Save at least one complete HEAT temperature-vs-time trace and one complete COOL trace, including the command transition and steady window. Ensure the labels and units can be reconstructed from the raw file.
- [ ] Before leaving class, check that **all ten** rows have genuine measurements and filenames, that every referenced raw file opens, and that any bad run/repeat is identified without deleting the original. If missing, ask for a supervised repeat now or at the next supervised opportunity.
- [ ] Return command PWM to 0; verify both output reports are 0; switch off the actuator supply. Record any instructor sign-off and physical anomalies.

### D. Analysis and A2 handoff (Parts 4–6; after class)

- [x] Create the **provisional** ten-row [`steady_state.csv`](../../data/module_04/steady_state.csv) with source-file paths and 20-second windows; retain the selected raw time series unchanged in `Module_4/data/`. Mark H4/C4 as instructor-approved course-range exceptions. Revalidate rows against the revised Part 3 rule.
- [ ] Inspect the generated heating trace, cooling trace, and red/blue steady-T-vs-**signed PWM** [figures](../../Module_4/figures/) visually before placing the main graph in A2. Files and axis labels/fits exist; this visual-review step is still open.
- [x] Calculate **provisional** HEAT and COOL χ_T from stated signed-PWM ranges: +0.4954 and +0.1414 °C/PWM count; `r=m_h/m_c=3.5035`. Recalculate after Part 3 revalidation or repeats.
- [x] In the [A2 analysis draft](../assessments/a2_open_loop_tec.md), calculate the measured slopes/ratio, derive PWM current averages and the steady-state slope relation, infer `Q̇_J/Q̇_P=0.5559` within the simplified model, and explain passive conduction. Draft a 100–150-word conclusion.
- [ ] Student: independently locate the four Laird CP14-127-045 values and their conditions in the hot-side 27 °C table, as the assignment requires before AI checks the numbers. Then calculate the manufacturer maximum-current ratio, compare it with measured `r=3.5035`, and revise the provisional conclusion. Do not equate full PWM duty with manufacturer maximum current.
- [ ] Assemble the revised A2 into a 1–2-page PDF without old circuit/safety/code sections.
- [ ] Review generated PDF for fitted lines and readable units. Save as `A2_Huang_Zhu.pdf` **if these are the desired surname order**; each student uploads the same team PDF separately to Moodle by Monday 2026-10-05 6:00 PM.
- [ ] Retain raw class data and working code. The revised assignment requires **no new Git checkpoint or repository A2 file** for this short submission; versioning the work remains optional.

## VS Code agent operating rule

When assisting live: read this checklist and the newest raw CSV; update only boxes whose evidence is directly visible in files/instruments or explicitly reported by the operator/instructor, write the evidence beside the item or in the table, and leave all other boxes open. Ask the human before any powered test or change to safety limits. Do not autonomously run the physical apparatus unattended.
