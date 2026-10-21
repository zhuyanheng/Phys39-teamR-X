# Two-lump simulation screenshots — received 2026-10-19

All six screenshots were visually inspected. They are GUI observations, not
raw numerical exports; exact rise/settling times and peak values cannot be
claimed from them alone. Preserve the images unchanged.

| Figure in ../figures/ | Controller | Kp | Active Ki | Visual result |
|---|---|---:|---:|---|
| gui/two_lump/p_kp_0p25.png | P | 0.25 | 0 | Large droop, slow smooth response |
| gui/two_lump/p_kp_4.png | P | 4 | 0 | Smaller droop, smooth response |
| gui/two_lump/p_kp_100.png | P | 100 | 0 | Clear transient overshoot and decaying ringing |
| gui/two_lump/pi_kp_20_ki_0p1.png | PI | 20 | 0.1 | Slow final error correction |
| gui/two_lump/pi_kp_20_ki_0p2.png | PI | 20 | 0.2 | Intermediate integral correction |
| gui/two_lump/pi_kp_20_ki_0p5.png | PI | 20 | 0.5 | More visible overshoot, especially downward |

Shared visible settings: two_lump, measured inputs, Tamb=23.19°C, T0=23.0°C,
chi_c=0.14142°C/PWM, tau=73.03s, VTEC=10V, RM=1.50ohm, CT/C=0.35,
G=2 W/K, PWM limit=255, dt=0.05s, 600s rolling window, anti-windup on.
chi_h=0.49545°C/PWM in five images, but the Kp=100 image displays 0.495;
this small input difference also changes derived C/H/Pu/r. Record it as a
parameter mismatch, or standardize chi_h and rerun that one figure for exact
shared-parameter comparisons. Simulation speed=50 for P and 10 for PI changes
wall-clock playback, not simulated time. Initial conditioning and step times
differ across images; align steps individually for quantitative comparisons.

The GUI's configured Kp slider range is 0–100 in
python/Lab_6_7_modeling_tec_v3.py. The retained high-gain simulation is therefore
Kp=100, not 250. Module 5's high-gain experiment used Kp=250. Compare the
qualitative presence of overshoot/ringing, but do not interpret differences in
amplitude/period/decay as an equal-gain validation. The model screenshot has
decaying ringing; the old physical record has sustained late oscillations.

For P, the disabled Ki field still displays 0.5, but controller_command sets
the integral state and I output to zero in P mode. The orange line at zero
confirms that the disabled number is not an active PI gain. The displayed
"One-lump PI" damping ratio is not the two-lump P damping ratio and should
not be used to label these P plots.

The PI Ki=0.2 screenshot ends with displayed error +0.25°C; this does not
demonstrate the earlier ±0.2°C for 60s settling criterion. Extend that segment
if claiming a final settled response. A screenshot of a smooth curve does not
establish an exact settling time. The current target line shows the current
20°C setting across the chart, rather than the historical stepped target;
captions should explicitly identify the 20→30→20°C sequence.

Next: use these six screenshots and the retained physical-data analysis in
A3's simulation comparison, retain the above limitations, and complete the
two-lump damping/PI stability calculations and model-limit discussion. The
six-image receipt alone does not complete all Part II theory or the A3 report.
