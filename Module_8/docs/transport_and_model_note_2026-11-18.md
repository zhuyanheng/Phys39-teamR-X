# Transport conversion and model consistency — November 18, 2026

Offline analysis only: no serial port, no hardware command, no raw byte modified. This
note performs the step that `five_period_review_2026-11-18.md` deliberately stops short of
(its summary records `material_constants: "k and h not computed"`) and adds three things the
same records can still support: the k/h conversion with sourced constants, an independent
mean-profile route to the lateral loss, and a measured actuator response at the drive
frequency.

## Reproduction

```sh
.venv/bin/python Module_8/python/analysis/transport_note.py
```

Inputs are the five frozen analyses `data/processed/five_period_review/m08_pi_p<period>s_analysis.json`,
the confirmed geometry in `config/sensor_map.json`, the raw PI records, and the Module 7
reference `data/reference/module_07_selected_stationary.json`. Their SHA-256 values, plus the
hash of this script and of `angstrom_fit.py`, are stored in the output JSON. The module reads
raw CSVs only inside the retained intervals and never rewrites them.

Outputs: `data/processed/transport_note/m08_transport_parameters.json`,
`m08_transport_summary.csv`, and five figures in `figures/transport_note/`.

## Material constants: assumptions, not measurements

| Quantity | Value | Bound used | Source |
|---|---|---|---|
| Density rho | 2700 kg/m3 | +/- 27 (1 %) | 6061-T6 handbook range 2680-2720 |
| Specific heat c | 896 J/(kg K) | +/- 18 (2 %) | 6061-T6 handbook range 890-900 |
| Diameter d | 0.01277 m | +/- 0.01 mm | reported caliper resolution |
| Conductivity k | compared with 166-172 W/(m K) | - | Lienhard Table A.1, used in A4 |

The bounds are treated as rectangular and converted with sqrt(3). Using the same table's
central value, k = 167 W/(m K) and rho c = 2.4192e6 J/(m3 K) imply kappa = 6.90e-5 m2/s;
the measured mean of 6.80e-5 m2/s is 1.5 % below that, so the material set is at least
internally consistent. **These constants must be replaced by a cited source with stated
uncertainties before C6 quotes k or h as measured values.**

## Results

| Period (s) | q (1/m) | q' (1/m) | m = sqrt(q^2-q'^2) | kappa (1e-5 m2/s) | cond. | k (W/(m K)) | h from q,q' (W/(m2 K)) | m from mean fit (1/m) | h from mean fit |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 21.26 | 21.89 | - | 6.75 | - | 163.3 +/- 5.7 | not defined | 5.34 | 14.9 |
| 200 | 15.65 | 15.06 | 4.27 | 6.66 | 25.9 | 161.2 +/- 5.6 | 9.4 +/- 4.2 | 6.11 | 19.2 |
| 300 | 12.75 | 12.04 | 4.20 | 6.83 | 17.4 | 165.1 +/- 9.4 | 9.3 +/- 7.3 | 5.93 | 18.5 |
| 400 | 11.42 | 9.84 | 5.80 | 6.99 | 6.8 | 169.2 +/- 6.6 | 18.2 +/- 4.5 | 5.99 | 19.4 |
| 500 | 10.52 | 8.85 | 5.68 | 6.75 | 5.8 | 163.4 +/- 8.7 | 16.9 +/- 4.5 | 6.38 | 21.2 |

`cond.` is (q^2+q'^2)/|q^2-q'^2|, the factor by which relative errors in q and q' are
amplified in m^2 and therefore in nu. kappa mean = 6.80e-5 m2/s; span across periods 4.9 %;
largest pairwise difference 1.43 x the combined fit SE. k = 164.5 W/(m K) at the mean kappa.

## What these records establish

**F1. kappa is over-determined and consistent.** Five independent periods agree to 4.9 %,
and no pair disagrees by more than 1.5 combined standard errors. The implied
k = 161-169 W/(m K) brackets the 166-172 W/(m K) tabulated range for 6061-T6, so the
oscillatory method reproduces the accepted value without being told it. This is the
strongest result in Module 8 and it does not depend on the ambient temperature. Averaging
does not shrink the bar: the dominant terms (position, material) are common to all five
periods, so the defensible statement is k = 164.5 W/(m K) with a common systematic of
roughly 6-9 W/(m K), i.e. 4-5 %.

**F2. nu is not over-determined, and its ordering is explained by conditioning.** The
amplification factor is 5.8-6.8 at 400-500 s but 17-26 at 200-300 s, and the m^2 estimate
degenerates at 100 s. The 200/300 s pairs therefore give h = 9.3-9.4 W/(m2 K) while the
better-conditioned 400/500 s pairs give 16.9-18.2. The difference is a conditioning and
drift effect, not physics, and the pair with the worse conditioning is the one that
disagrees with the independent route in F3.


**F3. The mean profile supplies an independent route to the same loss.** Fitting
a(xi) = T_inf + (a0 - T_inf) cosh[mu(1-xi)]/cosh(mu) to all five sensors gives
m = 5.3-6.4 1/m with residuals of 0.11 C, and, with the same kappa,
h = 15-21 W/(m2 K) at the fitted ambient. At 400 s the two routes agree to 7 % in h and 3 %
in m; at 200/300 s the oscillatory value is roughly half the mean-profile value. This is the
first time the Module 7 and Module 8 routes have been compared on Module 8 data.

**F4. The 400 s record is the internally consistent one.** It is the only record where
m from the two routes, h from the two routes, and the Module 7 values (4.83-6.78 1/m) all
overlap. C6 should quote 400 s as the primary dataset and present the other periods as
consistency checks rather than as five equal measurements.

**F5. Ambient is fitted, not measured, and it dominates the mean route.** The fitted T_inf is
24.1-25.7 C at every period, which is self-consistent but is not a measurement. Fixing
T_inf at 20/22/24/26/28 C moves m from about 3.6-4.0 to 7-17 1/m, and h scales as m^2
(6.7-8.6 / 8.6-11.5 / 12-17 / 21-34 / 67-154 W/(m2 K) for those five choices). Without a
room thermometer the mean-profile route cannot produce an absolute h; only the oscillatory
route can.

**F6. The measured actuator is far from static.** From the raw records,
|dT_A0/dPWM| / chi_static = 0.165, 0.356, 0.482, 0.558, 0.635 at 100-500 s, with lag
1.18, 1.02, 0.87, 0.77, 0.68 rad. The OPEN feedforward inverts a static curve, so at 200 s it
under-delivers the requested 5 C (measured TEC amplitude 1.77 C, ratio 0.354); the PI runs
deliver 4.69-4.87 C by raising the PWM amplitude to 57/27/20/18/15 counts. This is the
quantitative reason the course insists on optimising the waveform from pilot data instead of
trusting the static susceptibility, and it is the missing half of the OPEN/P/PI comparison.

**F7. Boundary tracking is good and the finite-length picture is frequency dependent.**
T1 follows the requested sinusoid to 2.0-4.0 % rms (gate 10 %). The complex finite-length
error at 400 s is 0 / 0.4 / 1.6 / 5.4 / 16 % at T1-T5, so the semi-infinite approximation
fails at T4-T5 for long periods; at 100 s it is below 3.5 % everywhere, because 1/q shrinks
with period. Bi_perp = 1.8-3.4e-4 wherever m^2 > 0, so the one-dimensional assumption holds.
At 100 s m^2 < 0 makes Bi_perp meaningless; `angstrom_fit.py` currently writes a negative
Bi_perp there, which should be suppressed rather than reported.

**F8. A fixed spatial residual appears at every period.** The mean-profile residuals are
-0.06, +0.15, -0.06, -0.13, +0.11 C at T1-T5, identical at all five periods to better than
0.01 C. This is not drift: it is a static discrepancy that looks like a per-probe offset or a
position error at T2/T3, exactly the pair that sets the spatial slope. It is the one
systematic that a common-bath cross-calibration and a re-measured position table would
remove, and it maps directly into q and therefore into kappa.

## What these records do not establish

- No record passes the provisional settled-periodic spans, so every number above is a
  diagnostic estimate with drift-dominated systematics. The single-cycle spread of kappa is
  10.6-27.0 %, five to ten times the pooled fit SE; that spread, not the SE, is the honest
  scale of the period-to-period reliability.
- The 100 s sign of nu depends on the estimator: the five-cycle pooled finite-rod fit gives
  m^2 < 0, while the per-cycle spatial fits give nu = +1.9e-4 to +7.1e-4 1/s. No h is
  reported there.
- There is no common-bath cross-calibration, so a per-channel gain bias is not bounded; F8
  suggests one exists.
- The scan skew is an assumed 0.17 s, not a measured value; it contributes 3-20 % of the h
  budget at 200-500 s.
- The material constants are handbook values, not measurements of this rod.
- `five_period_review.py` still reports "k and h not computed". This note supersedes that
  field; if the team prefers one pipeline, add the `material` block to that script's plan
  dictionary and the two k/h columns to its summary, then regenerate.

## Figures

| File | Content |
|---|---|
| `m08_transport_kappa_nu.png` | kappa with the literature band and the single-cycle spread; nu with conditioning factors and the unphysical 100 s point |
| `m08_transport_k_h.png` | k against the tabulated range; h from both routes against the provisional 10 W/(m2 K) |
| `m08_mean_profile_fit.png` | normalised mean profile with the finite insulated-tip fit, and the repeated residual pattern of F8 |
| `m08_actuator_frf.png` | measured absolute dT/dPWM relative to the static susceptibility, and the measured lag, versus period |
| `m08_spatial_per_sensor.png` | amplitude decay and phase lag at all five sensors, showing the T5 departure from the T1-T4 line |

## Missing measurements this analysis exposes

1. **Room temperature and its drift** (highest value). Removes the F5 degeneracy, makes the
   mean profile absolute, and lets the finite-rod fit provide a real h cross-check.
2. **Common-bath cross-calibration** of all six channels with the 0.2 C criterion, to convert
   F8 from a suspicion into a bounded correction.
3. **Re-measured position table with uncertainties**, because +-1 mm alone moves kappa by
   2.5-2.6 % and the T2/T3 residual pattern is position-like.
4. **Measured scan skew** (or an interleaved/duplicated-channel test) instead of the assumed
   0.17 s.
5. **One repeat of the 200 s or 400 s programme with a longer settle**, to test whether the
   cycle spread is environmental drift or a slow transient of the apparatus.
6. **100 s OPEN and P trials at the same mean and amplitude as PI**, to complete the control
   comparison at the period the course specifies.
7. **A slow static ramp with the rod attached**, to revalidate the heat/cool ratio and the
   feedforward curve, which are still Module 4 values.
