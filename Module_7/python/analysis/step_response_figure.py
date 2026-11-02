"""Plot the six-channel step response of one rod run (Part 2 deliverable).

Usage: .venv/bin/python Module_7/python/analysis/step_response_figure.py \
           [Module_7/data/raw/module_07_rod_interlock_trip_45C_40C.csv]
Writes Module_7/figures/part_02_step_response.png by default.

The default run is the one the field record calls the step response: the 20 C
hold, the 45 C step that the firmware interlock cuts short, and the 40 C hold
that follows. Commanded regions, the setpoint steps and the safety stop are
read from the CSV's own event rows, so no annotation can drift away from the
data. The script only reads raw/ and writes one figure.
"""
import argparse
import collections
import csv
import os
from datetime import datetime
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/module7-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MODULE = Path(__file__).resolve().parents[2]
DEFAULT_RAW = MODULE / "data/raw/module_07_rod_interlock_trip_45C_40C.csv"
KEYS = ["tec_C"] + [f"rod{i}_C" for i in range(1, 6)]
POSITIONS = ["0 cm", "3.85 cm", "8.95 cm", "14.05 cm", "19.15 cm"]
LABELS = ["A0 TEC"] + [f"A{i} rod{i} ({x})"
                       for i, x in enumerate(POSITIONS, start=1)]
COLORS = ["#111111", "#245a81", "#2f7d4f", "#927919", "#b45b22", "#693f85"]
REGION_COLORS = {"20": "#dfe3e8", "40": "#d6e4f0", "45": "#f2d7d5"}


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def event_seconds(row, origin_wall, origin_time):
    """Arduino-second stamp of an event row, taken from its `host_time`.

    Event rows carry no `time_s` (the GUI leaves the Arduino columns blank), so
    each event is placed on the Arduino time axis from the wall clock, anchored
    on the first measurement row. For the committed runs the two clocks agree to
    better than a second over the whole record.
    """
    try:
        return origin_time + (datetime.fromisoformat(row["host_time"])
                              - origin_wall).total_seconds()
    except (KeyError, ValueError):
        return None


def commanded_regions(records, origin_wall, origin_time):
    """(start_s, stop_s, setpoint_C) for every commanded hold, from the events."""
    def event_time(row):
        return event_seconds(row, origin_wall, origin_time)

    regions, open_region = [], None
    for row in records:
        event = row.get("event")
        setpoint = number(row.get("setpoint_C"))
        if event == "start":
            open_region = (event_time(row), setpoint)
        elif event == "setpoint_step" and open_region:
            regions.append((open_region[0], event_time(row), open_region[1]))
            open_region = (event_time(row), setpoint)
        elif event == "stop" and open_region:
            regions.append((open_region[0], event_time(row), open_region[1]))
            open_region = None
    return [region for region in regions
            if region[0] is not None and region[1] is not None]


def limit_cycle(rows, start_after):
    """Mean, half peak-to-peak and period of the TEC trace after `start_after`.

    The 40 C hold is a PI limit cycle rather than a quiet hold, so the figure
    states its measured amplitude and period instead of letting a reader read
    them off a plot. Period is the mean gap between upward mean crossings.
    """
    tail = []
    for row in rows:
        time_s, tec = number(row.get("time_s")), number(row.get("tec_C"))
        if time_s is None or tec is None or time_s < start_after:
            continue
        tail.append((time_s, tec))
    if len(tail) < 20:
        return None
    values = [y for _, y in tail]
    mean = sum(values) / len(values)
    crossings = [tail[i][0] for i in range(1, len(tail))
                 if tail[i - 1][1] - mean < 0.0 <= tail[i][1] - mean]
    if len(crossings) < 3:
        return None
    gaps = [b - a for a, b in zip(crossings, crossings[1:])]
    return {"mean_C": mean, "half_range_C": (max(values) - min(values)) / 2.0,
            "period_s": sum(gaps) / len(gaps), "samples": len(tail)}


def draw(raw, path):
    with Path(raw).open(newline="") as stream:
        records = list(csv.DictReader(stream))
    rows = [row for row in records if row.get("event") == "measurement"]
    if len(rows) < 2:
        raise ValueError(f"{raw}: fewer than two measurement rows")
    times = [number(row["time_s"]) for row in rows]
    origin_wall = datetime.fromisoformat(rows[0]["host_time"])
    origin_time = times[0]

    figure, axes = plt.subplots(figsize=(12.5, 5.8), constrained_layout=True)
    for index, key in enumerate(KEYS):
        axes.plot(times, [number(row[key]) for row in rows], lw=1.6,
                  color=COLORS[index], label=LABELS[index])
    lowest = min(min(number(row[key]) for row in rows) for key in KEYS)
    highest = max(max(number(row[key]) for row in rows) for key in KEYS)
    axes.set_ylim(lowest - 1.0, highest + 1.4)
    labelled = False

    for start, stop, setpoint in commanded_regions(records, origin_wall,
                                                   origin_time):
        axes.axvspan(start, stop,
                     color=REGION_COLORS.get(f"{setpoint:g}", "#eeeeee"),
                     alpha=0.55, zorder=0)
        axes.plot([start, stop], [setpoint, setpoint], ls="--", lw=1.2,
                  color="#777777",
                  label="commanded setpoint" if not labelled else None)
        labelled = True
        axes.annotate(f"{setpoint:g} C", xy=((start + stop) / 2.0, 1.0),
                      xycoords=("data", "axes fraction"), xytext=(0, 4),
                      textcoords="offset points", ha="center", va="bottom",
                      fontsize=9, color="#444444", annotation_clip=False)

    for row in records:
        if row.get("event") == "setpoint_step":
            axes.axvline(event_seconds(row, origin_wall, origin_time),
                         color="#c0392b", lw=1.2, ls=":")
        if row.get("event") == "stop" and "Unsafe" in (row.get("note") or ""):
            trip = event_seconds(row, origin_wall, origin_time)
            axes.axvline(trip, color="#c0392b", lw=1.6)
            axes.annotate(f"interlock trip at t = {trip:.0f} s: {row['note']}",
                          xy=(trip, highest + 0.2),
                          xytext=(trip + 55, highest + 0.85), fontsize=9,
                          color="#c0392b", ha="left", va="center",
                          arrowprops={"arrowstyle": "->", "color": "#c0392b"})

    cycle = limit_cycle(rows, start_after=420.0)
    if cycle:
        axes.annotate(f"TEC limit cycle: {cycle['mean_C']:.2f} +- "
                      f"{cycle['half_range_C']:.2f} C, period {cycle['period_s']:.1f} s",
                      xy=(640.0, cycle["mean_C"]), xytext=(455.0, 36.0),
                      fontsize=9, color="#111111", ha="left",
                      arrowprops={"arrowstyle": "->", "color": "#555555"})

    gains = collections.Counter(
        (number(row.get("Kp_pwm_per_C")), number(row.get("Ki_pwm_per_C_s")))
        for row in rows if number(row.get("Kp_pwm_per_C")) is not None)
    gain_text = ("gains logged on PI rows: " + ", ".join(
        f"Kp = {kp:g}/Ki = {ki:g} on {count} rows"
        for (kp, ki), count in sorted(gains.items()))
        if gains else "gains not logged")
    safety = collections.Counter(row.get("safety") or "blank" for row in rows)
    axes.text(0.015, 0.97,
              f"{Path(raw).name}\n"
              f"{rows[0]['host_time'][11:19]}-{rows[-1]['host_time'][11:19]}, "
              f"{len(rows)} measurement rows, {times[-1] - times[0]:.0f} s\n"
              f"{gain_text}\nsafety: "
              + ", ".join(f"{key} {value}" for key, value in safety.items()),
              transform=axes.transAxes, ha="left", va="top", fontsize=8,
              bbox={"facecolor": "white", "alpha": 0.85,
                    "edgecolor": "#bbbbbb"})

    axes.set_xlabel("Arduino time t (s)")
    axes.set_ylabel("temperature (C)")
    axes.grid(alpha=0.25)
    axes.legend(fontsize=8, ncol=3, loc="lower right", framealpha=0.92)
    figure.suptitle("Rod response to commanded setpoint steps "
                    "(each probe sits at a different distance from the TEC base)",
                    fontsize=11)

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return Path(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", nargs="?", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--out", type=Path,
                        default=MODULE / "figures/part_02_step_response.png")
    args = parser.parse_args(argv)
    print(draw(args.raw, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
