"""Inspect one short rod run without changing its raw readings.

Usage: .venv/bin/python Module_7/python/analysis/analyze_pilot_run.py RAW.csv
The slope check uses a least-squares line over the last 60 Arduino seconds;
it is a diagnostic, not certification of a sustained stationary interval.
"""
import argparse
import collections
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import statistics

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/module7-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MODULE = Path(__file__).resolve().parents[2]
KEYS = ["tec_C"] + [f"rod{i}_C" for i in range(1, 6)]
POSITIONS_CM = [0, 3.85, 8.95, 14.05, 19.15]
COLORS = ["#111111", "#245a81", "#2f7d4f", "#927919", "#b45b22", "#693f85"]


def number(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return math.nan


def inspect(raw):
    before = hashlib.sha256(raw.read_bytes()).hexdigest()
    with raw.open(newline="") as stream:
        records = list(csv.DictReader(stream))
    rows = [row for row in records if row["event"] == "measurement"]
    if len(rows) < 2:
        raise ValueError("At least two measurement rows are required")
    times = [number(row["time_s"]) for row in rows]
    if not all(math.isfinite(t) for t in times):
        raise ValueError("Nonfinite Arduino timestamp")
    tail = [row for row in rows if number(row["time_s"]) >= times[-1] - 60]
    result = {
        "source": str(raw.resolve()), "source_sha256": before,
        "measurement_rows": len(rows), "duration_s": times[-1] - times[0],
        "largest_gap_s": max(b - a for a, b in zip(times, times[1:])),
        "nonadvancing_timestamps": sum(b <= a for a, b in zip(times, times[1:])),
        "positions_cm_from_hole2": POSITIONS_CM, "analysis_length_m": 0.2715,
        "events": [{k: row[k] for k in ("host_time", "event", "setpoint_C", "note")}
                   for row in records if row["event"] != "measurement"],
        "status": {k: dict(collections.Counter(row[k] for row in rows))
                   for k in ("safety", "rod_ok", "control_active", "backlog_sample")},
        "channels": {},
    }
    for key in KEYS:
        pairs = [(number(row["time_s"]), number(row[key])) for row in rows]
        valid = [(t, y) for t, y in pairs if math.isfinite(y)]
        recent = [(number(row["time_s"]), number(row[key])) for row in tail
                  if math.isfinite(number(row[key]))]
        slope = None
        if len(recent) >= 2:
            mt = statistics.mean(t for t, _ in recent)
            my = statistics.mean(y for _, y in recent)
            denominator = sum((t - mt) ** 2 for t, _ in recent)
            if denominator:
                slope = 60 * sum((t - mt) * (y - my) for t, y in recent) / denominator
        result["channels"][key] = {
            "valid_rows": len(valid), "invalid_rows": len(rows) - len(valid),
            "first_C": pairs[0][1], "last_C": pairs[-1][1],
            "minimum": min(valid, key=lambda pair: pair[1]) if valid else None,
            "maximum": max(valid, key=lambda pair: pair[1]) if valid else None,
            "last60_slope_C_per_min": slope,
        }

    figure, axes = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True,
                                gridspec_kw={"height_ratios": [1, 1.5]},
                                constrained_layout=True)
    axes[0].plot(times, [number(row["tec_C"]) for row in rows],
                 color=COLORS[0], lw=1.8, label="A0: measured TEC")
    axes[0].step(times, [number(row["setpoint_C"]) for row in rows],
                 where="post", color="#c0392b", ls="--", lw=1.5,
                 label="TEC setpoint (blank before control)")
    changes = []
    previous = None
    for row in rows:
        state = (row["control_active"], row["setpoint_C"])
        if previous is not None and state != previous:
            changes.append(number(row["time_s"]))
        previous = state
    for index, key in enumerate(KEYS[1:], 1):
        axes[1].plot(times, [number(row[key]) for row in rows],
                     color=COLORS[index], lw=1.6,
                     label=f"A{index} / T{index}: x={POSITIONS_CM[index-1]:g} cm")
    for ax in axes:
        for t in changes:
            ax.axvline(t, color="#999999", lw=.8, ls=":")
        ax.set_ylabel("Temperature (°C)")
        ax.grid(alpha=.2)
        ax.legend(loc="upper left", ncols=2, fontsize=9)
    axes[0].set_title("Short pilot: TEC control and measured rod response")
    axes[1].set_xlabel("Arduino time (s)")
    axes[1].set_title("Rod positions: holes 2, 5, 7, 8, 9; origin at hole 2", fontsize=11)
    figure.suptitle(raw.stem, fontsize=10)
    out = MODULE / "data/processed/pilot_checks"
    plots = MODULE / "figures/pilot_checks"
    out.mkdir(parents=True, exist_ok=True)
    plots.mkdir(parents=True, exist_ok=True)
    figure_path = plots / f"{raw.stem}_temperatures.png"
    figure.savefig(figure_path, dpi=160)
    plt.close(figure)
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == before
    result["raw_unchanged"] = True
    summary_path = out / f"{raw.stem}_quality.json"
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(summary_path)
    print(figure_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    inspect(parser.parse_args().raw)
