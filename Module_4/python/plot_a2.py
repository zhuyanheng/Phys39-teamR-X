"""Create A2 SVG figures from completed, manually reviewed steady-state data.

This script does not operate the TEC or decide when a run is steady. It validates
the chosen intervals against the raw GUI CSVs and uses only Python stdlib.
"""

import argparse
import csv
import html
import math
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_IDS = {f"{direction}{i}" for direction in "HC" for i in range(5)}
SUMMARY_FIELDS = {
    "run_id", "direction", "pwm", "start_temperature_C",
    "steady_temperature_C", "time_waited_s", "source_csv",
    "steady_start_s", "steady_end_s", "range_exception_approved", "notes",
}
RAW_FIELDS = {
    "time_s", "temperature_C", "pwm", "heat_cool", "safety",
    "heat_pwm_firmware", "cool_pwm_firmware", "limit_C",
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
        for field in ("start_temperature_C", "steady_temperature_C",
                      "steady_start_s", "steady_end_s"):
            row[field] = finite_number(row[field], f"{run_id} {field}")
        flag = row["range_exception_approved"].strip().lower()
        if flag not in ("yes", "no"):
            raise ValueError(f"{run_id}: range_exception_approved must be yes or no")
        row["range_exception_approved"] = flag == "yes"
        if (not 10 <= row["steady_temperature_C"] <= 45
                and not row["range_exception_approved"]):
            raise ValueError(f"{run_id}: steady T is outside 10–45 °C without an approved exception")
        if row["range_exception_approved"] and not row["notes"].strip():
            raise ValueError(f"{run_id}: an approved exception needs an explanatory note")
        wait = row["time_waited_s"].strip()
        if not wait and row["pwm"] != 0:
            raise ValueError(f"{run_id}: nonzero PWM needs a measured wait time")
        row["time_waited_s"] = finite_number(wait, f"{run_id} time_waited_s") if wait else None
        if ((row["time_waited_s"] is not None and row["time_waited_s"] < 0)
                or row["steady_end_s"] <= row["steady_start_s"]):
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
        row["limit_C"] = finite_number(row["limit_C"], f"{path} limit_C")
    return sorted(rows, key=lambda row: row["time_s"])


def validate_windows(summary, raw_cache):
    for row in summary:
        source = row["source_path"]
        if source not in raw_cache:
            raw_cache[source] = read_raw(source)
        raw = raw_cache[source]
        selected_indices = [i for i, sample in enumerate(raw)
                            if row["steady_start_s"] <= sample["time_s"] <= row["steady_end_s"]]
        subset = [raw[i] for i in selected_indices]
        if len(subset) < 2:
            raise ValueError(f"{row['run_id']}: fewer than two raw samples in steady window")
        expected_bit = 1 if row["direction"] == "HEAT" else 0
        for sample in subset:
            if sample["pwm"] != row["pwm"]:
                raise ValueError(f"{row['run_id']}: raw PWM differs in steady window")
            if sample["heat_cool"] != expected_bit:
                raise ValueError(f"{row['run_id']}: raw direction differs in steady window")
            if sample["safety"].strip().upper() != "OK":
                raise ValueError(f"{row['run_id']}: safety is not OK in steady window")
            if (not 10 <= sample["temperature_C"] <= 45
                    and not row["range_exception_approved"]):
                raise ValueError(f"{row['run_id']}: raw T leaves 10–45 °C without an approved exception")
            expected_heat = row["pwm"] if row["direction"] == "HEAT" else 0
            expected_cool = row["pwm"] if row["direction"] == "COOL" else 0
            if (sample["heat_pwm_firmware"], sample["cool_pwm_firmware"]) != (expected_heat, expected_cool):
                raise ValueError(f"{row['run_id']}: firmware output PWM differs from the selected command")
            if sample["limit_C"] != 60:
                raise ValueError(f"{row['run_id']}: recorded shutdown limit is not 60 °C")
        average = sum(s["temperature_C"] for s in subset) / len(subset)
        difference = abs(average - row["steady_temperature_C"])
        if difference > 0.02:
            raise ValueError(f"{row['run_id']}: stated steady T differs from raw-window mean by {difference:.3f} °C")
        if row["time_waited_s"] is not None:
            start = selected_indices[0]
            while (start > 0 and raw[start - 1]["pwm"] == row["pwm"]
                   and raw[start - 1]["heat_cool"] == expected_bit):
                start -= 1
            observed_wait = row["steady_start_s"] - raw[start]["time_s"]
            if abs(observed_wait - row["time_waited_s"]) > 0.05:
                raise ValueError(f"{row['run_id']}: wait time disagrees with the raw PWM segment")


def ticks(low, high, count=5):
    if high == low:
        high = low + 1
    return [low + i * (high - low) / count for i in range(count + 1)]


def svg_chart(path, title, xlabel, ylabel, series, xbounds, ybounds, caption,
              shade=None, fit_lines=None, connect_series=True,
              exception_points=None, dual_zero_baseline=False):
    caption_lines = textwrap.wrap(caption, width=110, break_long_words=False) or [""]
    width, height = 900, 565 + 20 * (len(caption_lines) - 1)
    left, right, top = 95, 45, 65
    plot_w, plot_h = width - left - right, 380
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
    if xlo < 0 < xhi:
        zero_x = xcoord(0)
        parts.append(f'<line x1="{zero_x:.1f}" y1="{top}" x2="{zero_x:.1f}" y2="{top+plot_h}" stroke="#555" stroke-width="1.6"/>')
    parts.append(f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#333"/>')
    for name, color, endpoints in fit_lines or []:
        coordinates = " ".join(f"{xcoord(x):.1f},{ycoord(y):.1f}" for x, y in endpoints)
        parts.append(f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="9 5"/>')
    for name, color, points in series:
        ordered = sorted(points)
        if not ordered:
            continue
        if connect_series:
            coordinates = " ".join(f"{xcoord(x):.1f},{ycoord(y):.1f}" for x, y in ordered)
            parts.append(f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        for x, y in ordered:
            open_marker = (exception_points and (x, y) in exception_points)
            zero_ring = dual_zero_baseline and name == "COOL" and x == 0
            if open_marker or zero_ring:
                fill = "white" if open_marker else "none"
                parts.append(f'<circle cx="{xcoord(x):.1f}" cy="{ycoord(y):.1f}" r="6" fill="{fill}" stroke="{color}" stroke-width="2.5"/>')
            else:
                parts.append(f'<circle cx="{xcoord(x):.1f}" cy="{ycoord(y):.1f}" r="4.5" fill="{color}"/>')
    parts.append(f'<text x="{width/2}" y="{top+plot_h+40}" text-anchor="middle" font-family="Arial" font-size="17">{html.escape(xlabel)}</text>')
    parts.append(f'<text transform="translate(26 {top+plot_h/2}) rotate(-90)" text-anchor="middle" font-family="Arial" font-size="17">{html.escape(ylabel)}</text>')
    legend = "   |   ".join(name for name, _, _ in series)
    if fit_lines:
        legend += "   |   dashed = linear fit"
    parts.append(f'<text x="{width/2}" y="{top+plot_h+68}" text-anchor="middle" font-family="Arial" font-size="14">{html.escape(legend)}</text>')
    for index, line in enumerate(caption_lines):
        parts.append(f'<text x="{width/2}" y="{top+plot_h+95+20*index}" text-anchor="middle" font-family="Arial" font-size="12">{html.escape(line)}</text>')
    parts.append('</svg>')
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def fit_linear(points):
    """Ordinary least squares, returning slope and intercept."""
    if len(points) < 2 or len({x for x, _ in points}) < 2:
        raise ValueError("A fit needs at least two distinct PWM points")
    mean_x = sum(x for x, _ in points) / len(points)
    mean_y = sum(y for _, y in points) / len(points)
    denominator = sum((x - mean_x) ** 2 for x, _ in points)
    slope = sum((x - mean_x) * (y - mean_y) for x, y in points) / denominator
    return slope, mean_y - slope * mean_x


def create_figures(summary, raw_cache, output_dir, criterion, fit_ranges):
    output_dir.mkdir(parents=True, exist_ok=True)
    all_t = [r["steady_temperature_C"] for r in summary]
    ymin, ymax = min(all_t) - 1, max(all_t) + 1
    series = []
    fitted = []
    slopes = {}
    for direction, color in COLORS.items():
        group = [r for r in summary if r["direction"] == direction]
        sign = 1 if direction == "HEAT" else -1
        series.append((direction, color,
                       [(sign * r["pwm"], r["steady_temperature_C"]) for r in group]))
        group.sort(key=lambda r: r["pwm"])
        low, high = fit_ranges[direction]
        if not 0 <= low < high <= 255:
            raise ValueError(f"{direction}: fit range must satisfy 0 <= MIN < MAX <= 255")
        chosen = [(sign * r["pwm"], r["steady_temperature_C"])
                  for r in group if low <= r["pwm"] <= high]
        slope, intercept = fit_linear(chosen)
        mean_temperature = sum(y for _, y in chosen) / len(chosen)
        squared_error = sum((y - (slope * x + intercept)) ** 2 for x, y in chosen)
        squared_total = sum((y - mean_temperature) ** 2 for _, y in chosen)
        r_squared = 1 - squared_error / squared_total if squared_total else 1.0
        slopes[direction] = slope
        xlo, xhi = min(x for x, _ in chosen), max(x for x, _ in chosen)
        fitted.append((f"{direction} fit", color,
                       [(xlo, slope * xlo + intercept), (xhi, slope * xhi + intercept)]))
        print(f"{direction} signed-PWM fitted slope = {slope:.4f} °C/PWM count; "
              f"magnitude range {low}–{high}; R² = {r_squared:.4f}")
        # Prefer a substantial, non-exception transition over the short
        # maximum-search segments that began near their final temperatures.
        selected = max((r for r in group if r["pwm"] > 0 and not r["range_exception_approved"]),
                       key=lambda r: abs(r["steady_temperature_C"] - r["start_temperature_C"]))
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
        svg_chart(output_dir / "heating_trace.svg" if direction == "HEAT" else output_dir / "cooling_trace.svg",
                  f"{direction} time trace, PWM {selected['pwm']}", "Arduino time (s)",
                  "Temperature (°C)", [(direction, color, [(s["time_s"], s["temperature_C"]) for s in trace])],
                  (start_time, end), (min(temperatures)-0.5, max(temperatures)+0.5),
                  f"PWM switch at {raw[start]['time_s']:.2f} s; green band = selected steady interval; {criterion}",
                  shade=(selected["steady_start_s"], selected["steady_end_s"]))
    if slopes["COOL"] == 0:
        raise ValueError("COOL fitted slope is zero; slope ratio is undefined")
    ratio = slopes["HEAT"] / abs(slopes["COOL"])
    print(f"Measured r = m_h / |m_c| = {ratio:.4f}")
    exception_points = {((1 if r["direction"] == "HEAT" else -1) * r["pwm"],
                         r["steady_temperature_C"])
                        for r in summary if r["range_exception_approved"]}
    svg_chart(output_dir / "steady_temperature_vs_pwm.svg",
              "Steady TEC temperature vs signed PWM", "Signed PWM (count; COOL < 0, HEAT > 0)",
              "Steady temperature (°C)", series,
              (-max(r["pwm"] for r in summary if r["direction"] == "COOL"),
               max(r["pwm"] for r in summary if r["direction"] == "HEAT")),
              (ymin, ymax),
              f"Fits: HEAT {fit_ranges['HEAT'][0]}–{fit_ranges['HEAT'][1]}, "
              f"COOL {-fit_ranges['COOL'][1]} to {-fit_ranges['COOL'][0]}; steady: {criterion}. "
              "Open endpoints H4/C4 are instructor-approved 10–45 °C range exceptions; "
              "H0/C0 overlap at 0 PWM.",
              fit_lines=fitted, connect_series=False,
              exception_points=exception_points,
              dual_zero_baseline=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path, help="Completed Module_4/data/steady_state.csv")
    parser.add_argument("--criterion", required=True, help="The actual recorded steady-state rule")
    parser.add_argument("--heat-fit", type=int, nargs=2, metavar=("MIN", "MAX"), required=True,
                        help="HEAT PWM magnitude range used for its linear fit")
    parser.add_argument("--cool-fit", type=int, nargs=2, metavar=("MIN", "MAX"), required=True,
                        help="COOL PWM magnitude range used for its linear fit")
    parser.add_argument("--output-dir", type=Path, default=REPO_ROOT / "Module_4/figures")
    args = parser.parse_args()
    summary_path = args.summary if args.summary.is_absolute() else REPO_ROOT / args.summary
    summary = read_summary(summary_path)
    raw_cache = {}
    validate_windows(summary, raw_cache)
    create_figures(summary, raw_cache, args.output_dir, args.criterion,
                   {"HEAT": args.heat_fit, "COOL": args.cool_fit})
    print(f"Created 3 figures in {args.output_dir}")


if __name__ == "__main__":
    main()
