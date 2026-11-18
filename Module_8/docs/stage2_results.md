# Module 8 Stage 2 — setups, completed simulation table and measured plots

The six-row table below contains mathematical simulations, not laboratory measurements. The Module 6 solver was copied without changes; the Module 8 adapter supplies sinusoidal raw PWM. Run the GUI with `../run_simulation.command`.

Common simulation setup: one-lump process, raw open-loop sine, room = initial = 22 °C, thermal time constant = 80 s, χh = 0.46 °C/PWM, Ua = 0, Ub = 50 PWM, dt = 0.05 s and PWM limit = 255. There is no feedback or cooling compensation. Kp/Ki and anti-windup are inactive in this raw mode. The limit is a simulation setting, not a proposed hardware limit. H = 1 is an arbitrary normalization, with C = Hτ and P_u = Hχ.

## Completed S18.3 simulation table

| Case | Period (s) | χc (°C/PWM) | Mean − room (°C) | Fundamental amplitude (°C) | Phase lag vs PWM (°) | Simulated duration (s) |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 100 | 0.23 | 3.660 | 3.367 | 78.84 | 1000 |
| 2 | 100 | 0.46 | 0.001 | 4.489 | 78.83 | 1000 |
| 3 | 200 | 0.23 | 3.661 | 6.379 | 68.34 | 2000 |
| 4 | 200 | 0.46 | 0.000 | 8.505 | 68.34 | 2000 |
| 5 | 300 | 0.23 | 3.661 | 8.843 | 59.19 | 3000 |
| 6 | 300 | 0.46 | 0.000 | 11.790 | 59.19 | 3000 |

Values are numerical first-harmonic fits to the final five complete simulated cycles of each ten-cycle run. The CSV also retains residual RMS and per-cycle spans. Duration is a budget, not a settling definition. Independent Fourier predictions agree within 0.004 °C in mean, 0.006 °C in amplitude and 0.1° in phase; the small remaining differences include forward-Euler error and finite startup decay.

At fixed PWM amplitude, a longer period increases temperature amplitude and reduces phase lag. Unequal heating/cooling susceptibility raises the mean above room temperature and adds waveform distortion. The exact steady fundamental uses χavg=(χh+χc)/2: B=χavg·Ub/sqrt(1+(ωτ)²), lag=atan(ωτ), and mean−room=Ub(χh−χc)/π for Ua=0. These are checks on this piecewise-linear model, not measured material parameters.

## Analytical startup check

For χh=χc=χ and Ua=0, let a=χUb/[1+(ωτ)²], b=−aωτ. Then T(t)=Troom+a sin(ωt)+b cos(ωt)+C exp(−t/τ), with C=Tinitial−Troom−b. At t=0 this gives Tinitial. Substitution yields τ d(T−Troom)/dt+(T−Troom)=χUb sin(ωt): the homogeneous term cancels and the sine/cosine coefficients satisfy a−ωτb=χUb and b+ωτa=0. The dashed overlay retains this startup term.

## Measured Stage 2 records

| Mode | Period (s) | Ua / Ub (PWM) | Fit cycles | TEC mean (°C) | Fundamental amplitude (°C) | Lag vs applied PWM (°) | Fit RMS (°C) |
|---|---:|---|---|---:|---:|---:|---:|
| RAW_ZERO | 300 | 0 / 50 | 1–2 | 29.832 | 7.870 | 47.65 | 0.789 |
| RAW_ZERO | 200 | 0 / 50 | 4–6 | 28.191 | 5.983 | 57.68 | 0.594 |
| RAW_ZERO | 100 | 0 / 50 | 7–9 | 28.558 | 3.581 | 67.79 | 0.338 |
| RAW_POS | 100 | 32 / 5 | 7–9 | 37.918 | 0.544 | 71.59 | 0.072 |

Measured plots retain the RUNNING history including startup; only time origins are shifted to each STEP event. Shading identifies descriptive fitting intervals. The 300 s record contains only two complete cycles plus a partial tail; its fit includes startup and is diagnostic. The other records use their final three complete cycles, with per-cycle spans saved for review. These figures do not certify settling.

The 100 s positive-only trial uses Ua=32, Ub=5 PWM, whereas its zero-centered baseline uses Ua=0, Ub=50 PWM. The amplitude was reduced for safety and the mean operating temperature changed. Absolute residual reductions therefore cannot isolate polarity reversal. Inspect RMS/B as well as absolute residuals; do not equate a smaller absolute residual with a uniquely identified mechanism. The positive-only measured mean is reported as measured, not relabelled 40 °C.

Room temperature was not recorded during these measurements. The prescribed 22 °C simulation input is not substituted for the missing lab ambient. A fully matched measured-ambient simulation/experiment comparison remains qualified by this missing input.

## Files

- [Completed five-column worksheet (CSV)](../data/processed/stage2/m08_stage2_s18_3_filled_table.csv)
- [Simulation fit diagnostics (CSV)](../data/processed/stage2/m08_stage2_s18_3_simulation_table.csv)
- [Measured metrics (CSV)](../data/processed/stage2/m08_stage2_measured_metrics.csv)
- [Zero-centered measured curves](../figures/stage2/m08_stage2_s18_3_measured_zero_pwm.png)
- [100 s measured zero/positive comparison](../figures/stage2/m08_stage2_s18_4_measured_100s_comparison.png)
- [Six simulation curves](../figures/stage2/m08_stage2_s18_3_six_simulations.png)
- [Analytical/numerical comparison](../figures/stage2/m08_stage2_s18_3_analytical_check.png)

Each figure has a PDF counterpart. Full simulated startup histories and setup/hash receipts are in `../data/simulation/s18_3/`. Original measured CSVs are unchanged.

Reproduce all plots and tables: `.venv/bin/python Module_8/python/analysis/stage2_raw_pwm.py` from the repository root.

[Course Stage 2 instructions](https://sethfraden.github.io/Phys39F26-course/labs/lab-09/#stage-2-explore-uncompensated-sinusoidal-pwm). The focused Stage 3 P/PI comparison uses a separate six-sensor rod simulator; the copied one-lump simulator is not a substitute for it. Codex generated the working figures and calculations; review the evidence and explain the model in your own account.
