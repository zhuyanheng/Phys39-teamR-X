# Data - Module 1

This folder contains experimental data collected during Module 1 experiments.

## Repository Structure

- [`README.md`](./README.md) — Data folder overview
- [`analysis_3c_ab.md`](./analysis_3c_ab.md) — Full quantitative analysis (mean, std dev, noise improvement, bit gain)
- [`part_3c_N1_data.csv`](./part_3c_N1_data.csv) — N=1 raw data (100 points, single reading each)
- [`part_3c_N1000_data.csv`](./part_3c_N1000_data.csv) — N=1000 averaged data (100 points, 1000-reading average each)

---

## Data Collection Details

| Item | Description |
| :--- | :--- |
| **Date** | September 2, 2026 |
| **Experimenters** | Ricky and Xavier |
| **Arduino Sketch** | `part_03c_averaging_comparison.ino` |
| **Board** | Arduino Uno |
| **ADC Reference** | 5.00 V (nominal) |
| **Potentiometer** | 100 kΩ, fixed at midpoint setting (n_mid = 513) |
| **Data Format** | CSV (comma-separated values) |

---

## File Descriptions

### [`part_3c_N1_data.csv`](./part_3c_N1_data.csv)

- **Description**: 100 sequential voltage readings, each obtained from a **single** `analogRead()` conversion (N = 1).
- **Purpose**: Represents the **unaveraged** ("rough") data block, used to estimate the noise level and minimum discrete voltage jump of a single ADC reading.
- **Data Summary**:

| Discrete Voltage (V) | Corresponding ADC Code | Frequency |
| :--- | :--- | :--- |
| 2.502444 | 512 | 3 |
| 2.507331 | 513 | 90 |
| 2.512219 | 514 | 7 |

**Columns**:

| Column | Header | Description | Units |
| :--- | :--- | :--- | :--- |
| 1 | `Point` | Point index (1–100) | — |
| 2 | `Voltage_V` | Measured voltage from single ADC reading | Volts (V) |

**Example Row**:
```
Point, Voltage_V
1, 2.507331
2, 2.507331
```

---

### [`part_3c_N1000_data.csv`](./part_3c_N1000_data.csv)

- **Description**: 100 sequential voltage readings, each obtained by **averaging 1000** `analogRead()` conversions (N = 1000).
- **Purpose**: Represents the **averaged** ("smooth") data block, used to quantify the noise reduction achieved by averaging.
- **Data Range**: 2.507151 V to 2.507341 V (100 data points)

**Columns**:

| Column | Header | Description | Units |
| :--- | :--- | :--- | :--- |
| 1 | `Point` | Point index (1–100) | — |
| 2 | `Voltage_V` | Measured voltage from 1000-reading average | Volts (V) |

**Example Row**:
```
Point, Voltage_V
1, 2.507317
2, 2.507239
```

---

### [`analysis_3c_ab.md`](./analysis_3c_ab.md)

- **Description**: Full quantitative analysis for Part 3C(a) and 3C(b), including mean, sample standard deviation, noise improvement ratio, minimum discrete voltage jump, and effective bit gain calculations.

---

## Key Results

| Quantity | N=1 Block | N=1000 Block |
| :--- | :--- | :--- |
| **Mean Voltage (V)** | 2.507527 | 2.507246 |
| **Sample Std Dev (V)** | 0.001591 | 0.0000344 |
| **Min Discrete Voltage Jump (V)** | 0.004887 | 0.000004 |
| **Measured Noise Improvement** | — | 46.2x |
| **Theoretical Improvement** | — | 31.6x (sqrt(1000)) |
| **Effective Bit Gain** | — | ~5.5 bits |

## Notes

- The noise improvement is better than the theoretical sqrt(N) prediction because the N=1 data only toggles between three adjacent ADC codes (512, 513, 514), limiting the effective noise range.
- The minimum discrete voltage jump for N=1000 (4 μV) is much smaller than the ADC's one-count step (ΔV_ADC = 4.8876 mV), demonstrating that averaging creates sub-LSB numerical resolution.
- However, the true **noise-limited resolution** is better represented by the standard deviation, which gives a gain of about 5.5 effective bits.

---

*Last updated: September 4th 2026*