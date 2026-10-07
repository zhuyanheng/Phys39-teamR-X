"""Plot the October 7 P-only high-gain temperature and applied PWM record."""

import csv
import os
import statistics
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "phys39_mpl_cache"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "Module_5/data/20261007_105005_kp250_20to30c_oscillation.csv"
OUTPUT = ROOT / "Module_5/figures/kp250_20to30c_oscillation"


def extrema(active, setpoint):
    peaks, troughs = [], []
    for before, row, after in zip(active, active[1:], active[2:]):
        time, temp = row[0], row[1]
        if time < 90:
            continue  # Exclude the initial overshoot and early settling cycles.
        if before[1] < temp >= after[1] and temp > setpoint + 0.5:
            peaks.append((time, temp))
        if before[1] > temp <= after[1] and temp < setpoint - 0.5:
            troughs.append((time, temp))
    return peaks, troughs


def main():
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if not rows or any(row["safety"] != "OK" for row in rows):
        raise ValueError("The source is empty or reports a safety fault")

    time = [float(row["time_s"]) for row in rows]
    temperature = [float(row["temperature_C"]) for row in rows]
    signed_pwm = [int(row["pwm"]) * (1 if row["heat_cool"] == "1" else -1)
                  for row in rows]
    active = [(float(row["time_s"]), float(row["temperature_C"]))
              for row in rows if row["p_active"] == "1"]
    settings = {(row["setpoint_C"], row["Kp_pwm_per_C"])
                for row in rows if row["p_active"] == "1"}
    if settings != {("30.0", "250.0")}:
        raise ValueError(f"Unexpected active settings: {settings}")

    setpoint = 30.0
    start_time, start_temp = active[0]
    first_peak = max(active, key=lambda item: item[1])
    peaks, troughs = extrema(active, setpoint)
    period = statistics.mean(b[0] - a[0] for a, b in zip(peaks, peaks[1:]))
    peak_to_peak = statistics.mean(temp for _, temp in peaks) - statistics.mean(
        temp for _, temp in troughs
    )

    plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True,
                         "grid.alpha": 0.2})
    fig, (ax_t, ax_pwm) = plt.subplots(2, 1, sharex=True, figsize=(11, 7.2),
                                       gridspec_kw={"height_ratios": [2, 1]},
                                       constrained_layout=True)
    fig.suptitle("P-only control: 20.9 °C to 30 °C, Kp = 250 PWM/°C")
    for ax in (ax_t, ax_pwm):
        ax.axvspan(start_time, time[-1], color="#eef3f9", alpha=0.7)
        ax.axvline(start_time, color="#6b7280", linestyle=":", linewidth=1.5)

    ax_t.plot(time, temperature, color="#245a81", linewidth=2,
              label="Measured block temperature")
    ax_t.axhline(setpoint, color="#b45b22", linestyle="--", linewidth=1.7,
                 label="30 °C setpoint")
    ax_t.scatter([start_time, first_peak[0]], [start_temp, first_peak[1]],
                 color=["#245a81", "#aa3434"], zorder=5)
    ax_t.annotate(f"P control starts: {start_temp:.2f} °C",
                  (start_time, start_temp), xytext=(start_time + 5, start_temp + 2),
                  arrowprops={"arrowstyle": "->", "color": "#65717d"})
    ax_t.annotate(f"First peak: {first_peak[1]:.2f} °C\n"
                  f"Overshoot: {first_peak[1] - setpoint:.2f} °C",
                  first_peak, xytext=(first_peak[0] + 9, first_peak[1] + 0.8),
                  arrowprops={"arrowstyle": "->", "color": "#aa3434"})
    ax_t.text(0.98, 0.06,
              f"Late cycles (t ≥ 90 s): period ≈ {period:.2f} s\n"
              f"Peak-to-peak ≈ {peak_to_peak:.2f} °C",
              transform=ax_t.transAxes, va="bottom", ha="right",
              bbox={"facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.92})
    ax_t.set_ylabel("Temperature (°C)")
    ax_t.set_ylim(19.5, 34.5)
    ax_t.legend(loc="upper left")

    ax_pwm.step(time, signed_pwm, where="post", color="#693f85", linewidth=1.5)
    ax_pwm.axhline(0, color="#555", linewidth=0.8)
    ax_pwm.axhline(255, color="#aa3434", linestyle="--", linewidth=0.8)
    ax_pwm.axhline(-255, color="#aa3434", linestyle="--", linewidth=0.8)
    ax_pwm.set_ylabel("Applied PWM\nHEAT + / COOL −")
    ax_pwm.set_xlabel("Elapsed Arduino time (s)")
    ax_pwm.set_ylim(-285, 285)
    ax_pwm.set_xlim(0, time[-1])
    ax_pwm.text(0.02, 0.93, "Dashed lines: PWM limits ±255", transform=ax_pwm.transAxes,
                va="top", color="#aa3434")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT.with_suffix(".png"), dpi=180)
    plt.close(fig)
    print(OUTPUT.with_suffix(".png"))
    print(f"late period={period:.3f} s; late peak-to-peak={peak_to_peak:.3f} °C")


if __name__ == "__main__":
    main()
