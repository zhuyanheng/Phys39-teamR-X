# Part 3C(a) & 3C(b) — Quantitative Analysis

This document contains the full quantitative analysis for Part 3C, including mean, sample standard deviation, noise improvement ratio, minimum discrete voltage jump, and effective bit gain calculations.

---

## Part 3C(a): Mean, Sample Standard Deviation, and Noise Improvement

### 1. N=1 Block (100 points)

The N=1 data contain only three discrete voltage values:

- 2.507331 V appears **90 times**
- 2.502444 V appears **3 times** (points 7, 16, 32)
- 2.512219 V appears **7 times** (points 31, 41, 55, 64, 71, 78, 80)

**Mean** (\(\bar{x}_1\)):

$$
\bar{x}_1 = \frac{90(2.507331) + 3(2.502444) + 7(2.512219)}{100} = 2.5075266 \ \text{V}
$$

**Sample standard deviation** (\(s_1\), using \(n-1 = 99\)):

$$
s_1 = \sqrt{\frac{90(2.507331 - 2.5075266)^2 + 3(2.502444 - 2.5075266)^2 + 7(2.512219 - 2.5075266)^2}{99}}
= 0.001591 \ \text{V} = 1.591 \ \text{mV}
$$

---

### 2. N=1000 Block (100 points)

Based on the data:

$$
\bar{x}_{1000} \approx 2.5072458 \ \text{V}
$$

$$
s_{1000} \approx 0.00003444 \ \text{V} = 34.44 \ \mu\text{V}
$$

---

### 3. Comparison with Theoretical Prediction

**Measured ratio**:

$$
\frac{s_{1000}}{s_1} = \frac{0.00003444}{0.001591} \approx 0.02165
$$

**Theoretical prediction** (independent noise):

$$
\frac{s_{1000}}{s_1} \approx \frac{1}{\sqrt{1000}} \approx 0.03162
$$

**Discussion**:

The measured ratio (0.02165) is smaller than the ideal prediction (0.03162), meaning the noise is suppressed more than expected. Possible reasons:

- **Quantisation noise**: The unaveraged data only toggle between three adjacent ADC codes (512, 513, 514). The effective fluctuation range is limited, so \(s_1\) does not fully represent wide-band analogue white noise, making the improvement appear larger.
- **Finite sample size**: Only 100 points per block are used, so the estimated standard deviations have statistical uncertainty.
- **Very stable input**: The potentiometer was fixed extremely well, introducing little low-frequency drift.

---

## Part 3C(b): Smallest Discrete Voltage Jump

### 1. N=1 Block

The smallest voltage difference between two adjacent values is the gap between discrete levels:

$$
2.507331 - 2.502444 = 0.004887 \ \text{V}
$$

$$
2.512219 - 2.507331 = 0.004888 \ \text{V}
$$

**Comparison with \(\Delta V_{ADC}\)**:

$$
\Delta V_{ADC} = \frac{5.00}{1023} = 0.0048876 \ \text{V}
$$

Thus, for N=1, the minimum jump is **approximately 1 LSB (4.8876 mV)**. The raw ADC resolution is limited to the 10-bit native step; no finer voltage difference can be resolved.

---

### 2. N=1000 Block

After sorting the averaged data, the smallest difference between two consecutive points appears between:

$$
2.507190 \ \text{V} \quad \text{and} \quad 2.507194 \ \text{V}
$$

Giving:

$$
0.000004 \ \text{V} = 4 \ \mu\text{V}
$$

(Other adjacent differences are also of the order of 4–5 \(\mu\)V.)

---

### 3. Discussion — Why is this Not the "5 Bits" Claim?

The theoretical gain of **about 5 effective bits** from averaging 1000 samples comes from the standard-deviation improvement:

$$
\sqrt{1000} \approx 32, \quad \log_2(32) = 5
$$

The smallest voltage jump observed here (4 \(\mu\)V) gives a much larger apparent bit gain:

$$
\frac{\Delta V_{ADC}}{4 \times 10^{-6}} = \frac{0.0048876}{0.000004} \approx 1222, \quad \log_2(1222) \approx 10.3 \ \text{bits}
$$

However, this is **not** the physically meaningful resolution. The true noise-limited resolution is better represented by the standard deviation:

$$
\frac{s_1}{s_{1000}} = \frac{0.001591}{0.00003444} \approx 46.2
$$

$$
\log_2(46.2) \approx 5.5 \ \text{bits}
$$

This agrees well with the theoretical prediction of **5 bits** (since \(1000 \approx 2^{10}\), \(\sqrt{1000} \approx 2^{5}\)).

---

## Summary Table

| Quantity | N=1 (single) | N=1000 (averaged) | Theoretical Prediction |
| :--- | :--- | :--- | :--- |
| **Mean Voltage (V)** | 2.5075266 | 2.5072458 | — |
| **Sample Std Dev (V)** | 0.001591 | 0.00003444 | — |
| **Std Dev Ratio** \(s_{1000}/s_1\) | — | 0.02165 | 0.03162 |
| **Smallest Voltage Jump (V)** | 0.004887 | 0.000004 | — |
| **Jump / \(\Delta V_{ADC}\)** | ≈ 1 | ≈ 1/1222 | — |
| **Effective Bit Gain (jump-based)** | — | ≈ 10.3 bits | — |
| **Effective Bit Gain (noise-based)** | — | ≈ 5.5 bits | ≈ 5 bits |

---

## Conclusion

Averaging creates sub-LSB numerical steps in the displayed voltage, but the actual improvement in **noise-limited precision** is governed by the reduction in standard deviation, which matches the \(\sqrt{N}\) rule. The finer numerical jumps are a by-product of floating-point arithmetic, not a true increase in absolute accuracy.

---

*Calculated from data collected on September 2, 2026*