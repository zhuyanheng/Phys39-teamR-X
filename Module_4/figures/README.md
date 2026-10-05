# Module 4 Part 4 figure index

The generated figure files live in this directory, matching the per-module layout used for Modules 1–3.

The figures were generated from the provisional ten-row [`steady_state.csv`](../../data/module_04/steady_state.csv) with:

```text
python3 Module_4/python/plot_a2.py data/module_04/steady_state.csv --criterion 'Provisional 20-s means; revised 3τ + 1-min steady test pending' --heat-fit 0 45 --cool-fit 0 96
```

Outputs: [`heating_trace.svg`](heating_trace.svg) uses H3; [`cooling_trace.svg`](cooling_trace.svg) uses C1. Each shows the command interval and green selected 20-second averaging window, **not** necessarily the full revised steady-state observation interval. Retain these as supporting class evidence. The revised 1–2 page A2 PDF needs the [`steady_temperature_vs_pwm.svg`](steady_temperature_vs_pwm.svg) graph: negative x for COOL, positive x for HEAT, blue/red measured points, dashed fits, labeled axes/units, and the actual steady criterion. H0/C0 overlap at x=0. Open H4/C4 endpoints mark instructor-approved course-range exceptions, included in the fits and identified in the graph caption. Replot after revalidating Part 3.

The 0–45 HEAT and −96–0 COOL points are approximately linear over the observed settings (R² 0.9990 and 0.9991). The signed-x slopes are `m_h = +0.4954 °C/PWM count` and `m_c = +0.1414 °C/PWM count`; `r = m_h/|m_c| = 3.5035`. Positive `m_c` is correct when COOL lies on negative signed x; against nonnegative COOL magnitude its slope is −0.1414. These are fits to the selected data, not manufacturer predictions. Source-window details and caveats remain in the [data note](../../data/module_04/README.md).
