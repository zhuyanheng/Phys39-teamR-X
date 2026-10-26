# Module 7: Step 1 six-channel integration check

On-site operating procedure for the first time the six-channel chain is powered.
Goal: prove that **one `DATA` line = one set of displayed values = one CSV row**,
that each channel maps to the right physical probe, and that a failed rod probe
degrades visibly without touching the actuator or the TEC safety path.

This check is done **with the TEC actuator supply disconnected**. Nothing in this
procedure heats the rod. The cross-calibration (Step 3) needs the six probes
free and un-mounted, so **do not push any probe into a rod hole yet**.

Companion document: [lab-day runbook](module_07_lab_day_runbook_2026-10-26.md).

## 0. Preconditions

- [ ] Actuator supply (H-bridge / TEC rail) **switched off and unplugged**. Arduino
  USB power only. Record who confirmed this: `____________`
- [ ] 6 working thermistors, each with a permanent label: `TEC`, `1`, `2`, `3`, `4`, `5`.
- [ ] Labels are already assigned to channels; do not re-assign later, because the
  calibration coefficients `a_i`, `b_i` are per physical probe:
  `A0` = TEC base, `A1` = rod 1 (nearest the TEC, defines `x = 0`), `A2`–`A5` = rod 2–5
  in order of increasing distance, `A5` = furthest / near the tip.
- [ ] Tools: breadboard or screw terminals, multimeter, caliper, tape, spare jumper wires.

## 1. Wiring (unpowered, verify with the multimeter before applying USB)

Each channel is an identical independent divider:

```text
+5V ──[ 100 kΩ fixed ]──┬── A0/A1/…/A5 ──> Arduino ADC
                        │
                   [ thermistor NTC 100 kΩ @ 25 °C, β = 4540 ]
                        │
                       GND
```

The firmware uses `V = 5.00 V`, `R_fixed = 100 kΩ`, `R_25 = 100 kΩ`, `β = 4540`
and computes `R_therm = R_fixed · V / (VREF − V)`
(`Module_7/arduino/module_07_rod_controller/module_07_rod_controller.ino`).
Six dividers must share only the +5 V and GND rails, never a node.

Expected readings at room temperature, so the wiring can be checked before any
software is involved:

| Probe temperature | `R_therm` | Voltage at `Ax` | ADC counts (0–1023) |
| --- | --- | --- | --- |
| 20 °C | ≈ 130 kΩ | ≈ 2.82 V | ≈ 578 |
| 25 °C | 100 kΩ | 2.50 V | ≈ 512 |
| 30 °C | ≈ 78 kΩ | ≈ 2.19 V | ≈ 448 |

Sensitivity near room temperature is only ≈ 0.065 V per °C (≈ 13 ADC counts per °C),
so a 1 °C disagreement between probes is normal before calibration.

- [ ] `+5V` to `GND` is **not** a short on the breadboard (resistance > 10 kΩ).
- [ ] `+5V` to each `Ax`: one 100 kΩ resistor.
- [ ] Each `Ax` to `GND`: the labelled probe, ≈ 100–130 kΩ at room temperature.
- [ ] Pin map confirmed: `A0` TEC, `A1`–`A5` rod 1–5, `D9` = HEAT, `D10` = COOL, common GND.
- [ ] H-bridge logic inputs may stay connected to `D9`/`D10`; its power side and the
  TEC stay disconnected. If the H-bridge is disconnected entirely, write that down —
  then `D9`/`D10` can only be checked with a voltmeter (section 6).

## 2. Flash the firmware

Arduino IDE: board `Arduino Uno`, the `usbmodem`/`usbserial` port, then upload
`Module_7/arduino/module_07_rod_controller/module_07_rod_controller.ino`.
Equivalent command line:

```bash
ARDUINO_CLI="/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli"
"$ARDUINO_CLI" board list                 # find the port, e.g. /dev/cu.usbmodem101
"$ARDUINO_CLI" compile --fqbn arduino:avr:uno Module_7/arduino/module_07_rod_controller
"$ARDUINO_CLI" upload -p /dev/cu.usbmodem101 --fqbn arduino:avr:uno \
  Module_7/arduino/module_07_rod_controller
```

- [ ] Build size matches the verified build: **7844 B flash (24 %), 545 B RAM (26 %)**.
  A different size means a different sketch is being uploaded — stop and check.
- [ ] Record board, port, upload time and the sketch file name in section 7.

## 3. Raw serial check (Serial Monitor, 9600 baud)

- [ ] Open the Serial Monitor at **9600** baud. Expected: four `#` header lines, then one
  `DATA,…` line every 0.5–0.7 s; nothing else. The spacing is quantised by the ≈168 ms
  full sweep (the firmware prints when `millis()` has advanced ≥ 500 ms, so intervals
  alternate ≈ 0.50 / 0.67 s). Every line carries its own Arduino timestamp, so the CSV
  never assumes a fixed rate.
- [ ] `time_s` strictly increases; `pwm` = 0; `heat_cool` = 0; `safety` = OK; `rod_ok` = 5.
- [ ] All six temperatures are within ≈ 1 °C of each other and of room temperature.
- [ ] **Close the Serial Monitor before opening the GUI** — one program per port.

## 4. GUI check (PWM 0 on connect)

```bash
Module_7/run_rod_acquisition.command        # use --preview to look at the window only
```

- [ ] `Refresh ports` → select the same port → `Connect (PWM 0)`.
- [ ] Status bar: `Connected; wait for a fresh Safety: OK line. CSV: …/Module_7/data/raw/module_07_rod_<timestamp>.csv`
- [ ] Readout line shows `valid 5/5`, `Safety=OK`, `PWM=+0`, and `rows ok/bad=` with
  `bad` staying at 0. A growing `bad` count means a baud-rate or wiring problem, not data.
- [ ] All six temperature curves plus the dashed setpoint line are visible; TEC is the
  thick black curve; rod 1–5 are blue, green, olive, orange, violet.

## 5. Channel fingerprint (the actual integration test)

Warm **one** probe at a time (pinch it between two fingers, or rest it against a
finger) for 15–20 s, then let go. Expected: that channel rises 1–3 °C within
10–20 s and falls back slowly; the other five move < 0.1 °C. Wait ≥ 10 rows between
probes so the previous probe has started to recover.

| Probe label | Channel | Rose alone? (Y/N) | ΔT peak (°C) | Time to peak (s) | Other channels moved? |
| --- | --- | --- | --- | --- | --- |
| TEC | A0 |  |  |  |  |
| 1 | A1 |  |  |  |  |
| 2 | A2 |  |  |  |  |
| 3 | A3 |  |  |  |  |
| 4 | A4 |  |  |  |  |
| 5 | A5 |  |  |  |  |

- [ ] Every probe produced a response on its own channel only.
- [ ] Two channels moving together ⇒ shared node, swapped leads, or probes taped together.
- [ ] No response at all ⇒ open lead, wrong divider, or probe on the wrong `Ax`.
- [ ] **Mapping signed off** (this table becomes the sensor map in
  `module_07_rod_instrument.md`): `____________`

## 6. Fault injection (safe: actuator power is off)

- [ ] Pull one rod probe out of its `Ax` (or its GND) → the next `DATA` line shows `nan`
  for that channel, `valid 4/5`, `rod_ok` = 4, and **`Safety` stays `OK`** with the
  actuator command unchanged. The GUI keeps updating; `bad` does not count these rows.
  (An open probe pulls the node to +5 V and a dead short pulls it to 0 V; the firmware
  returns `nan` for both, so `nan` alone does not tell you which — use the multimeter.)
- [ ] Push it back → the next line returns to `valid 5/5` without restarting anything.
- [ ] Pull the **TEC** probe (`A0`) → `TEC=nan`, `Safety=SHUTDOWN`, `pwm` = 0. This is the
  independent safety path from Module 6 and must still work.
- [ ] Reconnect `A0` → `Safety` returns to `OK` (the firmware re-checks every cycle).
- [ ] Optional, only if the H-bridge is wired but unpowered: send `SET PWM 128 DIR HEAT`
  from the Serial Monitor and measure `D9`–`GND` ≈ 2.5 V DC, `D10`–`GND` ≈ 0 V; then
  `SET PWM 128 DIR COOL` for the reverse, then `SET PWM 0 DIR COOL` to leave both at 0.
  This is a logic-level measurement only — **no TEC supply, no load**.

## 7. Record (fills the evidence note)

| Item | Value |
| --- | --- |
| Date / operator |  |
| Actuator supply off confirmed by |  |
| Board / serial port |  |
| Sketch file + build size | `module_07_rod_controller.ino`, 7844 B / 545 B |
| Commit hash of this code |  |
| Probe label → channel map |  |
| Room temperature (independent thermometer) |  |
| Six channel readings at rest (TEC, rod 1–5) |  |
| CSV file written |  |
| Fault-injection result (`nan` rod / `SHUTDOWN` TEC) |  |

## 8. Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| All channels `nan`, or `0.00` everywhere | divider missing +5 V or GND; node shorted | measure `Ax` to GND, expect 2.2–2.9 V |
| One channel `nan`, others fine | that probe open or lead broken | re-solder, re-crimp |
| One channel pinned at a high temperature (≈ 85 °C or more) | low-resistance path to GND — wrong fixed resistor (10 kΩ instead of 100 kΩ) or a partial short | check the resistor value and the node |
| Values jump ±2 °C between samples | loose contact, long unshielded leads, no common ground | shorten leads, common GND at one point |
| `bad` count keeps rising | serial monitor/baud mismatch, second program on the port | close other programs, 9600 baud |
| GUI shows `valid 5/5` but curves are flat at 0 | plotting the wrong column (dev edit) | run `python3 Module_7/python/test_rod_protocol.py` |
| Actuator output present at boot | wrong sketch uploaded | re-upload, compare build size |
| `Connect` fails | port busy or wrong port | close Serial Monitor, `Refresh ports` |

## 9. Stop conditions and shutdown order

Stop immediately, press `STOP — PWM 0`, then cut actuator power and tell the
instructor if: any temperature moves the wrong way or approaches 10 °C / 45 °C,
the display or serial freezes, the supply current rises unexpectedly, or the TEC,
H-bridge or heatsink becomes hot or smells. During this check the actuator supply
is disconnected, so those hazards are not live — but do not connect it just to
"see if it works"; that belongs to the supervised step-response run.

Shutdown order: `Disconnect / PWM 0` in the GUI → close the GUI → unplug USB →
leave the probes loose (still un-mounted, so Step 3 can soak all six together).

