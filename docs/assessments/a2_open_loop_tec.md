# A2 — Open-Loop TEC Instrument Note (draft; not ready to submit)

Ricky Huang and Xavier Zhu · Phys 39 · Module 4 · **Lab date: TODO**

This is the repository version of A2. Values marked `TODO` require new supervised measurements or an instructor-verified observation. The live [Module 4 working note and checklist](../module_notes/module_04_open_loop_tec.md) is the source for those values.

## Apparatus and high-current wiring

The apparatus uses a thermistor read by an Arduino Uno, a Python manual-control GUI, an H-bridge, a thermoelectric cooler (TEC), a heat exchanger, and a thermal switch. The Arduino commands HEAT on D9 or COOL on D10, never both intentionally. The high-current path uses 18 AWG stranded copper wire. The Module 3 record describes the path as supply → H-bridge B+/B−, then H-bridge M+ → series thermal switch → TEC+ → TEC− → H-bridge M−. The switch should interrupt TEC current independently of software; it opens near 70 °C. **TODO:** recheck actual Module 4 routing, wire gauge, polarity, spade connections, switch continuity/placement, instructor approval, and insert the *verified* wiring diagram here. The existing drawings in `Module_4/Diagram/` have not yet been reconciled with the physical apparatus for A2.

## Power and software settings

| Setting | Value / evidence |
| --- | --- |
| Module 4 supply voltage | **TODO: actual approved value and meter/supply reading** (Module 3 previously recorded 12 V; do not assume unchanged) |
| Module 4 current limit | **TODO: actual approved setting** |
| Board / port / baud | Arduino Uno; `/dev/cu.usbmodem101`; 9600 baud in the current program — **TODO: recheck on lab day** |
| Thermistor sampling | 1000 ADC measurements averaged before each temperature calculation |
| Software safety limit | 60 °C named constant in the [Arduino source](../../Module_4/arudino/part_1/part_1.ino) |
| Operating range | 10–45 °C measured temperature; current code also forces both outputs to zero at/beyond these bounds |
| Hardware cutoff | Thermal switch near 70 °C; **TODO: confirm series placement/continuity in current apparatus** |
| Exact programs used | [Arduino safety/command sketch](../../Module_4/arudino/part_1/part_1.ino), [Python manual-control GUI](../../Module_4/python/part_5_tec_control_gui.py); **TODO: record final commit SHA and confirm upload/run matched these files** |

The GUI displays temperature versus time and PWM, and writes timestamped serial data. Open-loop means the operator selects direction and PWM magnitude; the controller is not trying to hold a temperature set point. The thermistor temperature, not a target temperature, is measured at each steady state.

## Safety-interlock verification

With TEC actuator power disconnected, a temporary 20 °C software threshold was below the observed room temperature of 22.84–22.90 °C. The firmware reported `Safety: SHUTDOWN`; `SET PWM 25 DIR HEAT` and `SET PWM 25 DIR COOL` did not produce nonzero output commands. Both firmware-reported H-bridge PWM values stayed at 0 while 15 serial measurements continued at roughly 0.51 s intervals. The 60 °C threshold was restored afterward; five subsequent reports showed `Safety: OK`, limit 60 °C, and both PWM outputs 0. See [shutdown serial log](../../Module_4/data/safety_shutdown_20260923_111505_281492.txt), [restoration log](../../Module_4/data/safety_restored_20260923_111532_983431.txt), and [full safety record](../../Module_4/part_1_safety_check.md). These are firmware/serial observations, **not independent voltage measurements** of pins D9/D10.

An additional instructor-present 30 °C demonstration produced a report at 29.97 °C with HEAT PWM 173 and safety OK, followed by a report at 30.67 °C with `SHUTDOWN` and both firmware output PWM values 0; serial data continued. See [30 °C test CSV](../../Module_4/data/module_04_tec_20260923_114043_802804.csv). This was a safety demonstration, **not** a steady-state calibration point. No deliberate run to 60 °C was performed. **TODO:** record any new instructor-verified physical pin-output check, if done.

## Direction, PWM levels, and steady-state criterion

The final table must contain five 8-bit nonnegative PWM magnitudes per direction: 0, approximately 25%, 50%, 75%, and 100% of that direction's separately chosen maximum useful PWM. The exact integer values are not known yet. Do not substitute prior short exploratory/safety CSV runs for steady-state points.

**Steady-state criterion actually used:** TODO — write the reproducible window length and allowed temperature drift *before* classifying points as steady. **Maximum useful PWM reasoning:** HEAT TODO; COOL TODO. **Supply-current observations:** TODO.

| Direction | PWM count | Start T (°C) | Steady T (°C) | Wait (s) | Notes / raw-data link |
| --- | ---: | ---: | ---: | ---: | --- |
| HEAT | 0 | TODO | TODO | TODO | TODO |
| HEAT | TODO (~25% of HEAT max) | TODO | TODO | TODO | TODO |
| HEAT | TODO (~50%) | TODO | TODO | TODO | TODO |
| HEAT | TODO (~75%) | TODO | TODO | TODO | TODO |
| HEAT | TODO (max) | TODO | TODO | TODO | TODO |
| COOL | 0 | TODO | TODO | TODO | TODO |
| COOL | TODO (~25% of COOL max) | TODO | TODO | TODO | TODO |
| COOL | TODO (~50%) | TODO | TODO | TODO | TODO |
| COOL | TODO (~75%) | TODO | TODO | TODO | TODO |
| COOL | TODO (max) | TODO | TODO | TODO | TODO |

Retained formal raw time-series data: [`data/module_04/`](../../data/module_04/) — **TODO: add links to the actual selected CSVs**. Earlier exploratory/safety files remain separately in `Module_4/data/`.

## Temperature traces and response curve

**Heating time trace:** TODO — insert a labeled figure from `docs/figures/module_04/` with time (s), temperature (°C), direction/PWM, raw source, and steady window. **Cooling time trace:** TODO — same. **Steady-state response graph:** TODO — insert red HEAT and blue COOL points with x = PWM magnitude (count), y = steady temperature (°C), and a caption stating the actual steady criterion. Figure-generation preparation is described in the [figures README](../figures/module_04/README.md).

Estimate temperature susceptibility as `χ_T = ΔT_steady / ΔPWM`, in **°C per PWM count**, separately for HEAT and COOL. **HEAT χ_T:** TODO (identify endpoints or local interval). **COOL χ_T:** TODO (identify endpoints or local interval). If the response is curved or saturates, describe that and do not present one slope as globally constant.

## Physical interpretation

**TODO: complete this paragraph after comparing the actual graph.** The directions need not have equal-magnitude response. Reversing a TEC reverses the Peltier heat-pumping direction, but electrical current also produces Joule heat in either direction. The heat exchanger has finite capacity to exchange heat with the room, and the thermistor measures one location rather than the whole TEC–block–sink system. Thermal contact, heat capacity, and the room-temperature boundary condition can therefore affect the two measured slopes differently. Tie these mechanisms to the observed signs, magnitudes, and any nonlinearity; do not claim a particular mechanism was directly measured unless it was.

## Reproducibility and submission

- [Exact Arduino source](../../Module_4/arudino/part_1/part_1.ino) and [exact Python GUI](../../Module_4/python/part_5_tec_control_gui.py), subject to lab-day version verification.
- [Safety evidence](../../Module_4/part_1_safety_check.md), [working lab record](../module_notes/module_04_open_loop_tec.md), and **TODO: selected formal raw CSV + final figure links**.
- Repository: [Phys39-teamR-X](https://github.com/zhuyanheng/Phys39-teamR-X). **TODO: replace/add the final GitHub commit permalink after committing the complete A2 evidence.**
- **TODO:** export the reviewed team PDF as `A2_Huang_Zhu.pdf` if that surname order is chosen; both teammates individually upload it to Moodle by Monday, 2026-09-28 at 6:00 PM.
