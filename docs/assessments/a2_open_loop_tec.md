# A2 — TEC Heating and Cooling Analysis (optional working draft)

Ricky Huang and Xavier Zhu · Phys 39 · Module 4 · **not yet ready for submission**

The professor's 2026-09-28 revision changed A2 from an instrument/safety note to a **1–2 page analysis PDF due Monday, 2026-10-05 at 6:00 PM**. No repository version or new Git checkpoint is required. This Markdown file is only a private drafting aid; submit `A2_Lastname_Lastname.pdf` to Moodle separately for each teammate. Keep the [ten-run lab record](../module_notes/module_04_open_loop_tec.md), raw data and code for later modules, but **do not repeat C2/C3 circuit sketches, apparatus description, safety demonstration or code documentation in the A2 PDF**.

## 1. Experimental graph and measured slopes

Insert the [Part 4 steady-temperature graph](../figures/module_04/README.md): x = **signed PWM count** (COOL negative, HEAT positive), y = steady temperature (°C), blue COOL and red HEAT data, two fitted lines over clearly identified approximately linear ranges, and the actual steady-state criterion in its caption. Do not fit through visibly curved sections without saying so.

| Quantity | Measured result | Fit range / note |
| --- | --- | --- |
| HEAT slope `m_h` | TODO °C/PWM count | TODO: signed x range |
| COOL slope `m_c` | TODO °C/PWM count | TODO: signed x range and sign convention |
| Ratio `r=m_h/abs(m_c)` | TODO, dimensionless | TODO: show calculation |

The plotter prints slopes with respect to **signed x**. If instead calculating COOL's slope against its nonnegative magnitude, that number has the opposite sign; its absolute value must be used consistently in `r`. State exactly which convention and fit range you used.

## 2. PWM averaging and steady-state model — show your derivation

Use duty cycle `D=|PWM|/255`, on-state current `I`, PWM period `τ`, current `I` for `Dτ` and zero for the remainder. Starting from the period integrals, show your steps leading to `⟨I⟩=DI` and `⟨I²⟩=DI²`. Explain why `⟨I²⟩` is **not generally** `⟨I⟩²=D²I²` and how that changes the predicted slope/curvature of temperature versus PWM.

The full object-face TEC heat flow in the [course hardware discussion](https://sethfraden.github.io/Phys39F26-course/hardware/#thermoelectric-cooler) contains Peltier, half the Joule heat, and passive conduction. In the assignment's reduced model, the TEC conduction term and other passive heat leaks are already combined into the effective conductance `G`. **Do not count TEC conduction again** inside the current-dependent `Q̇_TEC`. Start from

`C dT/dt = Q̇_TEC − G(T−T₀)`.

At steady state `dT/dt=0` but the individual heat flows need not be zero. With positive full-on Peltier and object-face Joule heat rates `Q̇_P` and `Q̇_J`, use the assignment's signed expressions:

`Q̇_TEC,h = D(Q̇_P + Q̇_J)`; `Q̇_TEC,c = D(−Q̇_P + Q̇_J)`.

**TODO: show the algebra in the PDF** for `T_h(D)−T₀`, `T_c(D)−T₀`, both derivatives with respect to `D`, and the ratio. The target relation to verify is `Q̇_J/Q̇_P = (r−1)/(r+1)`; test your algebra with the course check `r=2 → 1/3`. Convert the measured `r` to a numerical ratio only after the measured slopes are available. If data give an unexpected sign/value, discuss the model assumptions rather than hiding the result.

## 3. Manufacturer data — student must locate values first

Open the course-linked [Laird CP14-127-045 data sheet](https://sethfraden.github.io/Phys39F26-course/references/laird-tec-cp14-127-045.pdf). **Locate and transcribe these numbers yourself before asking AI to check them**. Use the class model and the **27 °C hot-side** column/table. Record units, exact table location, meaning and operating condition for each:

| Data-sheet quantity | Your independently located value + unit | Meaning, condition, citation |
| --- | --- | --- |
| Module resistance `R_M` | TODO | TODO |
| Maximum current `I_max` | TODO | TODO |
| Maximum cold-side heat pumping `Q_c,max` at `ΔT=0` | TODO | TODO |
| Maximum temperature difference `ΔT_max` | TODO | TODO |

At the data-sheet maximum current and `ΔT=0`, calculate `Q̇_J,max = ½ I_max² R_M`, then use `Q_c,max = Q̇_P,max − Q̇_J,max` to find `Q̇_P,max`. Calculate `r_Laird,max = (Q̇_P,max + Q̇_J,max)/(Q̇_P,max − Q̇_J,max)`. Put units on all heat-transfer rates (W). These are **manufacturer maximum-current conditions**, not automatically the lab apparatus's conditions at full PWM duty: actual current also depends on supply voltage/current limit, H-bridge drop, wiring and TEC resistance.

## 4. Interpretation and conclusion

Compare measured `r` with `r_Laird,max` without assuming agreement. Address PWM versus steady DC, finite temperature differences, passive heat paths, changing material properties and fit-range curvature where relevant. Explicitly answer: above room temperature, which way does passive heat flow? Below room temperature, which way? Why can approximately symmetric passive conduction oppose both directions but not by itself explain unequal slope **magnitudes**?

**Conclusion (about 100–150 English words): TODO** — state what your measurements imply about Peltier transport, Joule heating and conduction, while separating observed results from model-based interpretation.

## Final PDF check

- [ ] 1–2 pages, legible graph with signed PWM, red/blue points, both fitted lines and ranges.
- [ ] Both measured slopes in °C/PWM count and dimensionless `r`.
- [ ] PWM averaging proof, steady-state balance/slope-ratio derivation and numerical measured ratio result.
- [ ] All four cited Laird values with units and conditions, `Q̇_J,max`, `Q̇_P,max`, predicted `r_Laird,max`.
- [ ] Measured/manufacturer comparison, passive-conduction answer, 100–150-word conclusion.
- [ ] No old apparatus/safety/code sections; both teammates separately upload the same `A2_Lastname_Lastname.pdf` by 2026-10-05 6:00 PM.
