# Module 8: theory, offline analysis, and actual-data requirements

## Scope and relationship to A4

A4 is the individual Module 7 Parts I/II theoretical prediction. Its inputs are
measured geometry, literature k and provisional h=10 W/(m2 K). It needs no
Module 8 temperature data. Module 8 instead measures sinusoidal amplitudes and
phases to estimate diffusivity and lateral loss independently. A5, not A4, is
the individual Angstrom derivation/measurement-plan assignment.

## Derivation and units

Let theta=T-T_inf. Energy conservation, axial Fourier conduction and linear
side cooling give

    rho*c*A*d(theta)/dt = k*A*d2(theta)/dx2 - h*P*theta
    d(theta)/dt = kappa*d2(theta)/dx2 - nu*theta
    kappa = k/(rho*c) [m2/s]; nu = h*P/(rho*c*A) [1/s].

Every term in the second line has units K/s. Put the settled oscillation in
complex form F(x)*exp(i*omega*t), omega=2*pi/period [rad/s]. Substitution gives
F''-s2*F=0, s2=(nu+i*omega)/kappa. Write s=q+i*q_prime, with both coefficients
in 1/m. Equating real and imaginary parts gives

    q2-q_prime2 = nu/kappa = m2
    2*q*q_prime = omega/kappa
    kappa = omega/(2*q*q_prime)
    nu = kappa*(q2-q_prime2).

For a semi-infinite rod, F(x)/F(0)=exp[-(q+i*q_prime)*x]. Thus log amplitude
and phase have slopes -q and -q_prime when the fitted sinusoid is
T=a+B*cos(omega*t+phase). More negative phase is downstream lag. With no side
loss, q=q_prime. Negative inferred nu is preserved and flagged, not clamped.

The finite insulated-tip response is instead

    F(x)/F(0) = cosh[s*(L-x)]/cosh(s*L).

It satisfies F(0)=F0 and F'(L)=0. The numerical implementation uses the stable
exponential form exp(-s*x)*(1+exp[-2*s*(L-x)])/(1+exp[-2*s*L]). It fits this
complex response to the independently fitted per-sensor amplitudes/phases,
referenced to the measured T1. TEC setpoint and A0 are never substituted for T1.
Linear semi-infinite spatial fits are also retained as a comparison. This is a
two-stage analysis: individual time fits, followed by spatial fits, not a global
fit that hides poor individual waveforms.

Convert to material/air properties only with sourced rho and c:

    k = rho*c*kappa [W/(m K)]
    h = nu*rho*c*A/P = nu*rho*c*d/4 [W/(m2 K)].

The stationary and periodic results should agree on m2=nu/kappa, subject to
uncertainty and different ambient/airflow conditions. The three characteristic
lengths are 1/m (mean), 1/q (amplitude) and 1/q_prime (one radian of phase lag).
Separate checks are complex finite-vs-infinite response error at each selected
position and Bi_perp=(q2-q_prime2)*(d/4)^2 for radial consistency. A small radial
Biot number does not establish a semi-infinite rod.

## Programs and exact usage

`Module_8/run_angstrom_analysis.command` opens the **offline** viewer. It has no
serial imports. Load/save an analysis plan, choose a real Module 8 CSV and a
measured oscillatory sensor-map JSON, and fit the saved plan. It displays raw
six-channel histories, the retained interval, log amplitude and phase fits,
conditional parameters, and individual/finite-model time residuals.

The command-line equivalent is:

    .venv/bin/python Module_8/python/analysis/angstrom_fit.py \
        --config Module_8/config/analysis_plan.json

The supplied plan is explicitly a template. Replace its raw filename and times,
justify its settling/noise thresholds and supply actual x_m/L in sensor_map.json.
The map remains pending: full-length Module 7 coordinates are reference only.
No real Module 8 periodic record has been collected in this task.

The fitter refuses a Module 7 constant-setpoint schema, unknown geometry,
clock reset/duplicates, large gaps, missing retained probes, safety/stopped
intervals, changes of period/control mode/plan/step, fewer than five complete
cycles, fewer than three retained rod sensors, or an inadequate amplitude fit.
Mean/amplitude/phase spans across complete cycles test the selected interval
against explicit supplied settling tolerances; failing intervals are diagnostic.
Boundary first-harmonic residuals quantify distortion. Rho/c remain null until
sourced values are supplied, so k/h are not invented.

Outputs are `<plan>_angstrom.json` in Module_8/data/processed and one spatial
fit/residual figure per interval in Module_8/figures. The JSON preserves source,
plan, geometry and analysis hashes, excluded tails, individual coefficients and
residuals, both spatial models, finite-end checks and cross-frequency consistency.
Raw CSV bytes are verified unchanged. Output regeneration replaces derived files,
never raw measurements.

## Uncertainty and limits of software completion

Repeated-cycle q/q_prime covariance is propagated into kappa and nu; their
correlation is retained. The optional first-order input budget also accepts relative-position covariance
(or independent position standard errors), L, d, period, rho and c standard
uncertainties. Missing inputs are listed explicitly, with a completeness flag;
partial errors are labelled known components. These are **not complete
measurement uncertainties** without the missing experimental inputs.
The final C6 budget must additionally propagate measured position/L/d errors,
forcing-period error, material-property errors, sensor offsets/contact, phase
branch choice, sequential ADC scan timing and systematic model error. The caliper
specification 0.01 mm is not automatically a standard uncertainty. These missing
experimental inputs cannot be completed by treating software tests as data.

Independent room temperature is absent in the latest Module 7 record. Oscillation
amplitude/phase fits include their own fitted means and do not need an assumed
room temperature; mean excess-temperature comparisons must preserve that gap.
The reconstruction compares oscillations about the measured per-sensor means;
it does not independently validate the stationary mean-profile model.

The minimum operational Part I production target remains two usable periods,
with >=5 complete accepted cycles and >=3 useful rod sensors at each, plus the
matched OPEN/P/PI comparison and measured T1 waveform check. The later Part II
page mentions a one-frequency minimum with additional frequencies as an extension;
use the stricter current Part I two-period acquisition plan unless the instructor
explicitly revises it. No new hardware upload/start was performed here.

## Sources and AI assistance

- Part I: https://sethfraden.github.io/Phys39F26-course/labs/lab-09/
- Part II: https://github.com/SethFraden/Phys39F26-course/blob/main/course/labs/lab-10/index.md
  (read from the connected GitHub source on 2026-11-04).
- Current A4 deadline: student-provided Moodle text, Nov. 9, 2026, 09:05 AM.

Codex implemented the offline mathematical analysis, viewer and synthetic tests.
Synthetic data is used only in temporary test directories and never presented
as a measured Module 8 result. Students must review and explain the inference.

For the numeric input budget, provide `position_uncertainty_m` (five values,
first zero) or `position_covariance_m2` (5x5, first row/column zero),
`analysis_length_standard_uncertainty_m` and `diameter_standard_uncertainty_m`
in the measured map. Provide `period_standard_uncertainty_s` per interval and
`density_standard_uncertainty_kg_m3` / `specific_heat_standard_uncertainty_J_kgK`
in its material object. Position values are relative coordinates. No such
standard errors are inferred automatically from the caliper precision.
