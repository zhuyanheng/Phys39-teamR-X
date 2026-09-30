# A2 — TEC Heating and Cooling Analysis (optional working draft)

Ricky Huang and Xavier Zhu · Phys 39 · Module 4 · **working draft only; measurements require revalidation under the revised Part 3 rule**

The professor's 2026-09-28 revision changed A2 from an instrument/safety note to a **1–2 page analysis PDF due Monday, 2026-10-05 at 6:00 PM**. No repository version or new Git checkpoint is required. This Markdown file is only a private drafting aid; submit `A2_Lastname_Lastname.pdf` to Moodle separately for each teammate. Keep the [ten-run lab record](../module_notes/module_04_open_loop_tec.md), raw data and code for later modules, but **do not repeat C2/C3 circuit sketches, apparatus description, safety demonstration or code documentation in the A2 PDF**.

## 1. Experimental graph and measured slopes

Insert the [Part 4 steady-temperature graph](../../Module_4/figures/steady_temperature_vs_pwm.svg): x = **signed PWM count** (COOL negative, HEAT positive), y = steady temperature (°C), blue COOL and red HEAT data, two fitted lines over clearly identified approximately linear ranges, and the actual steady-state criterion in its caption. Do not fit through visibly curved sections without saying so.

| Quantity | Measured result | Fit range / note |
| --- | --- | --- |
| HEAT slope `m_h` | +0.4954 °C/PWM count | Signed x = 0–45; all five measured HEAT points |
| COOL slope `m_c` | +0.1414 °C/PWM count | Signed x = −96–0; all five measured COOL points |
| Ratio `r=m_h/abs(m_c)` | 3.5035, dimensionless | 0.4954/0.1414 using unrounded fitted slopes |

The plotter prints slopes with respect to **signed x**. Thus the assignment's ratio is `r=m_h/m_c` (both positive); the absolute-value notation above is redundant but numerically equivalent. If instead calculating COOL's slope against its nonnegative magnitude, that number has the opposite sign. State exactly which convention and fit range you used. **These fits are provisional:** the 2026-09-28 revised Part 3 requires approximately `3τ` after a step plus one additional minute of low-drift observation. The present 20-second averaging windows do not establish that rule for every point; see the [audit](../module_notes/module_04_open_loop_tec.md#revised-steady-state-protocol-audit).

H4 and C4 came from maximum-search runs. Their selected windows cross the nominal course measurement boundaries, but the instructor accepted those points on 2026-09-28; the graph marks them with open circles and its caption states the exception. They are included in the displayed fits. H0/C0 are distinct raw baseline runs whose plotted temperatures coincide at signed PWM 0. The two selected 20-second window means are each 23.44 °C.

## 2. PWM averaging and steady-state model

Let `D=|PWM|/255`. During one period `τ`, current is `I` for `Dτ` and zero for `(1−D)τ`. Therefore, starting from the period integrals,

`⟨I⟩ = (1/τ)∫₀^τ I(t)dt = [I(Dτ)+0((1−D)τ)]/τ = DI`,

`⟨I²⟩ = (1/τ)∫₀^τ I²(t)dt = [I²(Dτ)+0((1−D)τ)]/τ = DI²`.

But `⟨I⟩²=D²I²`; their difference is `D(1−D)I²`, positive for `0<D<1`. For fixed on-state current, both the Peltier term (`∝⟨I⟩`) and Joule term (`∝⟨I²⟩`) are linear in duty cycle. Incorrectly using `⟨I⟩²` for Joule heat would make that contribution quadratic in `D`, falsely predicting a duty-dependent susceptibility even in the idealized constant-current model. Our five-point fits are approximately linear (`R²=0.9990` HEAT, `0.9991` COOL); the largest absolute fitted-point residuals are about 0.38 °C and 0.20 °C, respectively. This does not rule out small curvature.

The full object-face TEC heat flow in the [course hardware discussion](https://sethfraden.github.io/Phys39F26-course/hardware/#thermoelectric-cooler) contains Peltier, half the Joule heat, and passive conduction. In the assignment's reduced model, the TEC conduction term and other passive heat leaks are already combined into the effective conductance `G`. **Do not count TEC conduction again** inside the current-dependent `Q̇_TEC`. Start from

`C dT/dt = Q̇_TEC − G(T−T₀)`.

At steady state `dT/dt=0` but the individual heat flows need not be zero. With positive full-on Peltier and object-face Joule heat rates `Q̇_P` and `Q̇_J`, define signed duty `d=u/255` and magnitude `D=|d|`. The revised assignment's combined expression is

`Q̇_TEC = d Q̇_P + |d| Q̇_J`.

It becomes, branch by branch,

`Q̇_TEC,h = d(Q̇_P + Q̇_J)` for `d>0`; `Q̇_TEC,c = d(Q̇_P − Q̇_J)` for `d<0`.

Set `dT/dt=0`, so `G(T−T₀)=Q̇_TEC`. Substitution and division by `G` give

`T_h(d)−T₀ = d(Q̇_P+Q̇_J)/G`, and `T_c(d)−T₀ = d(Q̇_P−Q̇_J)/G`.

Thus `dT_h/dd=(Q̇_P+Q̇_J)/G` and `dT_c/dd=(Q̇_P−Q̇_J)/G`. Because `d=u/255`, the fitted signed-PWM slopes are `m_h=(Q̇_P+Q̇_J)/(255G)` and `m_c=(Q̇_P−Q̇_J)/(255G)` when `Q̇_P>Q̇_J`. Both are positive even though increasing COOL *magnitude* lowers temperature. Their ratio is

`r=m_h/m_c=(Q̇_P+Q̇_J)/(Q̇_P−Q̇_J)`; solving, `Q̇_J/Q̇_P=(r−1)/(r+1)`.

Check: `r=2` gives `1/3`. Using the unrounded fitted slopes gives `r=3.50345048` and **`Q̇_J/Q̇_P=0.5559`**. This is an *inference within the simplified near-room-temperature model*, not a direct calorimetric measurement of either heat rate. Repeating the fit without instructor-approved boundary points H4/C4 gives `r=3.5913` and inferred `Q̇_J/Q̇_P=0.5644`; the small change is a useful fit-range sensitivity check, not a replacement for the stated ten-point graph.

## 3. Manufacturer data — student must locate values first

Open the course-linked [Laird CP14-127-045 data sheet](https://sethfraden.github.io/Phys39F26-course/references/laird-tec-cp14-127-045.pdf) and read the **27 °C hot-side** column. Values, units, meaning, and operating condition for each required quantity:

| Data-sheet quantity | Value + unit | Meaning, condition, citation |
| --- | --- | --- |
| Module resistance `R_M` | 1.50 Ω | Module resistance, 27.0 °C hot-side column |
| Maximum current `I_max` | 8.6 A | `Imax (I @ ΔTmax)`, 27.0 °C hot-side column |
| Maximum cold-side heat pumping `Q_c,max` at `ΔT=0` | 71.3 W | `Qcmax (ΔT = 0)`, 27.0 °C hot-side column (Tark page lists 71.32 W) |
| Maximum temperature difference `ΔT_max` | 70.5 °C | `ΔTmax (Qc = 0)`, 27.0 °C hot-side column |

From the 27 °C column: `Q̇_J,max = ½ I_max² R_M = ½ × 8.6² × 1.50 = 55.47 W`, `Q̇_P,max = Q_c,max + Q̇_J,max = 71.3 + 55.47 = 126.77 W`, and

`r_Laird,max = (Q̇_P,max+Q̇_J,max)/(Q̇_P,max−Q̇_J,max) = 1+I_max² R_M/Q_c,max = 1 + (8.6² × 1.50)/71.3 = 2.556`.

The last equality follows from `Q_c,max=Q̇_P,max−Q̇_J,max`; it is dimensionless and provides an independent arithmetic check. These are manufacturer maximum-current conditions, not automatically the lab apparatus's conditions at full PWM duty: actual current also depends on supply voltage/current limit, H-bridge drop, wiring and TEC resistance. `ΔT_max` describes the maximum no-load temperature separation and is contextual data; it is not substituted into the `ΔT=0` heat-rate equation.

## 4. Interpretation and conclusion

The measured ratio is `r=3.5035` versus the manufacturer maximum-current prediction `r_Laird,max=2.556` (measured ≈1.37× larger). Do not assume agreement: `D=1` means the H-bridge is continuously on, **not** that the TEC current equals `I_max`. The supply voltage/current limit (12 V, 10 A), H-bridge and wiring drops, TEC resistance, PWM versus steady DC, finite hot–cold temperature difference, and temperature-dependent properties can all change the operating point. Because the symmetric model predicts `r→1` as current falls below `I_max`, a measured `r` above `2.56` is not explained by a simple current deficit; it reflects the model's idealizations (equal half-Joule split, a single symmetric `G`) and any unequal passive heat paths. A single linear fit also averages over any small curvature.

When the object is hotter than room temperature, passive heat flows **out of the object**; when colder, passive heat flows **into the object**. In both cases passive conduction opposes the imposed temperature departure and is represented by `−G(T−T₀)`. If `G` is approximately the same on both sides of `T₀`, it reduces both temperature responses similarly; it does not by itself make the HEAT and COOL slope *magnitudes* unequal. The simple model attributes the asymmetry primarily to Joule heat adding to the heating-direction Peltier term while partially canceling cooling-direction Peltier pumping. Real unequal passive paths could modify this interpretation and are not separately measured here.

**Provisional conclusion (revise after the data-sheet comparison; about 115 English words):** Our open-loop measurements show an approximately linear steady-temperature response to PWM in each direction, with a larger heating susceptibility than cooling susceptibility. The fitted slope ratio is 3.50. Under the simplified near-room-temperature energy balance, that ratio corresponds to object-face Joule heating about 0.56 times the full-on Peltier heat rate. This is a model-based inference, not a direct measurement of either heat flow. Peltier transport reverses with current, while Joule heating keeps the same sign, so their effects add during heating and partly offset during cooling. Passive conduction carries heat away from a hot block and toward a cold one, opposing both departures. The measured slope ratio (3.50) exceeds the manufacturer's maximum-current prediction (2.56), reflecting the simplifications of the symmetric model and the apparatus operating away from `I_max`.

## Final PDF check

- [ ] 1–2 pages, legible graph with signed PWM, red/blue points, both fitted lines and ranges.
- [ ] Both measured slopes in °C/PWM count and dimensionless `r`.
- [x] PWM averaging proof, steady-state balance/slope-ratio derivation and numerical measured ratio result in this working draft.
- [x] All four cited Laird values with units and conditions, `Q̇_J,max`, `Q̇_P,max`, predicted `r_Laird,max`.
- [x] Measured/manufacturer comparison, passive-conduction answer, 100–150-word conclusion.
- [ ] No old apparatus/safety/code sections; both teammates separately upload the same `A2_Lastname_Lastname.pdf` by 2026-10-05 6:00 PM.
