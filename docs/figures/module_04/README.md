# Module 4 A2 figures

No Part 3 figures exist yet. After supervised measurements and a completed [`steady_state.csv`](../../../data/module_04/README.md), run:

```text
python3 Module_4/python/plot_a2.py data/module_04/steady_state.csv --criterion "<actual steady-state rule>" --heat-fit <heat-min> <heat-max> --cool-fit <cool-min> <cool-max>
```

The script creates `heating_trace.svg`, `cooling_trace.svg`, and `steady_temperature_vs_pwm.svg` in this folder. Inspect all three against the raw files and working note before including the **main graph** in A2. Time traces show a chosen nonzero-PWM command interval and shaded steady window; retain them with the class data, but the revised 1–2 page A2 does not require them in the PDF. The main graph uses **negative signed PWM for COOL**, positive for HEAT, red/blue points, dashed fitted lines over the two explicitly supplied approximately linear magnitude ranges, labeled axes/units, and a place for the actual steady-state criterion. The CLI prints the two signed-x slopes in °C/PWM count and `r=m_h/|m_c|`. These are not pre-existing measurements.
