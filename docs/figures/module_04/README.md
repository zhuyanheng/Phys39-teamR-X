# Module 4 A2 figures

No Part 3 figures exist yet. After supervised measurements and a completed [`steady_state.csv`](../../../data/module_04/README.md), run:

```text
python3 Module_4/python/plot_a2.py data/module_04/steady_state.csv --criterion "<copy the actual recorded steady-state rule>"
```

The script creates `heating_trace.svg`, `cooling_trace.svg`, and `steady_temperature_vs_pwm.svg` in this folder. Inspect all three against the raw files and working note before including them in A2. Time traces should show the chosen nonzero-PWM command interval and shade the marked steady window. The response graph uses red HEAT and blue COOL, labeled axes/units, and a place for the actual steady-state criterion in its caption/report text. These are not pre-existing measurements.
