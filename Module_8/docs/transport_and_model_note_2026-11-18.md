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

| Period (s) | q (1/m) | q′ (1/m) | κ (10⁻⁵ m²/s) | Initial TEC (°C) | Mean-profile m (1/m) | Mean-profile h (W/m²K) | Ruler scenario range for mean-profile h (W/m²K) | Oscillatory h (W/m²K) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 21.26 | 21.89 | 6.75 | 24.13 | 5.36 | 14.96 | 14.16–15.78 | — |
| 200 | 15.65 | 15.06 | 6.66 | 24.02 | 4.90 | 12.37 | 11.78–12.97 | 9.36 |
| 300 | 12.75 | 12.04 | 6.83 | 23.90 | 5.67 | 16.94 | 16.16–17.73 | 9.30 |
| 400 | 11.42 | 9.84 | 6.99 | 22.99 | 4.56 | 11.24 | 10.67–11.84 | 18.16 |
| 500 | 10.52 | 8.85 | 6.75 | 25.25 | 5.97 | 18.61 | 17.67–19.59 | 16.86 |

The conditioning factor is (q^2+q'^2)/|q^2-q'^2|, the factor by which relative errors in q and q' are
amplified in m^2 and therefore in nu. kappa mean = 6.80e-5 m2/s; span across periods 4.9 %;
largest pairwise difference 1.43 x the combined fit SE. k = 164.5 W/(m K) at the mean kappa.

## What these records establish

**F1. kappa is over-determined and consistent.** Five independent periods agree to 4.9 %,
and no pair disagrees by more than 1.5 combined standard errors. The implied k = 161–169 W/(m K) overlaps the 166–172 W/(m K) reference range.
Geometry and material inputs are shared across periods, so averaging does not remove their systematic effects.
The confirmed ruler bound is applied to five recorded gaps. Its 32 sign combinations give κ ranges with
half-widths of roughly 5% relative to the nominal values. These ranges are separate from the conditional
uncertainty bars. The listed parameter estimates remain diagnostic under the original cycle checks.

**F2. nu is not over-determined, and its ordering is explained by conditioning.** The
amplification factor is 5.8-6.8 at 400-500 s but 17-26 at 200-300 s, and the m^2 estimate
degenerates at 100 s. The 200/300 s pairs therefore give h = 9.3-9.4 W/(m2 K) while the
better-conditioned 400/500 s pairs give 16.9-18.2. Sensitivity and drift can contribute to the difference. Comparing with the mean-profile route requires checking the room reference for each run.


**F3. The mean-profile fit uses the initial TEC reference.** As specified on November 20,
the first finite TEC measurement in each acquisition sets `T∞`. For the five PI records these
readings were taken while IDLE with zero PWM. We fit the finite insulated-tip mean profile to all five
rod means with the base mean free and `T∞` fixed. The fit gives m = 4.56–5.97 1/m with
residual RMS of 0.107–0.112 °C. The h estimates combine that m with the same κ used in the
oscillatory analysis. They therefore share the κ input.

**F4. The room reference changes the comparison.** At 400 s the mean-profile estimate falls to
11.24 W/(m² K), compared with 18.16 W/(m² K) from the oscillatory fit. At 500 s the corresponding
estimates are 18.61 and 16.86 W/(m² K). The earlier free-ambient fit showed closer agreement at
400 s. That agreement depended on allowing the room reference to vary in the fit.

**F5. The room reference describes the TEC at acquisition startup.** Independent air temperature
and drift are unknown. Initial TEC temperature can retain heat from previous operation. For example,
the November 18 P-only run starts at 29.31 °C. The source row for each acquisition is in the
[room-reference record](../data/processed/m08_initial_tec_room_references.json).
The JSON also retains fixed-temperature sensitivity scenarios for the mean-profile fit.

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

**F8. The mean-profile residuals have a recurring spatial pattern.** T2 residuals range
from +0.15 to +0.18 °C and T4 residuals from −0.14 to −0.13 °C. Channel offsets,
probe placement, contact and model discrepancy can all contribute. The analysis uses the
recorded channel readings directly, per the operator’s decision to skip common-bath calibration.

## What these records do not establish

- No record passes the provisional settled-periodic spans, so every number above is a
  diagnostic estimate with drift-dominated systematics. The single-cycle spread of kappa is
  10.6-27.0 %, five to ten times the pooled fit SE; that spread, not the SE, is the honest
  scale of the period-to-period reliability.
- The 100 s sign of nu depends on the estimator: the five-cycle pooled finite-rod fit gives
  m^2 < 0, while some per-cycle spatial fits return positive loss. The pooled oscillatory
  result has no physical h at 100 s. The mean-profile h in the table uses the initial TEC reference.
- Channel-dependent offsets and gains remain unquantified.
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
| `m08_mean_profile_fit.png` | normalised mean profile with the initial TEC reference, finite insulated-tip fit and residuals |
| `m08_actuator_frf.png` | measured absolute dT/dPWM relative to the static susceptibility, and the measured lag, versus period |
| `m08_spatial_per_sensor.png` | amplitude decay and phase lag at all five sensors, showing the T5 departure from the T1-T4 line |

## Measurement decisions

The start-of-acquisition TEC reference is used throughout the current analysis. The team chose to
skip the six-channel common-bath calibration. The original ±1 mm ruler error is documented and
included as a per-gap sensitivity bound for positions and L. Absolute ambient temperature and drift,
probe contact, and scan timing still limit interpretation of the uncertainty. The 100 s scalar
feedforward and P-only trials already have recorded data.
