# Module 8: Angstrom Experiment And Final Thermal Transport

The Module 8 controller now generates sinusoidal setpoints, compares calibrated
open-loop/P/PI control, adds uncompensated zero-centered and heating-only PWM
diagnostics, and executes an editable multi-step frequency schedule
on the Arduino. The horizontal Python GUI displays all six thermistors and saves
complete measurement, event and plan evidence inside this module.

Course sources: [Part I](https://sethfraden.github.io/Phys39F26-course/labs/lab-09/)
and [Part II](https://sethfraden.github.io/Phys39F26-course/labs/lab-10/).
See the [lab runbook](../docs/module_notes/module_08_lab_day_runbook_2026-11-04.md),
[status note](../docs/module_notes/module_08_angstrom.md) and [serial protocol](docs/serial_protocol.md).

## Run the instrument

1. Upload `arduino/module_08_rod_controller/module_08_rod_controller.ino` with
   Arduino IDE, selecting the actual board and port. The adjacent `angstrom_core.h`
   must remain in the sketch folder. Use the v2 sketch with the updated GUI;
   current build/upload evidence is in `docs/verification.json`.
   Close other serial applications before connecting.
2. Double-click `run_rod_acquisition.command`. The GUI and firmware use **115200 baud**;
   earlier Module 7 firmware is incompatible. A version handshake blocks starting with old firmware.
3. Select the port and **Connect (output off)**. Confirm six plausible live readings.
4. Choose/edit a preset, enter ambient information and a quantitative settling
   criterion, and verify the calibration and gains. Blank ambient remains explicitly unknown.
5. Click **1. Upload plan**. Each command is acknowledged; upload leaves output off.
   The GUI snapshots the plan, sensor map and source hashes beside the raw CSV.
6. Click **2. Start schedule** when the apparatus is ready. Arduino owns waveform,
   phase, controller and schedule timing. GUI updates do not set the waveform timing.
7. Use **STOP** at any time. Completion sets both outputs to zero. After a latched
   fault, fix the cause, wait for safe readings, click **Reset latched fault**, then
   upload again. No automatic restart occurs.

Offline preview:

```bash
Module_8/run_rod_acquisition.command --preview
```

Preview never discovers or opens serial ports and creates no experimental files.
The repository's existing `.venv` is shared. Package dependencies are listed in
`python/requirements.txt`; there are no runtime imports from older modules.

## Waveforms, control and presets

The setpoint is `Ta + Tb*sin(phase)`, with phase accumulated using Arduino elapsed
time. Frequency changes integrate the old period up to the transition and the new
period afterward. Phase stays continuous. Changing mean or amplitude may intentionally
change the setpoint immediately; keep both fixed when comparing frequencies.

| Preset | Schedule | Purpose |
| --- | --- | --- |
| Comparison | OPEN, P, PI at 100 s, then PI at 150 s; each step 1800 s; Ta=35 C, Tb=5 C | Editable planning defaults for the four measurement segments |
| Single trial / fixed target | One PI step, 1800 s, 100 s period, 35 +/- 5 C | Tune one trial; set amplitude to 0 for a fixed temperature; choose OPEN or P if needed |
| Short rehearsal | Three 5-second PI steps with periods 100, 150, 240 s; Ta=35 C, Tb=2 C | Test two automatic frequency changes and completion; not production data |
| Raw zero-centered | RAW_ZERO, Ua=0, Ub=100 PWM, 100 s period, 900 s budget | Uncompensated +/-100 sinusoidal PWM; begin near measured room temperature |
| Raw heating only | RAW_POS, Ua=32, Ub=5 PWM, 100 s period, 900 s budget | Positive-only diagnostic; adjust Ua from measured mean, initially estimated near 40 C |

The 1800-second durations and Kp=50, Ki=0.3 are starting values, **not a verified
periodic tuning or settling guarantee**. Retune on the actual apparatus and budget
settling plus at least five accepted cycles at each retained period. Rehearsal
shortens step durations; it never reduces the sinusoidal period below 100 s.
Plans can be saved/loaded as JSON in `config/` and contain at most 12 steps.

Ready-to-load diagnostic files are also placed at the top level of `Module_8`:
`RAW_ZERO_100PWM_100s_15min.json`, `RAW_ZERO_100PWM_200s_20min.json`,
`RAW_ZERO_100PWM_500s_2500s.json`, and `RAW_POS_32_5PWM_100s_15min.json`.
Durations are planning budgets, not settling certificates. Change period only
after inspecting the live data. Raw PWM uses separate Ua/Ub table columns;
inactive temperature and gain cells are grey. The third live plot shows actual
applied signed PWM, linked to all six temperature histories.

- **RAW_ZERO / RAW_POS:** `u = Ua + Ub*sin(phase)`. No temperature feedback,
  lookup or cooling multiplier. RAW_ZERO requires Ua=0, Ub>0; RAW_POS requires
  Ua>Ub>0. Raw plans use limit 100, independently of the existing comparison
  plans' limit 96. A raw peak above the selected limit is rejected, not clipped.
  The same measured-temperature limits, watchdogs and stop behavior apply.

- **OPEN:** piecewise-linear inverse of measured steady-state temperature vs signed
  PWM. No extrapolation. It is not a sine PWM and receives no second cooling multiplier.
- **P / PI:** raw command `Kp*error + Ki*integral(error dt)`; I is zero for P.
  Negative commands are multiplied by measured `chi_heat/chi_cool` **before** saturation.
  Anti-windup tests the compensated command against the applied PWM limit, allowing
  the integral to unwind. Changing control mode resets the integral; frequency-only
  transitions preserve it. STOP, completion and faults clear it.
- Calibration is loaded from `data/reference/module_04_steady_state.csv` by default.
  The heating/cooling susceptibilities and ratio (approximately **3.5035**) are
  calculated from its signed-PWM branches. These are provisional historical values;
  preserve the Module 4 settling audit and revalidate with the rod attached.
- A replacement calibration CSV may use the original table's columns, or
  `temperature_C,signed_pwm`. Temperatures and signed PWM must both strictly increase
  after exact duplicate points are removed. If both branches are present, loading
  it recalculates the ratio; otherwise enter an independently measured ratio.

## Preserved and added safety limits

The earlier **10–45 C TEC operating range remains in force** in both firmware and
plan validation. Every requested waveform must fit wholly inside it. The 60 C TEC
backup limit is retained; a measured T1 >= 56 C or missing T1 also stops output.
The physical interlock previously tripped on a 45 C run and remains independent.
The handout's 40 +/- 16 C waveform is rejected by this version. Do not bypass the
installed protections to run it; the lower-amplitude defaults are an adaptation.

Firmware stops both bridge outputs for an invalid TEC/base sensor, out-of-range
TEC temperature, T1 overtemperature, >2 s control interval, >2 s absent GUI heartbeat,
serial overflow, or completed schedule. Faults latch. A2–A5 remain measurement-only;
missing downstream probes are logged as nan without masking missing T1.
STOP is always accepted. Both bridge directions are set off before applying one.

## Programs and files

| Path | Purpose |
| --- | --- |
| `arduino/module_08_rod_controller/module_08_rod_controller.ino` | Sensors, validated commands, bridge outputs, complete fixed-format records |
| `arduino/module_08_rod_controller/angstrom_core.h` | Portable schedule, phase, lookup, P/PI and fail-off logic used by firmware and native tests |
| `python/rod_acquisition_gui.py` | Plan editor/uploader, live six-channel display, events, watchdog heartbeats and logging |
| `python/angstrom_plan.py` | Plan validation, measured calibration inversion and ratio, presets and command encoding |
| `python/rod_protocol.py` | Strict v2 parser with saved v1 temperature-record compatibility |
| `python/analysis/acquisition_check.py` | Data continuity/channel diagnostics and temperature plot; no Angstrom parameter fit |
| `python/analysis/cross_calibration_fit.py` | Optional actual common-bath correction fits; do not use heated-rod gradients as calibration |
| `python/pi_controller.py` | Earlier copied host-side arithmetic kept as reference; not used by the new firmware-controlled GUI |
| `python/test_*.py`, `python/tests_native/` | Fake-serial Qt tests, plan/parser tests and tests of the actual C++ firmware |
| `config/sensor_map.json` | Oscillatory geometry still pending measurement; old full-length map is reference only |

## Outputs and conventions

All acquisition outputs are created in `Module_8/data/raw/`, independent of the
launch directory. Each connection creates a unique file set:

- `module_08_rod_<timestamp>.csv`: LF-only parsed measurements and events.
- Same stem `.serial.log`: every incoming serial byte, including headers, events,
  malformed lines, acknowledgements and transitions, without editing.
- Same stem `_plan_01.json`, `_plan_02.json`, etc.: immutable upload snapshots,
  plan hash, sensor-map snapshot and source hashes. Configuration metadata
  includes purpose (comparison/single/rehearsal), calibration provenance and ambient method.

Missing sequence records and malformed records are counted and recorded. Logging
failure requests STOP and disables starting. Firmware independently stops if the
GUI no longer sends heartbeats. Startup and frequency transients stay in raw data;
accepted settled intervals are selected later in analysis, not deleted at acquisition.

Derived results go in `data/processed/`, corrections in `data/calibration/`, plots
in `figures/`, and report PDFs in `output/pdf/`. Prior-module raw data stays in its
original module. The reference calibration copy is not new Module 8 evidence.
Course notes remain in repository-root `docs/module_notes/` and `docs/assessments/`.

```bash
.venv/bin/python Module_8/python/analysis/acquisition_check.py Module_8/data/raw/<run>.csv
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s Module_8/python -t Module_8/python
```

The full 89-test suite includes the earlier 80 tests and nine raw-mode integration
and compatibility tests, plus expanded native-core safety and waveform checks.
The native tests compile the actual sketch/core with a host C++ compiler and do
not access hardware. Uno compilation also passes: 16,474 bytes flash and 1,238
bytes global RAM, leaving 810 bytes for locals/stack. Physical gain tuning,
interlock validation and the on-apparatus rehearsal remain to be performed.

## Experiment and deliverables

Include the raw zero-centered PWM trials at 100, 200 and 500 s and a positive-only
diagnostic. These are separate from calibrated OPEN temperature feedforward.
Then plan matched OPEN/P/PI comparisons at one period,
then another usable period with the selected controller. A qualifying comparison
trial can supply the first retained dataset. Otherwise repeat it. At each of two
usable periods, retain **at least five complete cycles after quantitative settling**,
with measurable amplitude and phase at **three or more rod sensors**. The short
rehearsal does not satisfy this requirement. See the runbook for acceptance checks.

| Date | Work |
| --- | --- |
| Nov. 4 | Pilot fits and production plan |
| Nov. 9 | Two-period production record and data-readiness check |
| Nov. 11 | A5 analysis checkpoint; check the course page/Moodle for the final submission deadline |
| Nov. 16 | P4 and runnable formative modeling-app check |
| Nov. 18–23 | Conductivity, heat transfer, uncertainty and model comparison |
| Nov. 30, 11:55 | C6 demonstration/receipt citing the frozen pushed analysis commit |
| Dec. 2 | F1 team slides before presentation; every member speaks and answers questions |

The offline analysis/model viewer is now implemented: `run_angstrom_analysis.command`.
It performs individual sinusoid fits, semi-infinite spatial slope fits, a complex
finite insulated-tip fit, conditional cycle-repeat uncertainty, transport
conversion, waveform/settling checks and residual inspection. See
[theory and usage](docs/theory_and_analysis.md). Measured periodic files, measured
oscillatory geometry and a complete systematic-error budget are still pending.

## Offline analysis (no Arduino connection)

```bash
Module_8/run_angstrom_analysis.command
.venv/bin/python Module_8/python/analysis/angstrom_fit.py --config Module_8/config/analysis_plan.json
```

The supplied analysis plan is a template, not measured evidence. Fill actual
periodic intervals and measured geometry first. Outputs preserve raw hashes,
actual tolerances, both spatial models and conditional fit errors. Missing rho/c
leave k/h uncomputed. No original acquisition or firmware file was changed by
this offline-analysis extension. The prior Module 7 near-steady result is kept
under `data/reference/module_07_selected_stationary.json` with its failed strict
criterion and fitted-ambient limitation attached.
