# Module 1 Data

This directory contains the Part 3C experimental data and quantitative analysis.

## Files

- [N=1 voltage data](./part_3c_N1_data.csv)
- [N=1000 averaged voltage data](./part_3c_N1000_data.csv)
- [Part 3C quantitative analysis](./analysis_3c_ab.md)
- [Arduino sketch used for the averaging comparison](../arduino/part_03c_averaging_comparison/part_03c_averaging_comparison.ino)

## Data Collection Metadata

| Item | Description |
|---|---|
| Date | September 2, 2026 |
| Experimenters | Ricky Huang and Xavier Zhu |
| Board | Arduino Uno |
| Analog input | A0 |
| ADC reference | 5.00 V nominal |
| Potentiometer | 100 kΩ potentiometer held near the midpoint |
| N=1 block | 100 reported points, one ADC conversion per point |
| N=1000 block | 100 reported points, 1000 ADC conversions averaged per point |
| Data format | CSV |
| Voltage unit | Volts (V) |

## Data Columns

Both CSV files contain the following columns:

| Column | Meaning | Unit |
|---|---|---|
| `Point` | Sequential point number from 1 through 100 | Dimensionless |
| `Voltage_V` | Reported voltage | V |

## N=1 Data

The [N=1 CSV file](./part_3c_N1_data.csv) contains 100 sequential voltage
values, each obtained from one `analogRead()` conversion.

The measured values occupy three discrete levels:

| Voltage (V) | ADC code | Frequency |
|---:|---:|---:|
| 2.502444 | 512 | 3 |
| 2.507331 | 513 | 90 |
| 2.512219 | 514 | 7 |

Calculated results:

- Mean voltage: 2.50752655 V
- Sample standard deviation: 0.00154093 V = 1.54093 mV
- Smallest nonzero jump between subsequent points: 0.004887 V = 4.887 mV

## N=1000 Data

The [N=1000 CSV file](./part_3c_N1000_data.csv) contains 100 sequential
reported voltage values. Each reported point is the average of 1000
`analogRead()` conversions.

Calculated results:

- Mean voltage: 2.50724583 V
- Sample standard deviation: 0.000034438 V = 0.034438 mV = 34.438 µV
- Minimum voltage: 2.507151 V
- Maximum voltage: 2.507341 V
- Smallest nonzero jump between subsequent points: 0.000004 V = 0.004 mV = 4 µV

For example, consecutive points 2 and 3 are:

```text
Point 2: 2.507239 V
Point 3: 2.507243 V