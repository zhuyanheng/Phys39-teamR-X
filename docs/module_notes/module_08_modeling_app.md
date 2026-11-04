# Module 8 modeling app checkpoint

Status on 2026-11-04: offline Angstrom analysis/model fitting and its Qt viewer are implemented. Actual periodic measurements and the full systematic-error budget are pending.
Sinusoidal acquisition and firmware scheduling are implemented separately. `Module_8/python/analysis/acquisition_check.py`
is only an acquisition diagnostic, not the formative Angstrom modeling app.

The authoritative offline analysis lives in `Module_8/python/analysis/`, read original
Module 8 files, and save processed results and figures within Module 8. Its supported workflow and remaining experimental requirements are:

- imported raw data, selected settled intervals and excluded data with reasons;
- requested and measured TEC/base waveforms and boundary tracking metrics;
- per-sensor sinusoid fits, amplitudes, unwrapped phases and residuals;
- spatial fits, q and q_prime with units and uncertainty;
- kappa = omega/(2*q*q_prime), nu = kappa*(q*q - q_prime*q_prime);
- k = rho*c*kappa and h = nu*rho*c*A/P, with input sources and uncertainty;
- finite-length error and transverse-Biot checks for the retained sensors;
- frequency consistency, measured/modelled T(x,t), and limitations;
- exact reproduction steps, code version, data identity and meaningful AI assistance.

AI assistance during setup: Codex copied the earlier acquisition baseline,
made controller imports local, redirected output paths, removed old geometry
labels from new-run diagnostics, and wrote the setup/run-plan documentation.
No measurements or fitted Module 8 results were generated.

Additional AI assistance: Codex implemented the firmware schedule/control core,
GUI plan editor/uploader, measured lookup/ratio handling, versioned serial/logging
and safety stops, with native firmware tests, fake-serial Qt tests and Uno compilation.
Physical tuning and actual experiment validity remain unverified.

## Implemented entry points

- `Module_8/run_angstrom_analysis.command`: offline configuration and result viewer.
- `Module_8/python/analysis/angstrom_fit.py`: reproducible CLI and mathematical core.
- `Module_8/config/analysis_plan.json`: explicitly unfilled measurement-plan template.
- `Module_8/docs/theory_and_analysis.md`: derivation, formulas, tests and limits.

Time-series fits feed both semi-infinite slopes and a finite insulated-tip
complex spatial fit. The latter supplies the reported transport parameters;
semi-infinite results remain available for comparison. No measurement or
geometry was invented to populate the viewer. Supplied geometry/material/period standard errors can be propagated in the
optional numeric input budget; unknown components are explicitly listed and
kept separate from conditional repeat-cycle fit errors.
