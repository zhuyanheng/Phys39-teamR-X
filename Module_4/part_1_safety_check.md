# Module 4 Part 1 software verification — 2026-09-23

Current configuration after the user's operating-limit request: both PWM outputs shut down at temperature <=10 °C or >=45 °C, as well as on non-finite sensor readings. The assignment's 60 °C software limit remains in the code; the 45 °C operating guard intervenes first in normal operation. These are checks in the same firmware, not independent protective systems. GUI and new CSV files record both operating bounds and the 60 °C limit. The 10 °C and 45 °C boundaries have not been physically tested. Earlier tests below used the thresholds stated in their own sections.

The user confirmed that TEC external power was off and disconnected. Arduino Uno was connected by USB at `/dev/cu.usbmodem101`, 9600 baud. No powered TEC run was performed.

## Code used

- [Arduino source](arudino/part_1/part_1.ino): averages 1000 ADC readings before converting temperature, checks safety every loop before commands, forces both outputs and commanded PWM to zero on overtemperature or non-finite temperature, and continues serial reporting. Normal threshold: 60 °C. Once temperature is valid and below the limit, safety clears; commanded PWM remains zero until a new command.
- [Python GUI](python/part_5_tec_control_gui.py): displays and saves safety state, firmware output values, and threshold; preserves invalid-temperature reports; creates a distinct timestamped CSV each launch.

## Test and results

A temporary copy of the Arduino sketch used a 20 °C threshold; the repository source remained at 60 °C. Both versions compiled for `arduino:avr:uno` (7294 bytes flash, 403 bytes global RAM).

At measured 22.84–22.90 °C, the temporary firmware reported `Safety: SHUTDOWN`. Commands `SET PWM 25 DIR HEAT` and `SET PWM 25 DIR COOL` were rejected. Commanded PWM, Heat PWM, and Cool PWM stayed at zero, with 15 serial measurements continuing at approximately 0.51 s intervals.

- [Shutdown serial evidence](data/safety_shutdown_20260923_111505_281492.txt)

The 60 °C production firmware was then uploaded. Five measurements reported `Safety: OK`, `Limit (C): 60.00`, and all PWM values zero, at 23.52–23.82 °C.

- [Restoration serial evidence](data/safety_restored_20260923_111532_983431.txt)

## Subsequent instructor-present 30 °C test

The user subsequently requested a 30 °C temporary threshold with the instructor present and then reported completion. The GUI recorded a heating command and an actual threshold crossing in [the 30 °C test CSV](data/module_04_tec_20260923_114043_802804.csv). The earlier external-power-off statement applies to the initial test only; the later physical power configuration was not independently observed.

| Arduino time (s) | Temperature (°C) | Commanded PWM | Safety | Firmware heat/cool PWM |
| --- | --- | --- | --- | --- |
| 26.41 | 29.97 | 173 | OK | 173 / 0 |
| 26.92 | 30.67 | 0 | SHUTDOWN | 0 / 0 |
| 28.45 | 31.61 | 0 | SHUTDOWN | 0 / 0 |
| 34.09 | 29.87 | 0 | OK | 0 / 0 |

Serial reporting continued through shutdown and recovery. The 30.67 °C sample is the first *reported* shutdown, not an exact measurement of the triggering temperature between reports. The brief temperature rise after PWM removal is consistent with thermal inertia but was not independently diagnosed. Physical output voltages remain unreported. The production source remains at 60 °C.

## Physical documentation still to record

Serial output values are firmware reports, not independent voltage measurements of pins 9 and 10. Verify both physical outputs with instructor-approved instruments before claiming electrical verification. Sensor-disconnection shutdown was inspected in code and its serial parsing checked, but was not tested by disconnecting the actual sensor.

Wiring diagram, 18 AWG wiring/crimp inspection, thermal-switch continuity and series placement, approved supply voltage/current limit, and instructor approval remain to be recorded. Keep actuator power disconnected until those checks are complete. Module 4 operating range is 10–45 °C; the software threshold is not the permitted operating maximum.
