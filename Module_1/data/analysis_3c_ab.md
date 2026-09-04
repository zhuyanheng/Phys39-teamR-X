# Part 3C Quantitative Analysis

## Source Files

- [N=1 voltage data](./part_3c_N1_data.csv)
- [N=1000 averaged voltage data](./part_3c_N1000_data.csv)
- [Part 3C Arduino sketch](../arduino/part_03c_averaging_comparison/part_03c_averaging_comparison.ino)

Each CSV contains 100 sequential reported voltage points.

## N=1 Results

The N=1 data contain three discrete voltage values:

| Voltage (V) | ADC code | Frequency |
|---:|---:|---:|
| 2.502444 | 512 | 3 |
| 2.507331 | 513 | 90 |
| 2.512219 | 514 | 7 |

The mean voltage is:

\[
\bar{x}_1
=
\frac{1}{100}\sum_{i=1}^{100}x_i
=
2.50752655\ \mathrm{V}.
\]

Using the sample-standard-deviation definition,

\[
s_1
=
\sqrt{
\frac{
\sum_{i=1}^{100}(x_i-\bar{x}_1)^2
}{
100-1
}
},
\]

the result is:

\[
s_1
=
0.00154093\ \mathrm{V}
=
1.54093\ \mathrm{mV}.
\]

The smallest nonzero voltage jump between two subsequent points is:

\[
\Delta V_1
=
0.004887\ \mathrm{V}
=
4.887\ \mathrm{mV}.
\]

## N=1000 Results

For the N=1000 data:

\[
\bar{x}_{1000}
=
2.50724583\ \mathrm{V},
\]

and:

\[
s_{1000}
=
0.000034438\ \mathrm{V}
=
0.034438\ \mathrm{mV}
=
34.438\ \mu\mathrm{V}.
\]

The smallest nonzero voltage jump between subsequent points occurs between
points 2 and 3:

\[
2.507243\ \mathrm{V}
-
2.507239\ \mathrm{V}
=
0.000004\ \mathrm{V}.
\]

Therefore:

\[
\Delta V_{1000}
=
4\ \mu\mathrm{V}
=
0.004\ \mathrm{mV}.
\]

## Nominal ADC Resolution

The Arduino Uno has a 10-bit ADC and therefore has:

\[
2^{10}=1024
\]

possible output codes.

For a nominal 5.00 V reference, the nominal one-count resolution is:

\[
\Delta V_{\mathrm{ADC}}
=
\frac{5.00\ \mathrm{V}}{1024}
=
0.0048828125\ \mathrm{V}
=
4.883\ \mathrm{mV}.
\]

The voltage-conversion sketch uses:

\[
V=5.00\frac{n}{1023}
\]

so that ADC code 1023 maps to 5.00 V. Consequently, adjacent displayed
voltage values differ by approximately \(5.00/1023=4.8876\) mV. This displayed
mapping interval should be distinguished from the nominal ADC bin width of
\(5.00/1024=4.883\) mV.

## Comparison With the Independent-Noise Prediction

The measured ratio is:

\[
\frac{s_{1000}}{s_1}
=
\frac{0.000034438}{0.00154093}
=
0.02235.
\]

The independent-noise prediction is:

\[
\frac{s_{1000}}{s_1}
\approx
\frac{1}{\sqrt{1000}}
=
0.03162.
\]

The measured precision-improvement factor is:

\[
\frac{s_1}{s_{1000}}
=
44.745.
\]

The corresponding measured effective bit gain is:

\[
b_{\mathrm{measured}}
=
\log_2(44.745)
=
5.484\ \text{bits}.
\]

The theoretical bit gain is:

\[
b_{\mathrm{predicted}}
=
\frac{1}{2}\log_2(1000)
=
4.983\ \text{bits}.
\]

The measured result is reasonably close to the theoretical five-bit estimate,
but it does not exactly follow the ideal prediction. Possible causes include
finite sample size, quantization, correlated electrical noise, slow input
drift, and variation of the Arduino reference voltage.

## Interpretation

Averaging can produce reported values with sub-LSB numerical spacing because
the mean of many integer ADC codes does not have to be an integer. However,
the 4 µV minimum numerical jump should not be interpreted as 4 µV absolute
accuracy. The standard deviation is a more useful empirical measure of
noise-limited precision in this experiment. Averaging reduces random
fluctuations but does not remove systematic calibration errors.