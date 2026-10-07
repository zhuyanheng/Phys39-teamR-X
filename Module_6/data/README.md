# Module 6 derived analysis

These files are derived from unchanged Module 4 and 5 data. Reproduce with `.venv/bin/python Module_6/python/analysis/module_06_analysis.py` from repository root.

- `susceptibility.csv`: two provisional directional fits and endpoint sensitivity.
- `time_constants.csv`: six 63.2% estimates and endpoint sensitivity (not confidence intervals).
- `open_loop_comparison.csv`: H3/C1 endpoint predictions and trace RMSE.
- `p_droop_comparison.csv`: raw-recomputed experimental and theoretical droop, loop gain and tau_cl.
- `simulation_metrics.csv`: **simulated**, target-based transient metrics. Blank rise/settling means not reached in the finite run; blank zeta means not applicable to P.
- `simulation_*.csv`: official v3 StepResult samples exported every 0.5 s, from dt=0.1 s integration. Temperature is post-step; PWM is the command used for that step. Continuous simulated PWM differs from integer hardware PWM.
- `windup_comparison.csv`: simulation-only unreachable-setpoint test, not physical data.
- `numerical_checks.csv`: dt-halving and analytical error checks; blank analytical error means not evaluated for PI.
- `analysis_results.json`: exact parameters, results, URLs and source SHA256 values. H=1 is arbitrary normalization, not measured conductance.

No physical PI experiment is present. Read the Module 6 note and existing Module 4 audit before using calibration as final equilibrium evidence.
