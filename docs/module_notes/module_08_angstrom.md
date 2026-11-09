# Module 8 Angstrom status

Updated 2026-11-09. See [Module 8](../../Module_8/README.md),
[serial protocol](../../Module_8/docs/serial_protocol.md) and
[runbook](module_08_lab_day_runbook_2026-11-04.md).

## Implemented

- Arduino-owned sinusoidal setpoint and multi-step schedule with continuous phase.
- OPEN/P/PI trials, calibrated inverse static feedforward, measured heating/cooling
  ratio, compensation before PWM saturation, and compensated-command anti-windup.
- GUI schedule editor, presets, JSON import/export, measured-curve loading, per-step
  gains, acknowledged plan upload and separate Start action.
- Versioned fixed serial schema with six temperatures, forcing/controller parameters,
  step, phase, raw/compensated/applied PWM, sequence and safety state.
- Live six-channel plots, setpoint/control/PWM readout, event notes, raw incoming-byte
  log, parsed CSV and immutable per-upload plan/sensor-map/source-hash snapshots.
- Preserved 10–45 C operating range and 60 C TEC backup; added T1 validity/56 C
  cutoff, 2 s firmware heartbeat/control-gap stops and latched fault/reset flow.
- All acquisition and default analysis outputs remain inside Module 8.
- Three presets: four-segment comparison, single trial/fixed target, short rehearsal.

## Verification and limits

- Hardware-free plan/parser/Qt tests and tests of the actual C++ sketch/core pass;
  current verification details are recorded in `Module_8/docs/verification.json`.
- Arduino Uno compilation passes with AVR core 1.8.8: 15,542 bytes flash, 1,122 bytes
  globals, 926 bytes remaining for locals/stack. Compiler was found inside Arduino IDE.
- Preview checked with port discovery and physical serial access blocked.
- No firmware was uploaded, no physical connection was opened and no measurement
  was collected during implementation. Test data remains in temporary directories.
- New firmware must be uploaded before using this GUI (115200 baud); Module 7's
  9600-baud firmware is deliberately rejected by the new version/schema checks.
- The firmware-controlled acquisition is implemented; physical tracking quality,
  periodic gains and settling are not yet validated.

## Still needed on apparatus / in analysis

- Oscillatory sensor positions and uncertainties. `Module_8/config/sensor_map.json`
  is pending; inherited Module 7 coordinates are reference only.
- Calibration validation with the rod attached, actual gains, room-temperature
  method and a quantitative periodic settling criterion.
- Full-period pilot, gain/settling qualification and two-period production records.
  The hardware schedule rehearsal passed on Nov. 9; details are below.
- Actual periodic measurements and their accepted intervals; the offline fitter/viewer
  is implemented and described in the modeling-app note. Complete propagation of
  geometry/material/systematic errors still needs experimental input.

## Carry-forward facts

A0 = TEC; A1–A5 = T1–T5. T1 is the analysis boundary, separate from A0.
Diameter reported Nov. 4 is 12.77 mm with caliper specification 0.01 mm.
Earlier sensor positions used physical hole 2 as origin; moving T1 to the first
hole requires remeasuring all coordinates and the analysis length.

No independent room thermometer is available in the latest Module 7 record;
fitted/self-estimated ambient must not be described as independently measured.
Common-bath calibration was skipped previously; retaining its fitter is not
calibration evidence. The Module 4 static curve and ratio approximately 3.5035
retain their protocol qualifications. The physical interlock previously tripped
on a 45 C run; no protection was bypassed to implement the new features.
The 40 +/- 16 C handout trial is rejected by the retained 10–45 C range.

## Run record

No experimental data was acquired during the original software implementation.
On Nov. 9, the operator completed the hardware rehearsal:

- Raw sessions: `module_08_rod_20261109_093936_011209` and
  `module_08_rod_20261109_094442_064803` in `Module_8/data/raw/`.
- 405 + 506 = 911 measurement rows, all six temperatures finite, 0 missing sequence
  records, 0 malformed DATA lines, and no firmware errors or safety faults.
  Sample intervals were 0.499–0.501 s. CSV and exact serial-log sequence lists agree.
- Three schedules completed (5 s/step, 5 s/step, 50 s/step), each with two changes
  between 100, 150 and 240 s periods. Every DONE record reports both PWM outputs zero.
- Independent reconstruction from the uploaded steps and start timestamps agrees
  with recorded phase within 0.000026 rad and generated setpoint within 0.000048 C.
  This checks waveform generation, not measured-temperature tracking.
- The second session changed mean temperature 20 -> 35 -> 20 C. Its setpoint
  jumps are consistent with those deliberate mean changes. Keep mean/amplitude
  fixed in the next periodic pilot.
- The 50 s/step schedule contains only 0.5, 0.333 and 0.208 cycles per step;
  it is not a settled periodic dataset. 154/300 active rows were saturated; this
  includes large mean-temperature transitions and does not establish poor settled tuning.

Checks are reproducible with `Module_8/python/analysis/rehearsal_check.py`;
results and source hashes are in
`Module_8/data/processed/rehearsal_checks/rehearsal_check_20261109.json`.
Original raw files were unchanged during this check.

Proposed next acquisition: load `Module_8/config/pilot_pi_35C_5C_200s.json`.
One PI step, 2700 s, Ta=35 C, Tb=5 C, period=200 s, Kp=50, Ki=0.3,
PWM limit=96, measured provisional ratio approximately 3.50345, anti-windup on.
This is a pilot with editable starting settings, not an accepted production run.
Choose settled intervals quantitatively and retain at least five full settled
cycles; fixed duration alone does not prove acceptance. Preserve the actual sensor
configuration during this run and resolve the pending map before spatial inference.

### First full-period pilot result, Nov. 9

`module_08_rod_20261109_095722_597413.csv` records the 200 s PI pilot.
Its last saved measurement is at 10:39:43, approximately 2531 s after Start;
STOP/Disconnected follows. This is about 42 min, not an automatic 2700 s completion.
The command log contains STOP, but no subsequent measurement confirms zero output;
reconnect and confirm reported PWM 0 before uploading the next plan.

Twelve complete cycles are available. Across cycles 8–12, T1 and T2 meet the
planning full-span limits (0.1 C mean, 5% amplitude, 0.1 rad phase). T3 spans
8.06% in amplitude and 0.1402 rad phase, failing those limits. T3 amplitude is
approximately 0.40–0.43 C; T4/T5 are weaker and less repeatable. The final five
cycles contain no PWM saturation. Preserve this as a pilot; no qualifying
three-rod production interval is certified by this check.

Review: `Module_8/data/processed/pilot_checks/module_08_rod_20261109_095722_597413_final_pilot_review.json`.
Its input snapshot length and hash preserve the exact data basis.

Next proposed test: `Module_8/config/pilot_pi_35C_5C_500s.json`, one PI step,
3600 s, mean 35 C, amplitude 5 C, period 500 s, Kp=50, Ki=0.3, PWM limit=96,
ratio approximately 3.50345 and anti-windup on. Keep sensor positions and thermal
conditions fixed. Longer-period forcing is expected to improve downstream
amplitude; whether repeatability improves must be measured. Five retained cycles
alone take 2500 s (41 min 40 s), excluding settling. Sixty minutes is a planning
allowance, not an acceptance guarantee. No device operation was performed by Codex.

### Runtime planning correction

Separate transport acquisition (five settled cycles at two usable periods and
three rod sensors) from boundary-control comparison (at least three settled
cycles per method at common settings). Do not budget 45–60 min for every OPEN/P/PI
comparison or require all methods at the 500 s transport period. Reuse the existing
200 s PI record's repeatable TEC/T1 interval for control metrics while keeping its
three-rod transport qualification separate.

Remaining matched boundary-control plans are
`Module_8/config/control_open_35C_5C_200s.json` and
`Module_8/config/control_p_35C_5C_200s.json`: each uses 35 +/- 5 C, 200 s,
1200 s planning duration, ratio approximately 3.50345 and PWM limit 96. P uses Kp=50
and Ki=0. OPEN's gain fields are inactive. Retain three settled cycles (600 s)
for each and document the actual accepted intervals. Twenty minutes per mode is
a budget, not proof of settling. Both plans require explicit operator upload/start.
The raw-PWM diagnostics remain a separate outstanding feature/measurement item;
these two plans alone do not complete every updated course requirement.

## Offline analysis update, 2026-11-04

The fitter and offline Qt viewer now implement time harmonics, linear spatial
slopes, complex finite-rod spatial inference, cycle-repeat covariance, transport
conversion, settling and finite/radial checks, and residual inspection. See
`Module_8/docs/theory_and_analysis.md`. This implements the analysis workflow;
no real periodic parameters or final experimental completion are claimed.
The Nov. 4 Module 7 record is now a user-selected stationary approximation
with strict-criterion failure and fitted ambient recorded in the reference JSON.
