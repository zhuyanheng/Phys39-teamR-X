# Module 8 Angstrom status

Updated 2026-11-04. See [Module 8](../../Module_8/README.md),
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
- Hardware rehearsal, pilot and two-period production records.
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

No Module 8 experimental data has been acquired during software implementation.
Record each real run's map, ambient method, gains, selected intervals and file identity here.

## Offline analysis update, 2026-11-04

The fitter and offline Qt viewer now implement time harmonics, linear spatial
slopes, complex finite-rod spatial inference, cycle-repeat covariance, transport
conversion, settling and finite/radial checks, and residual inspection. See
`Module_8/docs/theory_and_analysis.md`. This implements the analysis workflow;
no real periodic parameters or final experimental completion are claimed.
The Nov. 4 Module 7 record is now a user-selected stationary approximation
with strict-criterion failure and fitted ambient recorded in the reference JSON.
