# Module 4 lab-day checklist (2026-09-28; updated for the revised instructions)

**Start at Step 0 when using this historical checklist.** The [ten-row measurement record](module_04_open_loop_tec.md) holds the actual data, and the [A2 analysis draft](../assessments/a2_open_loop_tec.md) is post-lab work; a repository draft is not the required submission. The instructor had already seen the earlier Part 1 demonstration. Recheck the setup before applying power, but do not independently repeat the 20/30/60 °C safety tests. Physical runs and safety tests belong in class, with measurements normally within **10–45 °C**. Do not intentionally heat to 60 °C.

> **Stop condition:** If temperature moves in the wrong direction, approaches either 10/45 °C boundary, the display or serial stream freezes, supply current rises unexpectedly, or the TEC, H-bridge, or heat exchanger becomes unusually hot or smells abnormal, enter `0` in the GUI, verify firmware outputs `0/0`, turn off actuator power, and tell the instructor. If the GUI or serial link fails, turn off actuator power directly rather than waiting for software. Do not leave the powered apparatus unattended or touch live terminals or hot components.

## 0. At the bench, before actuator power

- [ ] Open this repository and checklist in VS Code together with the [ten-row record](module_04_open_loop_tec.md). Check a box only after observing the step and recording its value or file. Date, operators, instructor: ________.
- [ ] Confirm the TEC actuator supply is **OFF** and its output disabled; the Arduino may be powered by USB. Do not energize the TEC simply to see whether it responds.
- [ ] Confirm the intended programs are the [Module 4 Arduino sketch](../../Module_4/arudino/part_1/part_1.ino) and [Module 4 Python GUI](../../Module_4/python/part_5_tec_control_gui.py), not the Module 3 versions. Current source settings are a `60 °C` firmware upper limit (the former 10–45 °C firmware guards were removed), HEAT on `D9`, COOL on `D10`, and `9600` baud. Still observe the course's separate operating range. Actual uploaded version/commit: ________.

## 1. Check wiring with power off; wait for instructor approval

The Module 3 **physical wiring record** describes the following path. This is a verification aid, not an instruction to rewire a live circuit. If labels or the actual apparatus differ, stop and ask the instructor. The high-current supply-to-bridge-to-TEC/switch leads were recorded as **18 AWG stranded copper**, with two crimped female spade terminals at the thermal switch.

```text
High-current supply V+ --18 AWG--> H-bridge B+
High-current supply V- --18 AWG--> H-bridge B-

H-bridge M+ --18 AWG--> thermal switch --18 AWG--> TEC+
H-bridge M- --18 AWG-----------------------------> TEC-
                 (thermal switch in series with TEC current)

Arduino 5 V --> H-bridge VCC, R_EN, L_EN (both enables HIGH)
Arduino GND --> H-bridge logic GND (common ground)
Arduino D9 --> H-bridge RPWM (team HEAT direction)
Arduino D10 --> H-bridge LPWM (team COOL direction)

Thermistor divider: Arduino 5 V --> 100 kOhm fixed resistor --> A0
                                                      A0 --> 100 kOhm NTC --> GND
```

The TEC must **not** connect directly to Arduino D9/D10; those pins drive H-bridge logic. The thermal switch must interrupt TEC current independently of software. The earlier [HEAT](../../Module_4/figures/part_1_heating_high_current.png) and [COOL](../../Module_4/figures/part_1_cooling_high_current.png) drawings show the switch on the other side of the TEC and depict it open. They are retained as historical illustrations, **not verified as-built wiring evidence**. Record the actual series path with the instructor; the revised A2 does not request a circuit diagram. Connect and run the heat-exchanger pump and fans as approved before applying nonzero TEC PWM.

- [ ] Trace `V+→B+`, `V−→B−`, `M+→thermal switch→TEC+`, and `TEC−→M−` against actual labels. Check 18 AWG wire, polarity, secure connections, and absence of exposed shorts. A switch on the other side of the TEC can still be in series; record the real path and ask the instructor rather than moving wires to match text. Actual path: ________.
- [ ] With power **off**, use a multimeter to confirm continuity through the normally closed thermal switch and inspect both spade crimps. Reading/instructor confirmation: ________. Do not measure continuity on a powered circuit.
- [ ] Check the physical Arduino `5 V/GND/D9/D10/A0` connections to bridge `VCC/GND/R_EN/L_EN/RPWM/LPWM`, the divider, and the TEC. The two directional PWM inputs must not be active simultaneously. Inspect heat-exchanger power but do not yet run the TEC.
- [ ] Draw the **actual full high-current path** in the lab notebook and show it and the apparatus to the instructor for wire gauge, polarity, switch series placement and continuity, crimps, and supply current-limit review. Instructor/time: ________. **Do not proceed to Step 3 without this approval.**

## 2. Arduino and GUI startup at zero actuator power

- [ ] Open `Module_4/arudino/part_1/part_1.ino` in Arduino IDE; choose **Arduino Uno** and the actual port, Verify, then Upload. Do not revert to the temporary 20/30 °C test version. Close Serial Monitor/Plotter after uploading so the GUI can use the port. Port: ________.
- [x] Check that the GUI's `SERIAL_PORT` matches the actual port (repository setting: `/dev/cu.usbmodem101`); change it only if necessary. From the repository root run `.venv/bin/python Module_4/python/part_5_tec_control_gui.py`. On a different computer, first install `requirements.txt` into the appropriate environment. The GUI sends `PWM 0` at startup and creates a timestamped CSV in `Module_4/data/`. The recorded CSV for this session is `Module_4/data/module_04_tec_20260928_095700_881845.csv`.
- [x] Earlier-version startup record: temperature and Arduino time updated about every 0.5 s; initial temperature was about `23.80 °C`, `Safety OK`, PWM outputs `0/0`. That CSV reported limits `60/10/45` and **does not prove** that the newer 60 °C-only sketch was uploaded.
- [ ] For the newer version, verify `Safety=OK`, `Heat PWM=0`, `Cool PWM=0`, and `Limit (C)=60.00` in the GUI/new CSV. Confirm that the new CSV no longer has `low_limit_C` or `operating_high_C` columns. New filename: ________.
- [ ] Show the instructor the [existing Part 1 safety evidence](../../Module_4/check/part_1_safety_check.md): the 20 °C power-off demonstration, restoration to 60 °C, and the supervised 30 °C demonstration. Repeat a power-off test only if the instructor asks; do not intentionally heat to 60 °C. Firmware-reported `0/0` is not an independent voltage measurement at D9/D10.

## 3. After approval, enable power and select the ten Part 2 PWM values

- [x] Confirm GUI PWM is still `0`, temperature is plausible, and the instructor approved this Module 4 supply setup. The [lab record](module_04_open_loop_tec.md#settings-to-write-down-before-the-first-new-run) lists **12 V** and a **10 A current limit** as the reported initial settings; the instructor said they did not need to be rewritten at every step.
- [ ] Enable the supply as approved while GUI PWM remains `0`. Verify the heat-exchanger pump and fans are running and supply current is normal before applying nonzero TEC PWM. Displayed current at PWM 0: ________ A.
- [ ] At `PWM command=0`, select the red `HEAT` direction. Enter an instructor-approved low value in the PWM text box and apply it with Enter or by leaving the field. A value such as 10 is only a historical exploratory example, not a required or inherently safe setting. Observe rising temperature, the red PWM trace, and supply current. Record values and observations: ________. Then enter `0` and confirm outputs `0/0`.
- [ ] At PWM 0, select blue `COOL` (the GUI also resets PWM on a direction change; verify zero yourself). Briefly test at an instructor-approved low value. Observe falling temperature, the blue PWM trace, and supply current. Record: ________. Return to `0`. If direction is wrong, stop and ask the instructor to inspect wiring/calibration.
- [x] Maximum-level exploration selected `Hmax=45` (operator reported about 45 ± 0.3 °C; raw HEAT-45 segment 45.31–45.45 °C) and `Cmax=96` (reported near 10 °C; raw COOL-96 segment 9.83–10.17 °C). The operator accepted small boundary fluctuations; this records the selection, not a blanket interpretation of the 10–45 °C course range.
- [x] Exact integer levels entered in the ten-row record: HEAT `[0, 11, 23, 34, 45]` (the half-level rounded to 23) and COOL `[0, 24, 48, 72, 96]`. Each direction has four distinct nonzero values.
- [x] The operator's original on-site steady rule was that temperature stopped changing persistently in one direction and fluctuated within a band. The last ~20 s were averaged; no fixed amplitude or slope threshold was specified or attributed to the instructor. **This older rule is superseded by the later 3τ-plus-minute requirement.**

## 4. Part 3: H0–H4 and C0–C4 measurements

For each row: record start temperature and Arduino time **before** changing PWM; apply the selected integer PWM and note its effective command time; observe temperature and program state; record the selected temperature window, mean, wait, notes, and CSV filename; then inspect the CSV for correct direction, PWM, temperature, and firmware outputs. Supply current is not a required column in the steady-state table. The original 20-second window alone does **not** establish compliance with the revised steady-state criterion.

- [x] `H0`: HEAT PWM-0 baseline, final-window mean **23.44 °C** at 5.10–24.82 s. Capture began after the block was near room temperature; the earlier wait was not recorded. See the [ten-row record](module_04_open_loop_tec.md).
- [x] `H1`: HEAT PWM 11, 218.12–237.97 s, mean **28.31 °C**.
- [x] `H2`: HEAT PWM 23, 402.29–422.14 s, mean **34.62 °C**. Three earlier PWM-233 rows are flagged as an anomaly outside the selected window; the raw file is retained unchanged.
- [x] `H3`: HEAT PWM 34, 519.31–539.16 s, mean **40.42 °C**.
- [x] `H4`: Operator selected the final ~20 s of HEAT PWM 45 in the maximum-search CSV, mean **45.37 °C**. All 40 selected samples exceed the course's 45 °C upper boundary. The raw trace and exception remain documented; the instructor accepted this exception on 2026-09-28.
- [x] `C0`: COOL PWM-0 baseline, final-window mean **23.44 °C** at 2.08–21.78 s. The return-to-room-temperature interval is outside this CSV, so its wait is unknown.
- [x] `C1`: COOL PWM 24, 408.97–428.82 s, mean **20.44 °C**.
- [x] `C2`: COOL PWM 48, 358.90–378.75 s, mean **16.99 °C**.
- [x] `C3`: COOL PWM 72, 336.72–356.57 s, mean **13.40 °C**.
- [x] `C4`: Operator selected the final ~20 s of COOL PWM 96 in the maximum-search CSV, mean **9.99 °C**. Of 40 selected samples, 21 fall below the course's 10 °C lower boundary. The raw trace and exception remain documented; the instructor accepted this exception on 2026-09-28.

The normal course measurement range remains **10–45 °C**. A window interrupted by safety shutdown, carrying the wrong direction/PWM, or not genuinely steady cannot be treated as a formal point. H4/C4 are explicit instructor-accepted range exceptions and must still be described truthfully in analysis or submission. Their range exceptions do not waive the revised steady-state timing evidence.

## 5. Before leaving the bench

- [ ] Enter `0` in the GUI and confirm both firmware-reported HEAT and COOL outputs are `0` in the newest serial/CSV line. Turn off actuator power, finish the heat-exchanger shutdown as directed, and then close the GUI. Do not normally stop by pulling USB while PWM is nonzero.
- [ ] Open the newest CSV and confirm it has data beyond the header. Check that the ten-row record has actual values, waits where captured, source filenames, and temperature windows, plus at least one HEAT and one COOL time trace. Ask the instructor about missing or anomalous runs while still in class.
- [ ] Show the instructor the record, raw files, actual supply voltage/current limit, wiring, and both directional responses. Record requested changes: ________. Preserve the identity of exploratory and safety CSVs; do not mix them into the formal ten points.

## 6. A2 after class (revised deadline: Monday, 2026-10-05 at 18:00)

The revised course page estimated about **1 h 30 min** of out-of-class work: preparation/boundaries 30 min, plots/slopes 15 min, heat-balance analysis 30 min, and review/submission 15 min. If measurements need repeating, wait for the next supervised lab rather than operating the apparatus at home.

- [ ] Revalidate the [ten-row table](../../Module_4/data/steady_state.csv) against the updated protocol and run the [plotting script](../../Module_4/python/plot_a2.py). Check HEAT/COOL traces and the main plot (**negative signed PWM = COOL; positive = HEAT**). Fit suitable near-linear intervals on each side and label ranges, slope units, and the actual accepted steady criterion.
- [ ] Calculate `m_h`, `m_c` (°C/PWM count) and `r=m_h/|m_c|`, noting fit ranges and curvature. Prove the PWM-period averages `⟨I⟩=DI` and `⟨I²⟩=DI²`; the latter is **not** `(DI)²`.
- [ ] Use the course steady-state energy balance to relate `r` to Peltier and Joule heat rates. TEC conduction is already included in effective `G`; do not count it twice. See the [A2 analysis draft](../assessments/a2_open_loop_tec.md).
- [ ] Independently locate `R_M`, `I_max`, `Q_c,max` at ΔT=0, and `ΔT_max` in the Laird CP14-127-045 table for a **27 °C hot side**; record units and conditions. Then calculate the manufacturer's maximum-current heat-rate and slope-ratio prediction. Do not assume PWM duty `D=1` implies actual current `I_max`.
- [ ] Compare measured and manufacturer ratios; explain differences, the direction of passive heat transfer above/below room temperature, and why approximately symmetric passive conduction alone does not explain the unequal branch slopes. Write a conclusion of about 100–150 English words.
- [ ] Produce a **1–2-page PDF** with only the revised required graph (including fit lines), slopes/ratio, derivations, condition-labelled Laird values and calculation, comparison/conduction explanation, and conclusion. Do not repeat C2/C3 wiring sketches, apparatus description, safety demonstration, or code documentation. Name it `A2_Lastname_Lastname.pdf`; **each teammate uploads the same PDF separately**. No new repository document or Git checkpoint is required for A2, but retain lab data and code.

## VS Code agent instructions for a live session

> Read `docs/module_notes/module_04_lab_day_runbook_2026-09-28.md` and `docs/module_notes/module_04_open_loop_tec.md` first. Advance one unfinished step at a time. Verify code and CSV facts directly, but ask the operator to confirm wiring, instrument readings, instructor approval, and apparatus state in person. After each completed step, record the value and evidence, check its box, and state the next exact control or reading. Do not independently rewire, energize the TEC, raise PWM, change safety thresholds, or leave a powered run unattended. If anything goes wrong, have the operator turn off actuator power and notify the instructor. Do not treat exploratory/safety CSVs as formal steady-state points.

References: [Module 4 course page](https://sethfraden.github.io/Phys39F26-course/labs/lab-04/) · [course hardware page](https://sethfraden.github.io/Phys39F26-course/hardware/) · [team Module 3 wiring record](module_03_tec_gui.md).
