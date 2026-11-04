# Module 8 modeling app checkpoint

Status on 2026-11-04: Angstrom analysis/model fitting is not yet implemented.
Sinusoidal acquisition and firmware scheduling are implemented separately. `Module_8/python/analysis/acquisition_check.py`
is only an acquisition diagnostic, not the formative Angstrom modeling app.

The authoritative analysis will live in `Module_8/python/analysis/`, read original
Module 8 files, and save processed results and figures within Module 8. It must show:

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
