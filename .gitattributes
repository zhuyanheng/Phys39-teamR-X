# Module 1 - Measurement Data Summary

## Part 3A: Minimum, Maximum, and Midpoint ADC Values

| Item | Value | Corresponding Voltage (V) | Note |
| :--- | :--- | :--- | :--- |
| **Minimum** \(n_{min}\) | 512 | 2.502444 | Lowest value observed in N=1 data |
| **Maximum** \(n_{max}\) | 514 | 2.512219 | Highest value observed in N=1 data |
| **Midpoint** \(n_{mid}\) | **513** | 2.507331 | \((512 + 514) / 2 = 513\) |

**Calculation**:
\[
n_{mid} = \frac{n_{min} + n_{max}}{2} = \frac{512 + 514}{2} = 513
\]

**Voltage conversion** (using \( V = ADC \times \frac{5.0}{1023} \)):
- 512 × (5.0/1023) = 2.502444 V
- 513 × (5.0/1023) = 2.507331 V
- 514 × (5.0/1023) = 2.512219 V

---

## Part 3B: ADC Voltage Resolution

| Item | Value |
| :--- | :--- |
| **ADC Resolution** | 10-bit |
| **Number of levels** | \(2^{10} = 1024\) |
| **Reference voltage** | 5.00 V |
| **One-count step** \(\Delta V_{ADC}\) | \(5.00 / 1023 = 4.8876 \, \text{mV}\) |

**Note**: Printing many decimal places (e.g., `2.507331`) does **not** improve the physical resolution of the ADC. The ADC itself can only resolve voltage changes of about 4.89 mV. The extra decimal digits are an artifact of floating-point arithmetic, not an indication of higher physical precision.

---

## Part 3C(a): Mean, Sample Standard Deviation, and Noise Improvement

### N=1 Data Statistics (100 points)

| Discrete Value | Frequency |
| :--- | :--- |
| 2.502444 V (ADC=512) | 3 times |
| **2.507331 V (ADC=513)** | **90 times** |
| 2.512219 V (ADC=514) | 7 times |

**Calculations**:

\[
\bar{x}_1 = \frac{3(2.502444) + 90(2.507331) + 7(2.512219)}{100}
= 2.507527 \, \text{V}
\]

\[
s_1 = \sqrt{\frac{3(2.502444-2.507527)^2 + 90(2.507331-2.507527)^2 + 7(2.512219-2.507527)^2}{99}}
= 0.001591 \, \text{V} = 1.591 \, \text{mV}
\]

---

### N=1000 Data Statistics (100 points)

Based on your data (range: 2.507151 ~ 2.507341 V):

\[
\bar{x}_{1000} = 2.507246 \, \text{V}
\]

\[
s_{1000} = 0.0000344 \, \text{V} = 34.4 \, \mu\text{V}
\]

---

### Comparison Table

| Quantity | N=1 (Single) | N=1000 (Averaged) | Theoretical Prediction |
| :--- | :--- | :--- | :--- |
| **Mean (V)** | 2.507527 | 2.507246 | — |
| **Sample Std Dev (V)** | **0.001591** | **0.0000344** | — |
| **Std Dev Ratio** \(s_{1000}/s_1\) | — | **0.0216** | \(1/\sqrt{1000} = 0.0316\) |
| **Noise Improvement Factor** | — | \(0.001591 / 0.0000344 = \mathbf{46.2\times}\) | \(\sqrt{1000} = 31.6\times\) |
| **Effective Bit Gain** | — | \(\log_2(46.2) = \mathbf{5.5 \, \text{bits}}\) | 5 bits |

**Conclusion**: The measured noise suppression (46.2×) is better than the theoretical prediction (31.6×). This is likely because the N=1 data only toggles between three adjacent ADC codes (512, 513, 514), giving a limited effective noise range. This makes \(s_1\) smaller than expected, causing the computed improvement factor to appear larger.

---

## Part 3C(b): Minimum Discrete Voltage Jump

| Item | N=1 | N=1000 |
| :--- | :--- | :--- |
| **Smallest Adjacent Jump (V)** | **0.004887** | **0.000004** |
| **Ratio to** \(\Delta V_{ADC}\) | ≈ 1 LSB | ≈ 1/1222 LSB |
| **Apparent Bit Gain** | — | \(\log_2(1222) \approx 10.3 \, \text{bits}\) |

**N=1 jump source**:
- \(2.507331 - 2.502444 = 0.004887\) V
- \(2.512219 - 2.507331 = 0.004888\) V
- Average ≈ **0.004887 V** = 1 LSB

**N=1000 jump source**:
- Smallest sorted difference: \(2.507194 - 2.507190 = 0.000004\) V = **4 μV**

**Important Discussion**:
- The apparent bit gain based on **minimum numerical jump** (~10 bits) is a mathematical artifact of floating-point arithmetic, not true physical resolution.
- The true **noise-limited effective resolution** is measured by the standard deviation, giving a gain of ~5.5 bits.
- Averaging creates sub-LSB numerical steps, but precision is still limited by residual noise.

---

## Part 3C: Deviations from Theoretical \(1/\sqrt{N}\) Prediction

Four reasons why the measured improvement may depart from the ideal prediction:

| Factor | Explanation |
| :--- | :--- |
| **Drift** | The potentiometer voltage slowly changes over time; averaging includes low-frequency variations, violating the assumption of purely random noise |
| **Correlated Pickup** | 50/60 Hz mains interference is sinusoidal and correlated, not random; averaging cannot effectively cancel it |
| **Quantization** | ADC values only toggle across 3 codes; quantization error is no longer white noise, so the average deviates from theory |
| **Reference Variation** | The Arduino 5V reference itself fluctuates; averaging cannot eliminate errors in the reference source |

---

## Averaging Table (Completed)

| | N=1 Block | N=1000 Block |
| :--- | :--- | :--- |
| **Mean (V)** | 2.507527 | 2.507246 |
| **Sample Std Dev (V)** | 0.001591 | 0.0000344 |
| **Min Discrete Voltage Jump (V)** | 0.004887 | 0.000004 |
| **Measured** \(s_{1000}/s_1\) | — | 0.0216 |
| **Theoretical** \(1/\sqrt{1000}\) | — | 0.0316 |
| **Noise-Limited Bit Gain** | — | ~5.5 bits |
| **Jump-Based Apparent Bit Gain** | — | ~10.3 bits |

---

## Part 3D: Time Cost of Averaging

*(Run the Part 3D code and fill in the measured values)*

| Item | Value |
| :--- | :--- |
| **Total time for 1000 analogRead()** | ______ μs = ______ ms |
| **Time per single analogRead()** | ______ μs |
| **Conversion rate** | ______ conversions/s |
| **Arduino reference value** | ~100 μs / conversion |

**Expected**: The measured value should be close to 100 μs per conversion, with a total time of about 100,000 μs (0.1 s). If the measured value is significantly larger, this may be due to overhead from `micros()` timing, serial printing, or floating-point calculations.

---

## Part 3C: What the Oscilloscope Revealed that the Serial Displays Did Not

*(2-3 bullet points as required by the checklist)*

1. **Waveform shape**: The oscilloscope shows the actual square-wave PWM waveform, allowing direct visualization of the duty cycle, rise/fall times, and any overshoot/ringing. The serial display only shows numerical values and cannot reveal the waveform shape.

2. **Transient noise**: The oscilloscope captures high-frequency noise spikes, voltage ripple, and switching transients that occur at microsecond timescales. These are completely invisible in the serial monitor/plotter because the ADC samples at ~10 kHz, which averages out or misses such fast events.

3. **Frequency accuracy**: The oscilloscope provides a direct measurement of the actual PWM frequency (e.g., 487 Hz vs. the theoretical 490 Hz), revealing the real-time behavior of the Arduino's internal clock. The serial display cannot independently verify the timing accuracy.

---

## What's Missing from This README?

Based on the A1 Evidence Checklist, here is what you still need to add:

### 🔴 Missing Data

| Item | Status | Action Needed |
| :--- | :--- | :--- |
| **Part 1 - Blink 1:1** (High/Low V, Period, Freq, Duty) | ❌ Missing | Measure with oscilloscope |
| **Part 1 - Blink 10:1** (High/Low V, Period, Freq, Duty) | ❌ Missing | Measure with oscilloscope |
| **Part 1 - Blink 1:10** (High/Low V, Period, Freq, Duty) | ❌ Missing | Measure with oscilloscope |
| **Part 4 - PWM Setting 1** (High/Low V, Period, Freq, Duty) | ❌ Missing | Measure with oscilloscope at potentiometer position 1 |
| **Part 4 - PWM Setting 2** (High/Low V, Period, Freq, Duty) | ❌ Missing | Measure with oscilloscope at potentiometer position 2 |
| **Part 3D - Time Cost** | ❌ Missing | Run Part 3D code, record the values |
| **Equipment Photo** | ❌ Missing | Take a clear photo of the apparatus (Arduino + breadboard + potentiometer + LED) |
| **PWM Waveform Screenshot** | ❌ Missing | Capture oscilloscope screenshot or draw a clear sketch |

### 🟡 Need to Add to `/figures/`

| Screenshot | Status |
| :--- | :--- |
| Part 3A - Serial Monitor (integer discrete levels) | ❓ Confirm you have this |
| Part 3A - Serial Plotter | ❓ Confirm you have this |
| Part 3C - Plotter with transition (N=1 to N=1000) near center | ✅ You have the data |
| Part 3C - Plotter with ONLY N=1 block (for min jump) | ❌ Missing - run the N1_only code |
| Part 4 - Oscilloscope PWM waveform | ❌ Missing |
| Part 4 - Wiring photo | ❌ Missing |

### 🟢 To Add to `/wiring/`

| Item | Status |
| :--- | :--- |
| Pin table (A0→pot, ~9→LED, etc.) | ❌ Not yet written |
| Wiring diagram/schematic | ❌ Not yet drawn |

### 🟢 To Add to `/module_notes/`

| Item | Status |
| :--- | :--- |
| What you built, measured, changed, and learned | ❌ Not yet written |

---

## Next Steps Checklist

- [ ] Run **Part 3D** code and record time cost → fill in the table
- [ ] Run **Part 3C N1_only** code and capture Serial Plotter screenshot → save to `/figures/`
- [ ] Measure **Blink 3 duty cycles** with oscilloscope → fill in data table
- [ ] Measure **PWM 2 settings** with oscilloscope → fill in data table
- [ ] Take **photo** of the apparatus → save to `/figures/`
- [ ] Capture **PWM waveform** screenshot → save to `/figures/`
- [ ] Write **pin table** → save to `/wiring/pin_table.md`
- [ ] Write **module notes** → save to `/module_notes/module_1_notes.md`
- [ ] Update root **README.md** to link to all sections
- [ ] **Commit + Push** everything to GitHub