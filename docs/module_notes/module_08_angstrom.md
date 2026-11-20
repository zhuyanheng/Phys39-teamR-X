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

- Raw sessions: `m08_rehearsal_pi_multi_period_20261109_093936_011209` and
  `m08_rehearsal_pi_multi_period_20261109_094442_064803` in `Module_8/data/raw/`.
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

`m08_pi_p200s_20261109_095722_597413.csv` records the 200 s PI pilot.
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

Review: `Module_8/data/processed/pilot_checks/m08_pi_p200s_20261109_095722_597413_final_pilot_review.json`.
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

## P boundary comparison, 2026-11-11

Recorded `Module_8/data/raw/m08_p_p200s_20261111_094156_728168.csv`
with its serial log and immutable plan snapshot. Operator confirmed TEC supply
on before control start. Firmware STEP began at device time 177.356 s,
09:44:54 local time. Exclude the preceding 354 passive measurements from P
analysis, but preserve the complete original record: Stage 1/S18.2 and Stage 5
require unchanged raw data. The proposed raw deletion was cancelled after the
operator prioritized course requirements and agreed to this preservation policy.

The 1200 s P schedule completed six full 200 s cycles (2400 active samples),
Kp=50 PWM/C, Ki=0, mean 35 C, amplitude 5 C, limit 96. Final firmware state
was DONE/PWM 0 with no fault; GUI was disconnected afterward to close logging.
All six temperatures are finite, with no sequence gaps and maximum sample gap
0.501 s. Forty startup samples saturated; cycles 2–6 did not saturate.

Cycles 4–6 have TEC mean span 0.0054 C, amplitude span 0.132%, phase span
0.00037 rad. T1 spans 0.1259 C, 2.864%, and 0.0527 rad: its mean exceeds the
provisional 0.1 C full-window tolerance. Although cycles 5–6 are more repeatable,
three settled boundary cycles are not yet certified. Do not classify this as
a complete production dataset or declare the whole module complete.

Exact per-cycle fits, coverage, provisional thresholds, and the closed-file hash:
`Module_8/data/processed/pilot_checks/m08_p_p200s_20261111_094156_728168_p_control_review.json`.
The control-start sidecar records the analysis exclusion without removing samples.

## Raw PWM feature update, 2026-11-11

Firmware/GUI v2 now adds RAW_ZERO (`Ua=0, Ub>0`) and RAW_POS (`Ua>Ub>0`),
both using `u=Ua+Ub*sin(phase)` without feedback, lookup or cooling compensation.
Ua/Ub are separate PWM-count fields. Raw STEP temperature/gain slots are zero;
their measured-record fields are nan. The record appends Ua_pwm/Ub_pwm (44 fields),
and the parser still reads saved v1 temperature records. Old temperature-plan
JSON files load unchanged and migrate in memory; a v2 firmware handshake is required.

Both validators reject raw peaks above the chosen limit rather than clipping.
Only the new diagnostic plans use limit 100; existing 96-limit comparison plans
and all temperature, link, physical-cutoff and zero-output protections remain.
The GUI adds two presets, editable Ua/Ub columns and a linked applied-PWM plot.
Four diagnostic JSON files are available in config/ and at Module_8 top level.
Positive-only Ua=32, Ub=5 is an initial static-curve estimate, requiring measured
mean verification rather than assuming 40 C is achieved.

The complete 89-test suite and Uno compilation pass (16474 bytes flash,
1238 bytes global RAM, 810 bytes remaining). Firmware was uploaded with verify
to the detected Arduino Uno at /dev/cu.usbmodem1101. Passive GUI validation
`m08_setup_raw_zero_p100s_ua0_ub100_20261111_104447_604409.csv` records the v2 handshake and accepted
raw plan, 94 valid six-channel samples, and zero output throughout; no START
command was issued. It is software/connection evidence, not a raw-PWM trial.
The GUI was disconnected after verification and remains open with the first
100 s, +/-100 PWM, 900 s planning configuration loaded. Actual diagnostic
waveforms, settling and safety behavior still need measurement on the apparatus.

## Raw PWM temperature-stop review, 2026-11-11

The 11:23 and 11:25 RAW_ZERO trials both tripped TEC_RANGE near 45.1 C;
T1 was 31.15 and 32.68 C, respectively. This is the preserved TEC operating
limit, not the T1 limit or a demonstrated failure of the 60 C backup.
No protection or physical cutoff was raised or bypassed. Failed records remain.

The course page fetched again today has changed its S18.3 protocol: begin near
room temperature at 300 s with initial Ua=0, Ub=50, reduce Ub if approaching the
software cutoff, and use the selected safe amplitude unchanged at 300/200/100 s.
The earlier +/-100, 100/200/500 s guidance is superseded for new raw trials.
New 50-PWM plans for 300/200/100 s are in config/ and Module_8 top level.
The existing GUI preset and older 100-PWM files are historical defaults; explicitly
load RAW_ZERO_50PWM_300s_25min.json for the revised initial safety pilot.
No controller was restarted and no thermal limit was changed during this review.
Evidence: data/processed/pilot_checks/raw_pwm_temperature_limit_review_20261111.json.

## End of session, 2026-11-11

Operator ended the day and accepted the partial 300 s raw-PWM record for today:
`m08_raw_zero_p300s_ua0_ub50_20261111_113001_400415.csv` and its unchanged log/plan.
This is retained partial evidence, not automatic production qualification.
The GUI logged STOP and disconnect at 11:44:19, then closed. At review the
Arduino serial device was absent; no post-STOP zero-output measurement was saved.
The user was instructed to switch off the TEC supply. No acquisition was restarted.
Exact settings, elapsed duration, hash and shutdown limitation are in the matching
`_end_of_day.json` under Module_8/data/processed/pilot_checks.

## Session continuation, 2026-11-16

Raw +/-50 PWM records at 200 s and 100 s completed without a fault; the
300 s partial run remains accepted by the operator for today, not certified as
production. RAW_POS Ua=32, Ub=5 at 100 s also completed: the final cycle TEC
mean was 38.002 C (not 40 C), final-three-cycle mean span 0.165 C. Preserve
this measured result and the safety-reduced amplitude qualification.

Operator confirmed T1–T5 have exactly the Module 7 hole positions and explicitly
authorized reuse. sensor_map.json now selects x=[0,.0385,.0895,.1405,.1915] m,
L=.2715 m, T1 origin physical hole 2; uncertainty values remain unknown. Do not
require remeasurement solely because a new module began. Qualify downstream
signals using the pilot before deciding whether repositioning is necessary.

Next prepared trial: PI_35C_5C_100s_20min.json, 1200 s, Ta35/Tb5, period100,
Kp50/Ki.3, ratio3.50345, cap96, anti-windup ON. This is a budgeted control/rod
pilot with unchanged safeguards, not proof of five settled production cycles.
No device was started while preparing these files.

### Nov. 16 PI 100 s pilot and prepared 300 s trial

`m08_pi_p100s_20261116_104519_503645.csv` completed 1200 s / 12 cycles,
2400 active samples, no sequence gaps, no fault, maximum TEC 39.698 C and
final DONE/PWM0. Last five cycles show repeatable TEC, but T3 amplitude span
25.9%, phase span .181 rad and mean span .168 C. Retain as a pilot; no
three-rod production interval is certified. The matching pilot_review.json
records exact intervals, fits and raw hash. Prepared PI_35C_5C_300s_40min.json:
Ta35/Tb5, Kp50/Ki.3, period300, budget2400 s, cap96, ratio3.50345, anti-windup
on. Longer-period downstream signal and settling still require measurement.
No hardware action was performed while preparing this plan.

## End of session, 2026-11-16

Operator stopped for today. The 300 s PI run actually completed all 2400 s /
8 cycles, 4800 active samples, final DONE/PWM0, no fault, and logging closed.
Do not restart or schedule more acquisition this session. User should switch
off the TEC supply. Last-five-cycle T3 amplitude span is about 25% and phase
span .268 rad; full production qualification is still pending.

PI records now exist at 100, 200, 300 and 500 s. The only completely unmeasured
required PI period is 400 s. Review the existing four before assigning repeats;
100/300 and the earlier 200/500 pilots have unresolved qualification concerns.
Five retained 400 s cycles alone take 2000 s (33 min 20 s), excluding settling.
The two remaining computer-simulation evidence groups are the S18.3 table/check
and the focused 100 s P/PI comparison; no saved results were found in the repo.
Exact sources/hashes and remaining work: Module_8/data/processed/pilot_checks/
session_inventory_20261116.json. No claim that all measured periods are qualified.

## Session plan, 2026-11-18

Confirmed there are no newer runs after Nov. 16 and no 400 s PI record.
Prepared PI_35C_5C_400s_53min20s.json (also config/production_pi_35C_5C_400s.json):
period400, duration3200 s / 8 cycles, Ta35/Tb5, Kp50/Ki.3, cap96,
ratio3.50345, anti-windup ON. Temperature safeguards and confirmed geometry
remain unchanged. This is the missing-period candidate record, not automatic
production qualification. Record current room temperature. After acquisition,
review all five periods before deciding on repeats. No hardware was accessed
or started while preparing this configuration.

## Five-period offline analysis, 2026-11-18

The 400 s PI run completed 8 cycles / 6400 active samples with DONE/PWM0
and no fault. All five required PI periods now have measured records. The
operator confirms no room-temperature record; Module 6/7 were searched for
geometry uncertainty. The caliper specification is 0.01 mm, not a supplied
standard error; the old +/-1 mm ruler calculation is retained as sensitivity
only, because the original geometry note and A4 leave standard errors unknown.

Completed fixed-last-five T1-T3 harmonic/finite-rod analysis, all contiguous
five-cycle stationarity checks, conditional joint uncertainty, geometry/trend/
extra-sensor sensitivity, residuals and finite-vs-infinite comparisons. No
source CSV edited and no hardware command sent. All five fail the original
provisional full-window settling tolerances; none is silently certified.
Diagnostic kappa centers are 6.66-6.99e-5 m2/s; 100 s nu is negative and changes
sign under a linear-baseline sensitivity fit, so it is not a credible positive
loss determination. The production-coverage helper now requires all five
specified periods, fixing obsolete two-period completeness logic.

Working results: Module_8/docs/five_period_review_2026-11-18.md.
Runnable analysis: Module_8/python/analysis/five_period_review.py.
Numerical provenance and frozen prefixes: Module_8/data/processed/five_period_review/.
Scientific PNG/PDF figures: Module_8/figures/five_period_review/.

## English translation and file organization, 2026-11-18

Translated the full five-period review into English at the same document path.
Standardized 17 acquired session stems by mode, period, raw-PWM settings where
applicable, and original acquisition timestamp. CSV, exact serial log and
immutable plan files retain matching stems. Renamed 92 files in total,
including 53 raw session files, analysis snapshots, derived results and figures.
No raw/snapshot content was edited. File mapping and captured hashes are in
Module_8/data/file_renames_20261118.csv and .json; the grouped entry point is
Module_8/data/DATASET_INDEX.md (machine-readable dataset_index.json).

Updated active configuration references, analysis scripts and derived paths.
Immutable plan contents and historical verification receipts keep capture-time
names and hashes, resolved through the mapping. The still-connected November 18
GUI retains two old CSV/log paths as symlinks to the canonical m08_pi_p400s
files; keep these aliases until that GUI session closes. No hardware commands
or GUI controls were used during organization.

Both analyses reran successfully. The three five-period numeric CSVs remained
byte-identical; OPEN/P/PI metric differences were floating-point roundoff only
(maximum about 5e-14). All 63 renamed raw/snapshot files passed full-content or
live-prefix hash verification; navigation links and 33 related tests passed.
Receipt: Module_8/data/organization_verification_20261118.json.

## Stage 2 simulator, figures and completed worksheet, 2026-11-18

Copied Module 6's Lab_6_7_modeling_tec_v3.py byte-for-byte to
Module_8/python/simulation/tec_model_v3.py. Module 6 remains unchanged. Added
an offline Module 8 frontend and raw-sine adapter, six JSON presets, full startup
CSV export, first-harmonic readout and equal-chi analytical overlay. Launch:
Module_8/run_simulation.command. Outputs are explicitly mathematical simulation
data in data/simulation/s18_3, separate from measured raw records.

Completed the S18.3 six-row worksheet at periods 100/200/300 s and chi_c=.23/.46,
with ambient=initial22 C, tau80 s, chi_h=.46, Ua0/Ub50 PWM. These are prescribed
teaching inputs, not substitutes for missing laboratory ambient readings.
All simulations use ten-cycle budgets and report the last five complete cycles,
with explicit cycle-span diagnostics, Euler dt=.05 and independent Fourier/
complete-transient checks. Six mathematical/export tests passed; GUI preset
loading and completed-response readout checked without device access.

Stage 2 figures now include measured zero-centered raw PWM at 300/200/100 s,
measured zero-vs-positive 100 s comparison, all six simulated responses, and the
300 s equal-chi analytical/startup comparison. Every figure has PNG/PDF copies.
The measured 300 s run has only two complete cycles and remains diagnostic.
Positive-only uses Ua32/Ub5 versus zero-centered Ua0/Ub50; different amplitude
and mean prevent a claim that polarity alone explains residual changes.
All four measured source hashes remain unchanged. No hardware commands sent.

Working notes/table/links: Module_8/docs/stage2_results.md.
Exact five-column worksheet: Module_8/data/processed/stage2/m08_stage2_s18_3_filled_table.csv.
Reproduce: .venv/bin/python Module_8/python/analysis/stage2_raw_pwm.py.
The Stage 3 focused P/PI task still needs the separate six-sensor rod simulator;
the copied one-lump simulator is not presented as that task's completion.

## Measurement-gap review against current course page, 2026-11-18

The current live Part I page (retrieved November 18, 878 lines, versus the
earlier cached 781-line version) explicitly requires a common-setting 100 s
feedforward/P/PI tracking comparison in S18.6-S18.8. The inventory has OPEN/P
only at 200 s. The existing 200 s figure remains useful evidence but does not
by itself fill that specified 100 s table. Acquire the missing 100 s OPEN and
P records if following the current checklist; independently review the existing
100 s PI record for reuse as control evidence (three settled cycles), without
claiming its five-cycle production qualification.

Prioritize review/improvement of PI100 and PI300, whose final-five T3 amplitude
spans are about 26% and 25%; RAW_ZERO300 has only two complete cycles including
startup, so it lacks a demonstrated settled Stage 2 interval. PI200/400/500 also
remain diagnostic under the original provisional span limits. Failure of those
planning limits is not itself proof that every record must automatically be
repeated; preserve the curves, noise checks and model limitations for review.

The current S18.4 worksheet defines residual amplitude as half peak-to-peak,
not residual RMS. Existing Stage 2 outputs report RMS and need that additional
calculation and the paired positive-only simulation/table; these are computer
tasks, not additional hardware measurements. New measurements must record real
ambient temperature and drift. Today's room temperature cannot retrospectively
replace missing ambient values from the older runs. Geometry is confirmed
unchanged, but instrument resolution/position-reading uncertainty remains
incompletely documented. No hardware commands were sent for this audit.

## Prepared physical 100 s feedforward parameter file, 2026-11-18

Clarified that the missing 100 s feedforward trial is a physical Arduino/TEC
measurement, separate from the already completed six teaching simulations.
Created FEEDFORWARD_35C_5C_100s_5min_CHECK_ROOM.json at Module_8 root and an
identical config/feedforward_35C_5C_100s_5min_check_room.json. Both load through
the current v2 plan validator and have positive, unclipped PWM commands.

The current course scalar formula is implemented using RAW_POS: period100,
duration300, Ua23.3325/Ub10.09191 PWM, cap96, no feedback or cooling multiplier.
The 35+/-5 C comparison request is metadata; RAW_POS Ta/Tb zero placeholders
are inactive, and the firmware records phase for reconstructing the comparison
setpoint in analysis. This differs from the existing OPEN inverse-table mode.

IMPORTANT: the draft Ua uses the historical Module 4 zero-PWM baseline23.44 C,
not current measured ambient. Actual ambient remains null. Before starting,
measure room temperature and update Ua=(35-Troom)/0.49544628875665514 as well
as the ambient metadata, then reload/upload. Do not silently relabel23.44 C as
a current measurement. No device access or upload/start occurred. Duration is
three cycles under the operator's instruction to ignore settling in this list;
it is not automatic certification of three settled cycles.

## Prepared next physical P-only trial, 2026-11-18

At operator request, prepared P_35C_5C_100s_5min.json at Module_8 root and an
identical config/comparison_p_35C_5C_100s_5min.json. This is the physical P-only
trial after feedforward: mode P, duration300 s, period100 s, Ta35/Tb5 C,
Kp50 PWM/C, Ki0, cap96, ratio3.503450480306341. Anti-windup is enabled but
inactive in P mode; Ua/Ub zero placeholders are inactive. Gains match existing
P200/PI100, geometry and firmware protections remain unchanged. Current ambient
is unknown and must be recorded for the new run, but the P control law does not
need it to compute its feedback command. A cold start can saturate the PWM cap;
the plan explicitly requires retaining that evidence. Both files round-trip
through the v2 validator and produce the expected schedule command offline.
No serial/device access, upload or start occurred. The feedforward file still
awaits current ambient confirmation; preparing this next plan does not complete
or start either physical trial.

## Physical-trial coverage completed, 2026-11-18

Verified two new actual acquisitions: module_08_rod_20261118_113619_678440
is scalar feedforward implemented as RAW_POS (Ua23.3325/Ub10.0919), and
module_08_rod_20261118_114204_147029 is P-only at35+/-5 C, Kp50/Ki0.
Both completed300 s / three100 s cycles with600 RUNNING samples, no sequence
gaps, no nonfinite temperature readings or recorded RUNNING faults, followed
by DONE/PWM0. No hardware commands were sent for this verification.

Under the operator's explicit instruction to ignore settling as a reason for
more measurements, all planned hardware trial types now have records. This is
trial coverage, not certification of settled production intervals. Both new
plan snapshots still have ambient_C null; feedforward used the historical
23.44 C calibration reference. Preserve that limitation rather than asserting
measured ambient or exactly matched current feedforward prediction.

Remaining work is on the computer: S18.4 paired simulation and residual
amplitude worksheets,100 s P/PI six-sensor simulation, matched300 s
theory/measurement/numerical-rod comparison, integrating the two new control
records into the100 s control figure/table, and final A5 synthesis. No new
hardware trial is initiated by this status check. Completion receipt:
Module_8/data/processed/control_comparison/m08_100s_physical_completion_20261118.json.

## Analysis inputs confirmed, 2026-11-20

The operator specified the first finite TEC A0 reading from each acquisition as
its room reference. The 18 acquisitions with RUNNING data are indexed in
Module_8/data/processed/m08_initial_tec_room_references.json. The source
timestamps, run state and applied PWM are recorded there. Air temperature and
its drift remain unmeasured. The five PI mean profiles were refitted using
their individual TEC references. Stage 2 measured metrics now include the
mean rise above this reference. Common-bath cross-calibration was removed from
the planned work at the operator's request. Fits use the recorded channels.

The operator confirmed the original ruler error as ±1 mm. The sensitivity
analysis applies the bound to each of the five ruler gaps originally recorded
between T1 and the tip, then accumulates the errors in the positions and L.
Both mean and oscillatory refits use all 32 sign combinations. The ruler
ranges are reported separately from conditional fit errors. See
Module_8/docs/transport_and_model_note_2026-11-18.md for the updated results.
