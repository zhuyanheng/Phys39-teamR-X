# Module 4 — next supervised lab recheck

This list implements the [current Part 3 instructions](https://sethfraden.github.io/Phys39F26-course/labs/lab-04/#part-3-measure-steady-state-temperature). Do not infer a pass from an existing 20-second mean. The exact connection and startup checks remain in the [main lab record](module_04_open_loop_tec.md); the GUI and Arduino source paths are listed there. Physical runs occur in class with the instructor.

## First, review existing traces together

- [ ] Show the instructor the [audit table](module_04_open_loop_tec.md#revised-steady-state-protocol-audit). Agree how to compare a one-minute net change with the ordinary short-term wiggle visible on the same trace. Record that practical comparison rule in the main lab record.
- [ ] For H2 (PWM 23), H3 (34), C1 (24), C2 (48), and C3 (72), inspect the final constant-command segment from the raw CSV. For each, mark: command time; approximately 63% response time `τ`; `3τ`; a complete **following 60-second** interval; net drift and typical wiggle; instructor/partner decision. C2 deserves extra attention because its last-minute first-to-last-ten-second change is about −0.12 °C. If the chosen interval still trends, extend/repeat the run rather than labelling it steady.

## Then capture the missing evidence

- [ ] H0, PWM 0: after the block returns near room temperature, record at least a full minute and confirm no trend larger than normal noise. Existing H0 CSV lasts only about 23 s.
- [ ] H1, HEAT PWM 11: start a new complete trace at the step, estimate `τ` while it changes, wait about `3τ`, then observe at least one further minute. Its old trace ends at about 230 s; rough `3τ+60` is about 266 s, and its last minute still rose about 0.33 °C.
- [ ] H4, HEAT PWM 45: establish the PWM-45 segment and keep recording through a complete post-settling minute. The old final PWM-45 segment is about 48 s and begins near its endpoint, so it cannot provide a trustworthy step-response `τ` on its own. Use a suitable preceding step or another interpretable response to estimate `τ`.
- [ ] C0, PWM 0: record a full minute after returning near room temperature. Existing C0 CSV lasts only about 21 s.
- [ ] C4, COOL PWM 96: establish the PWM-96 segment and keep recording through a complete post-settling minute. The old final PWM-96 segment is about 27 s and begins near its endpoint; estimate `τ` from an interpretable step, not this tiny change.
- [ ] For every accepted point, write the exact raw CSV, command time, approximate `τ`, minute-start/end times, net minute drift, usual wiggle, and selected averaging interval in the main record. Keep old files; do not replace them silently.

## Once measurements are accepted

- [ ] Update only changed rows in [`steady_state.csv`](../../Module_4/data/steady_state.csv), noting which raw file and averaging window now support each final value.
- [ ] Regenerate the [three figures](../../Module_4/figures/) with a caption that states the *actual* accepted 3τ-plus-minute criterion. Refit slopes, ratio, and inferred `Q̇_J/Q̇_P`; update the [A2 draft](../assessments/a2_open_loop_tec.md) and [C4 answers](../assessments/c4_module_04_oral_prep.md) if numbers change.
- [ ] Each student independently finds the four values in the **27 °C hot-side** Laird table before asking AI to verify them. This is intentionally deferred; the A2 manufacturer comparison cannot be completed until then.
- [ ] Produce and inspect a 1–2-page `A2_Lastname_Lastname.pdf` only after the measured data and Laird values are complete. Each teammate uploads it separately before Monday, October 5, 6:00 PM.
