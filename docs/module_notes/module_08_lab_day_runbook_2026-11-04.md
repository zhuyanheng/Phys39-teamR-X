# Module 8 lab runbook

Sources: [Part I](https://sethfraden.github.io/Phys39F26-course/labs/lab-09/)
and [Part II](https://sethfraden.github.io/Phys39F26-course/labs/lab-10/).
This is a plan, not a record of completed measurements.

## First resolve software and geometry

The new firmware and GUI implement this sequence. Upload the Module 8 sketch
first, then connect at 115200 baud, edit a plan, Upload, and explicitly Start.
Use the retained 10–45 C range; defaults are 35 +/- 5 C rather than the larger
handout waveform. Preserve the installed interlock and all software protections.

1. Verify channel labels, prior sensor checks and temperature/PWM conventions.
2. Put T1 at the first hole for x = 0; initially place T2–T5 about one inch apart.
   Measure every coordinate, uncertainty, diameter and distance from the origin to
   the tip. Save a diagram/photo and a separate oscillatory sensor map.
3. Establish room temperature and its measurement/estimation method. Preserve limitations.
4. Load the measured heat/cool calibration; form the inverse temperature-to-PWM
   lookup and compute the measured heating/cooling ratio.
5. Verify six live traces and saved complete records, including control mode,
   setpoint, raw command, compensated/applied PWM, run state and forcing parameters.

## Software rehearsal (does not count as a periodic dataset)

Choose the short-rehearsal preset and run a three-step check that
demonstrates at least two automatic frequency changes, continuous phase,
correct metadata, uninterrupted logging and zero output on completion. Restore
the intended durations before collecting production data. Label rehearsal records.

## Four planned physical measurement segments

| Segment | Action | Decision/evidence |
| --- | --- | --- |
| 1 | Calibrated open-loop trial at the first period | Is measured T1 sinusoidal? Save mean, amplitude, phase, asymmetry, distortion and PWM |
| 2 | P-only trial at the same mean, amplitude and period | Compare with segment 1; document Kp and compensation |
| 3 | PI trial at the same mean, amplitude and period | Compare with segments 1–2; document Kp, Ki, compensation, saturation and anti-windup |
| 4 | Second usable period with the selected controller | Retune if needed; preserve the frequency transition and independently select its settled interval |

The prescribed starting trial is Ta = 40 C, Tb = 16 C, period = 100 s,
subject to the measured rod-base limit and installed protections. This is the
handout's starting trial, **rejected by the retained 10–45 C operating range**. The GUI default
is the lower-amplitude 35 +/- 5 C adaptation.
If tracking is poor, the handout suggests 150 s and/or Tb = 10 C; changing
frequency or amplitude requires retuning. Periods below 100 s are prohibited.
Keep mean/amplitude fixed when comparing control modes and, where practical, periods.

One of segments 1–3 may also count as the first accepted periodic dataset.
If none qualifies, repeat that period with improved settings. If comparing the
three controllers at changed settings, rerun matched trials before interpreting
their differences as a controller effect. More periods/repeats are driven by
pilot evidence and class time, not by an arbitrary number of runs.

## Acceptance gate at each retained period

- Specify a numerical settling criterion before selecting the accepted interval:
  evaluate repeat-cycle means, amplitudes, phases and residuals. Any numerical
  tolerances chosen by the team must be justified by noise and the fit requirements.
- After that criterion passes, retain at least five complete cycles.
- At least three rod sensors must have measurable amplitude and phase.
- Inspect measured T1, rather than assuming the TEC request was reproduced.
- Preserve startup, transients, frequency/mode changes, malformed-record counts,
  restarts and safety events. Do not overwrite raw measurements with corrections.
- Stop safely and verify the saved file before ending the session.

The minimum retained production duration is `5*tau1 + 5*tau2`, in addition to
settling, control comparisons and transitions. For periods 100 s and 150 s this
is 1250 s (20 min 50 s) of accepted data, **not** the whole experiment duration.
These are illustrative periods; the second period must be selected from actual pilot results.

## Analysis and submission

1. Fit each retained trace for mean, amplitude and phase; unwrap phase consistently.
2. Fit ln(amplitude) vs position and unwrapped phase vs position for q and q_prime.
3. Infer kappa and nu, propagate uncertainty, inspect residuals and compare frequencies.
4. Carry forward finite-length and transverse-Biot checks; update them using measured parameters.
5. Calculate k and h, compare stationary/periodic estimates, reconstruct measured T(x,t),
   discuss systematic errors, and preserve reproducible code and evidence for C6/F1.

Individual A5 is due Nov. 11 at 09:05. P4 and the formative analysis-code check
are Nov. 16; C6 is Nov. 30 and F1 is Dec. 2. See Module 8 README for file conventions.
