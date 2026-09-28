"""Create A2 SVG figures from completed, manually reviewed steady-state data.

This script does not operate the TEC or decide when a run is steady. It validates
the chosen intervals against the raw GUI CSVs and uses only Python stdlib.
"""

import argparse
import csv
import html
import math
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_IDS = {f"{direction}{i}" for direction in "HC" for i in range(5)}
SUMMARY_FIELDS = {
    "run_id", "direction", "pwm", "start_temperature_C",
    "steady_temperature_C", "time_waited_s", "source_csv",
    "steady_start_s", "steady_end_s", "notes",
}
RAW_FIELDS = {
    "time_s", "temperature_C", "pwm", "heat_cool", "safety",
    "heat_pwm_firmware", "cool_pwm_firmware", "limit_C", "low_limit_C",
    "operating_high_C",
}
COLORS = {"HEAT": "#c62828", "COOL": "#1565c0"}


def finite_number(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label}: expected a number, got {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label}: must be finite")
    return number


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: missing CSV header")
        return set(reader.fieldnames), list(reader)


def read_summary(path):
    fields, rows = read_csv(path)
    missing = SUMMARY_FIELDS - fields
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    if len(rows) != 10:
        raise ValueError(f"{path}: expected 10 formal rows, found {len(rows)}")
    seen = set()
    for row in rows:
        run_id = row["run_id"].strip().upper()
        if run_id not in REQUIRED_IDS or run_id in seen:
            raise ValueError(f"Unexpected or duplicate run ID: {run_id!r}")
        seen.add(run_id)
        direction = row["direction"].strip().upper()
        if direction != ("HEAT" if run_id[0] == "H" else "COOL"):
            raise ValueError(f"{run_id}: direction disagrees with run ID")
        row["run_id"] = run_id
        row["direction"] = direction
        row["pwm"] = finite_number(row["pwm"], f"{run_id} PWM")
        if not row["pwm"].is_integer() or not 0 <= row["pwm"] <= 255:
            raise ValueError(f"{run_id}: PWM must be an integer from 0 to 255")
        row["pwm"] = int(row["pwm"])
        for field in ("start_temperature_C", "steady_temperature_C", "time_waited_s",
                      "steady_start_s", "steady_end_s"):
            row[field] = finite_number(row[field], f"{run_id} {field}")
        if not 10 <= row["steady_temperature_C"] <= 45:
            raise ValueError(f"{run_id}: steady T is outside 10–45 °C")
        if row["time_waited_s"] < 0 or row["steady_end_s"] <= row["steady_start_s"]:
            raise ValueError(f"{run_id}: invalid wait time or steady window")
        source = Path(row["source_csv"].strip())
        if not source.is_absolute():
            source = REPO_ROOT / source
        if not source.is_file():
            raise ValueError(f"{run_id}: raw CSV not found: {source}")
        row["source_path"] = source
    if seen != REQUIRED_IDS:
        raise ValueError(f"Missing run IDs: {sorted(REQUIRED_IDS - seen)}")
    for direction in COLORS:
        group = sorted((r for r in rows if r["direction"] == direction),
                       key=lambda r: r["pwm"])
        if group[0]["pwm"] != 0 or len({r["pwm"] for r in group}) != 5:
            raise ValueError(f"{direction}: need five distinct levels starting at PWM 0")
    return rows


def read_raw(path):
    fields, rows = read_csv(path)
    missing = RAW_FIELDS - fields
    if missing:
        raise ValueError(f"{path}: missing raw columns {sorted(missing)}")
    for row in rows:
        row["time_s"] = finite_number(row["time_s"], f"{path} time_s")
        row["temperature_C"] = finite_number(row["temperature_C"], f"{path} temperature_C")
        row["pwm"] = int(finite_number(row["pwm"], f"{path} pwm"))
        row["heat_cool"] = int(finite_number(row["heat_cool"], f"{path} heat_cool"))
        for field in ("heat_pwm_firmware", "cool_pwm_firmware"):
            row[field] = int(finite_number(row[field], f"{path} {field}"))
        for field in ("limit_C", "low_limit_C", "operating_high_C"):
            row[field] = finite_number(row[field], f"{path} {field}")
    return sorted(rows, key=lambda row: row["time_s"])


def validate_windows(summary, raw_cache):
    for row in summary:
        source = row["source_path"]
        if source not in raw_cache:
            raw_cache[source] = read_raw(source)
        subset = [sample for sample in raw_cache[source]
                  if row["steady_start_s"] <= sample["time_s"] <= row["steady_end_s"]]
        if len(subset) < 2:
            raise ValueError(f"{row['run_id']}: fewer than two raw samples in steady window")
        expected_bit = 1 if row["direction"] == "HEAT" else 0
        for sample in subset:
            if sample["pwm"] != row["pwm"]:
                raise ValueError(f"{row['run_id']}: raw PWM differs in steady window")
            if row["pwm"] and sample["heat_cool"] != expected_bit:
                raise ValueError(f"{row['run_id']}: raw direction differs in steady window")
            if sample["safety"].strip().upper() != "OK":
                raise ValueError(f"{row['run_id']}: safety is not OK in steady window")
            if not 10 <= sample["temperature_C"] <= 45:
                raise ValueError(f"{row['run_id']}: raw T leaves 10–45 °C in steady window")
            expected_heat = row["pwm"] if row["direction"] == "HEAT" else 0
            expected_cool = row["pwm"] if row["direction"] == "COOL" else 0
            if (sample["heat_pwm_firmware"], sample["cool_pwm_firmware"]) != (expected_heat, expected_cool):
                raise ValueError(f"{row['run_id']}: firmware output PWM differs from the selected command")
            if (sample["limit_C"], sample["low_limit_C"], sample["operating_high_C"]) != (60, 10, 45):
                raise ValueError(f"{row['run_id']}: recorded 60/10/45 °C limits are not the expected settings")
        average = sum(s["temperature_C"] for s in subset) / len(subset)
        difference = abs(average - row["steady_temperature_C"])
        if difference > 0.5:
            print(f"CHECK {row['run_id']}: stated steady T differs from raw-window mean by {difference:.2f} °C")


def ticks(low, high, count=5):
    if high == low:
        high = low + 1
    return [low + i * (high - low) / count for i in range(count + 1)]


def svg_chart(path, title, xlabel, ylabel, series, xbounds, ybounds, caption, shade=None):
    width, height = 900, 570
    left, right, top, bottom = 95, 45, 65, 125
    plot_w, plot_h = width - left - right, height - top - bottom
    xlo, xhi = xbounds
    ylo, yhi = ybounds
    if xlo == xhi:
        xlo, xhi = xlo - 1, xhi + 1
    if ylo == yhi:
        ylo, yhi = ylo - 1, yhi + 1

    def xcoord(x):
        return left + (x - xlo) * plot_w / (xhi - xlo)

    def ycoord(y):
        return top + plot_h - (y - ylo) * plot_h / (yhi - ylo)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="{width/2}" y="33" text-anchor="middle" font-family="Arial" font-size="23">{html.escape(title)}</text>']
    if shade:
        x1 = max(left, xcoord(shade[0]))
        x2 = min(left + plot_w, xcoord(shade[1]))
        parts.append(f'<rect x="{x1:.1f}" y="{top}" width="{max(0,x2-x1):.1f}" height="{plot_h}" fill="#e8f5e9"/>')
    for value in ticks(xlo, xhi):
        x = xcoord(value)
        parts.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+plot_h}" stroke="#eee"/>')
        parts.append(f'<text x="{x:.1f}" y="{top+plot_h+25}" text-anchor="middle" font-family="Arial" font-size="13">{value:.0f}</text>')
    for value in ticks(ylo, yhi):
        y = ycoord(value)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" stroke="#eee"/>')
        parts.append(f'<text x="{left-11}" y="{y+4:.1f}" text-anchor="end" font-family="Arial" font-size="13">{value:.1f}</text>')
    parts.append(f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#333"/>')
    for name, color, points in series:
        ordered = sorted(points)
        if not ordered:
            continue
        coordinates = " ".join(f"{xcoord(x):.1f},{ycoord(y):.1f}" for x, y in ordered)
        parts.append(f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        for x, y in ordered:
            parts.append(f'<circle cx="{xcoord(x):.1f}" cy="{ycoord(y):.1f}" r="4.5" fill="{color}"/>')
    parts.append(f'<text x="{width/2}" y="{height-78}" text-anchor="middle" font-family="Arial" font-size="17">{html.escape(xlabel)}</text>')
    parts.append(f'<text transform="translate(26 {top+plot_h/2}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="17">{html.escape(ylabel)}</text>')
    legend = "   |   ".join(name for name, _, _ in series)
    parts.append(f'<text x="{width/2}" y="{height-50}" text-anchor="middle" font-family="Arial" font-size="14">{html.escape(legend)}</text>')
    parts.append(f'<text x="{width/2}" y="{height-22}" text-anchor="middle" font-family="Arial" font-size="12">{html.escape(caption[:120])}</text>')
    parts.append('</svg>')
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def create_figures(summary, raw_cache, output_dir, criterion):
    output_dir.mkdir(parents=True, exist_ok=True)
    all_t = [r["steady_temperature_C"] for r in summary]
    ymin, ymax = min(all_t) - 1, max(all_t) + 1
    series = []
    for direction, color in COLORS.items():
        group = [r for r in summary if r["direction"] == direction]
        series.append((direction, color,
                       [(r["pwm"], r["steady_temperature_C"]) for r in group]))
        group.sort(key=lambda r: r["pwm"])
        slope = ((group[-1]["steady_temperature_C"] - group[0]["steady_temperature_C"])
                 / (group[-1]["pwm"] - group[0]["pwm"]))
        print(f"{direction} endpoint χ_T = {slope:.4f} °C per PWM count (0 to {group[-1]['pwm']})")
        selected = group[-1]
        raw = raw_cache[selected["source_path"]]
        end = selected["steady_end_s"]
        target_indices = [i for i, s in enumerate(raw)
                          if selected["steady_start_s"] <= s["time_s"] <= end]
        first = target_indices[0]
        start = first
        expected_bit = 1 if direction == "HEAT" else 0
        while start > 0 and raw[start-1]["pwm"] == selected["pwm"] and raw[start-1]["heat_cool"] == expected_bit:
            start -= 1
        start_time = max(raw[0]["time_s"], raw[start]["time_s"] - 5)
        trace = [s for s in raw if start_time <= s["time_s"] <= end]
        if len(trace) < 2:
            raise ValueError(f"{selected['run_id']}: insufficient trace points")
        temperatures = [s["temperature_C"] for s in trace]
        svg_chart(output_dir / f"{direction.lower()}ing_trace.svg" if direction == "HEAT" else output_dir / "cooling_trace.svg",
                  f"{direction} time trace, PWM {selected['pwm']}", "Arduino time (s)",
                  "Temperature (°C)", [(direction, color, [(s["time_s"], s["temperature_C"]) for s in trace])],
                  (start_time, end), (min(temperatures)-0.5, max(temperatures)+0.5),
                  f"Green band = selected steady interval; {criterion}",
                  shade=(selected["steady_start_s"], selected["steady_end_s"]))
    svg_chart(output_dir / "steady_temperature_vs_pwm.svg",
              "Steady TEC temperature vs PWM", "PWM magnitude (count)",
              "Steady temperature (°C)", series,
              (0, max(r["pwm"] for r in summary)), (ymin, ymax),
              f"Steady criterion: {criterion}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path, help="Completed data/module_04/steady_state.csv")
    parser.add_argument("--criterion", required=True, help="The actual recorded steady-state rule")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "docs/figures/module_04")
    args = parser.parse_args()
    summary_path = args.summary if args.summary.is_absolute() else REPO_ROOT / args.summary
    summary = read_summary(summary_path)
    raw_cache = {}
    validate_windows(summary, raw_cache)
    create_figures(summary, raw_cache, args.output_dir, args.criterion)
    print(f"Created 3 figures in {args.output_dir}")


if __name__ == "__main__":
    main()
