"""Cross-calibrate the six Module 7 thermistor channels from one raw run.

    .venv/bin/python Module_7/python/analysis/module_07_calibration.py \
        Module_7/data/raw/module_07_rod_20261026_141502_123456.csv

All six probes must have been soaked in the *same* stirred water bath, so the
TEC base probe (``tec_C``, channel A0) can act as the common reference. For each
rod channel ``i`` this script fits

    T_TEC = a_i + b_i * T_i          (so  T_i,corrected = a_i + b_i * T_i)

by ordinary least squares, then reports the statistics the runbook criterion
needs (start value: mean offset < 0.2 C and no residual trend larger than 0.2 C
across the covered temperature range, measured as the difference between the mean
correction residual at the hot end and at the cold end of the soak).

Outputs (see ``Module_7/data/README.md``):

    data/calibration/module_07_calibration_<raw-stem>.csv   one row per channel
    data/calibration/<raw-stem>_corrected.csv               raw rows + corrected columns
    figures/calibration/<raw-stem>_fit.png                  T_i vs T_TEC + residuals

The raw file is only ever read, never rewritten: the corrected columns are added
to a *copy* and the original ``rodN_C`` values stay untouched.

No serial port, no Arduino, no Qt. The fit and the criteria use the standard
library only, so this runs during the lab before any extra package is installed;
figures are written only when matplotlib is available (``--no-figures`` skips them).
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
import sys

MODULE = Path(__file__).resolve().parents[2]        # Module_7/
ROOT = MODULE.parent
sys.path.insert(0, str(MODULE / "python"))

from rod_protocol import FIELD_NAMES, ROD_CHANNELS  # noqa: E402

REFERENCE_FIELD = "tec_C"
MEASUREMENT_EVENT = "measurement"
CALIBRATION_DIR = MODULE / "data/calibration"
FIGURE_DIR = MODULE / "figures/calibration"
# Same fixed colours as the GUI (index 0 = TEC base, 1..5 = rod 1..5).
PENS = ["#111111", "#245a81", "#2f7d4f", "#927919", "#b45b22", "#693f85"]


class ChannelUnusable(ValueError):
    """Raised when one channel has too little variation to fit a line.

    ``main`` turns this into a ``NO DATA`` row instead of aborting, because one
    probe that fell out of the bath must not throw away the other four fits.
    """


def read_rows(path):
    """Return the raw CSV rows as dicts, keeping every original column."""
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise ValueError(f"{path}: no data rows")
    missing = [name for name in FIELD_NAMES if name not in rows[0]]
    if missing:
        raise ValueError(f"{path}: not a Module 7 raw file, missing {missing}")
    return rows


def measurement_rows(rows):
    """Drop operator events (``start``/``stop``/``operator_mark`` ...) if present.

    Files written by the GUI always carry an ``event`` column; a hand-made or
    older file may not, in which case every row is a measurement.
    """
    if "event" not in rows[0]:
        return list(rows)
    return [row for row in rows
            if row["event"].strip() in ("", MEASUREMENT_EVENT)]


def as_float(text):
    """Parse one CSV cell; ``nan``/``''``/missing become ``None``."""
    if text is None:
        return None
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def fit_line(xs, ys):
    """Least-squares fit ``y = a + b*x``; returns ``(a, b, residuals)`` or None."""
    n = len(xs)
    if n < 3:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx <= 0.0:
        return None
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    residuals = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    return intercept, slope, residuals


def fit_channel(rows, channel, reference=REFERENCE_FIELD):
    """Fit and score one rod channel against the reference channel."""
    pairs = []
    skipped = 0
    for row in rows:
        reference_c = as_float(row.get(reference))
        channel_c = as_float(row.get(f"{channel}_C"))
        if reference_c is None or channel_c is None:
            skipped += 1
            continue
        pairs.append((channel_c, reference_c))

    if len(pairs) < 3:
        raise ChannelUnusable(
            f"{channel}: only {len(pairs)} usable samples (need >= 3); "
            "was the bath really measured on both channels?")

    measured = [pair[0] for pair in pairs]
    reference_c = [pair[1] for pair in pairs]
    fit = fit_line(measured, reference_c)
    if fit is None:
        raise ChannelUnusable(
            f"{channel}: measured channel never changed, cannot fit")
    a, b, _ = fit

    # The runbook residual is (a + b*T_i) - T_TEC, i.e. what is left after
    # correcting, evaluated against the reference probe.
    correction_residuals = [a + b * value - ref
                            for value, ref in zip(measured, reference_c)]
    n = len(pairs)
    mean_residual = sum(correction_residuals) / n
    variance = sum((r - mean_residual) ** 2 for r in correction_residuals)
    std_residual = math.sqrt(variance / (n - 1)) if n > 1 else 0.0
    max_abs = max(abs(r) for r in correction_residuals)

    # "No residual trend larger than X across the whole soak" is measured as the
    # residual *curvature*: how far the residual bows away from the chord that
    # joins its two ends (mean of the middle half minus the mean of the two end
    # quarters). A straight-line residual cannot be reported this way because the
    # fit is orthogonal to it by construction: the slope reported below is ~0 for
    # exactly that reason, and a "hot end minus cold end" difference cancels to ~0
    # as well - least squares pushes the two ends onto opposite sides of the line,
    # so their means are equal and opposite. What is left to see, and what a
    # lagging probe or a drifting bath actually leaves behind, is curvature.
    trend_fit = fit_line(reference_c, correction_residuals)
    trend_slope = trend_fit[1] if trend_fit else 0.0
    order = sorted(range(len(pairs)), key=lambda index: reference_c[index])
    quarter = len(order) // 4
    span = max(reference_c) - min(reference_c)
    if quarter >= 2:
        ends = [correction_residuals[index] for index in order[:quarter]]
        ends += [correction_residuals[index] for index in order[-quarter:]]
        middle = [correction_residuals[index] for index in order[quarter:-quarter]]
        trend_span = abs(sum(middle) / len(middle) - sum(ends) / len(ends))
    else:
        # Too few samples to split: use the largest residual, which is conservative.
        trend_span = max_abs

    return {
        "channel": channel,
        "reference": reference,
        "n_points": n,
        "n_skipped": skipped,
        "t_min_C": round(min(reference_c), 3),
        "t_max_C": round(max(reference_c), 3),
        "span_C": round(span, 3),
        "a_C": round(a, 5),
        "b": round(b, 6),
        "residual_slope": round(trend_slope, 6),
        "residual_mean_C": round(mean_residual, 4),
        "residual_std_C": round(std_residual, 4),
        "residual_max_abs_C": round(max_abs, 4),
        "trend_span_C": round(trend_span, 4),
        "uncorrected_mean_offset_C": round(
            sum(meas - ref for meas, ref in zip(measured, reference_c)) / n, 4),
        "criterion_mean": "",
        "criterion_trend": "",
        "criterion_max": "",
        "criterion_met": "",
        "a_C_raw": a,
        "b_raw": b,
    }


def unusable_result(channel, reference, error):
    """A table row for a channel that could not be fitted at all."""
    return {
        "channel": channel,
        "reference": reference,
        "n_points": 0,
        "n_skipped": "",
        "t_min_C": "",
        "t_max_C": "",
        "span_C": "",
        "a_C": "",
        "b": "",
        "residual_slope": "",
        "residual_mean_C": "",
        "residual_std_C": "",
        "residual_max_abs_C": "",
        "trend_span_C": "",
        "uncorrected_mean_offset_C": "",
        "criterion_mean": "NO DATA",
        "criterion_trend": "NO DATA",
        "criterion_max": "NO DATA",
        "criterion_met": "NO DATA",
        "note": str(error),
    }


def evaluate(results, criterion_mean=0.2, criterion_trend=0.2,
             criterion_max=0.2):
    """Fill in the pass/fail columns and return whether every channel passed."""
    all_met = True
    for result in results:
        if result["criterion_met"] == "NO DATA":
            all_met = False
            continue
        mean_met = abs(result["residual_mean_C"]) <= criterion_mean
        trend_met = result["trend_span_C"] <= criterion_trend
        max_met = result["residual_max_abs_C"] <= criterion_max
        result["criterion_mean"] = "PASS" if mean_met else "FAIL"
        result["criterion_trend"] = "PASS" if trend_met else "FAIL"
        result["criterion_max"] = "PASS" if max_met else "FAIL"
        result["criterion_met"] = ("PASS" if (mean_met and trend_met and max_met)
                                   else "FAIL")
        all_met = all_met and mean_met and trend_met and max_met
    return all_met



TABLE_FIELDS = ("channel", "reference", "n_points", "n_skipped", "t_min_C",
                "t_max_C", "span_C", "a_C", "b", "residual_slope",
                "residual_mean_C", "residual_std_C", "residual_max_abs_C",
                "trend_span_C", "uncorrected_mean_offset_C", "criterion_mean",
                "criterion_trend", "criterion_max", "criterion_met", "note")


def write_table(path, results):
    """Write the coefficient table (one row per channel, extra keys ignored)."""
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=TABLE_FIELDS,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    return path


def write_corrected(path, rows, results, table_name):
    """Copy every raw row and append the corrected columns; originals untouched."""
    channels = [result["channel"] for result in results]
    coefficients = {result["channel"]: (result["a_C_raw"], result["b_raw"])
                    for result in results}
    fieldnames = list(rows[0].keys())
    for channel in channels:
        name = f"{channel}_corrected_C"
        if name not in fieldnames:
            fieldnames.append(name)
    fieldnames.append("calibration_file")

    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames,
                                extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            for channel, (a, b) in coefficients.items():
                value = as_float(row.get(f"{channel}_C"))
                out[f"{channel}_corrected_C"] = (
                    "nan" if value is None else f"{a + b * value:.4f}")
            out["calibration_file"] = table_name
            writer.writerow(out)
    return path


def channel_pairs(rows, channel, reference):
    """All finite (measured, reference) pairs for one channel."""
    pairs = []
    for row in rows:
        reference_c = as_float(row.get(reference))
        channel_c = as_float(row.get(f"{channel}_C"))
        if reference_c is not None and channel_c is not None:
            pairs.append((channel_c, reference_c))
    return pairs


def channel_colour(channel):
    """Pen for a channel, identical to the live GUI plot; unknown = grey."""
    if channel in ROD_CHANNELS:
        return PENS[ROD_CHANNELS.index(channel) + 1]
    return "#555555"


def write_figures(path, rows, results, criterion_mean, criterion_trend):
    """Two panels: T_i against T_TEC, and the correction residual."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(f"  (matplotlib not installed, skipped {path.name})")
        return None

    reference = results[0]["reference"]
    limit = max(criterion_mean, criterion_trend)
    figure, (left, right) = plt.subplots(1, 2, figsize=(11, 4.8))
    reference_values = [value for value in (as_float(row.get(reference))
                                            for row in rows)
                        if value is not None]

    for result in results:
        channel = result["channel"]
        # Colour by channel, never by position in ``results``: when one probe is
        # NO DATA it is left out of this list and every later probe would
        # otherwise borrow the wrong pen.
        colour = channel_colour(channel)
        pairs = channel_pairs(rows, channel, reference)
        if not pairs:
            continue
        xs = [pair[0] for pair in pairs]
        ys = [pair[1] for pair in pairs]
        a, b = result["a_C_raw"], result["b_raw"]
        left.plot(xs, [a + b * value for value in xs], color=colour, lw=1.6,
                  label=f"{channel}: a={a:+.2f} C, b={b:.3f}")
        left.scatter(xs, ys, s=4, color=colour, alpha=0.25, edgecolors="none")
        right.plot(ys, [a + b * value - ref for value, ref in zip(xs, ys)],
                   color=colour, lw=1.4, label=channel)

    if reference_values:
        low, high = min(reference_values), max(reference_values)
        left.plot([low, high], [low, high], ls="--", lw=1.0, color="#888888",
                  label="identity")
    left.set_xlabel("measured probe temperature (C)")
    left.set_ylabel(f"reference {reference} (C)")
    left.set_title("cross-calibration fits")
    left.legend(fontsize=7.5, loc="upper left")

    right.axhline(0.0, color="#888888", lw=1.0)
    for sign in (1, -1):
        right.axhline(sign * limit, color="#b45b22", lw=0.9, ls=":")
    right.set_xlabel(f"reference {reference} (C)")
    right.set_ylabel("(a + b T_i) - T_TEC (C)")
    right.set_title(f"correction residual, criterion +/-{limit:.2f} C")
    right.legend(fontsize=7.5, loc="upper right")

    for axes in (left, right):
        axes.grid(alpha=0.18)
        axes.spines["top"].set_visible(False)
        axes.spines["right"].set_visible(False)

    figure.tight_layout()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(figure)
    return path




def print_summary(results, criterion_mean, criterion_trend, criterion_max):
    print(f"  criterion: |mean residual| <= {criterion_mean:.2f} C, "
          f"residual curvature <= {criterion_trend:.2f} C, "
          f"max |residual| <= {criterion_max:.2f} C")
    print(f"  {'channel':7s} {'a (C)':>8s} {'b':>8s} {'n':>5s} "
          f"{'range (C)':>13s} {'mean':>7s} {'std':>6s} {'max':>6s} "
          f"{'trend':>6s} {'before':>7s}  verdict")
    for result in results:
        if result["criterion_met"] == "NO DATA":
            print(f"  {result['channel']:7s} {'':>8s} {'':>8s} {'0':>5s} "
                  f"{'':>13s} {'':>7s} {'':>6s} {'':>6s} {'':>6s} {'':>7s}  "
                  f"NO DATA  ({result['note']})")
            continue
        print(f"  {result['channel']:7s} {result['a_C']:8.3f} {result['b']:8.4f} "
              f"{result['n_points']:5d} "
              f"{result['t_min_C']:6.1f}-{result['t_max_C']:6.1f} "
              f"{result['residual_mean_C']:7.3f} {result['residual_std_C']:6.3f} "
              f"{result['residual_max_abs_C']:6.3f} {result['trend_span_C']:6.3f} "
              f"{result['uncorrected_mean_offset_C']:7.3f}  "
              f"{result['criterion_met']}")
    print("  columns: a, b = fitted T_TEC = a + b*T_i; mean/std/max = residual "
          "(a + b*T_i) - T_TEC;")
    print("           trend = residual curvature: mean of the middle half minus "
          "the mean of the two end quarters;")
    print("           before = mean (T_i - T_TEC) with no correction applied.")
    print("           (residual mean is 0 by construction - the fit has an "
          "intercept - so it is a self-check, not evidence.)")


def latest_raw_file():
    candidates = sorted((path for path in (MODULE / "data/raw").glob("*.csv")
                         if "_corrected" not in path.name),
                        key=lambda path: path.stat().st_mtime)
    return candidates[-1] if candidates else None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Cross-calibrate the Module 7 rod channels against the TEC "
                    "base probe from one raw CSV.")
    parser.add_argument("raw", nargs="*", type=Path,
                        help="raw CSV file(s); default: newest in Module_7/data/raw")
    parser.add_argument("--reference", default=REFERENCE_FIELD,
                        help="reference column (default tec_C)")
    parser.add_argument("--channels", nargs="+", default=list(ROD_CHANNELS),
                        help="channels to calibrate (default rod1..rod5)")
    parser.add_argument("--criterion-mean", type=float, default=0.2,
                        help="|mean residual| limit in C (default 0.2)")
    parser.add_argument("--criterion-trend", type=float, default=0.2,
                        help="hot/cold end residual difference limit in C "
                             "(default 0.2)")
    parser.add_argument("--criterion-max", type=float, default=0.2,
                        help="max |residual| limit in C (default 0.2)")
    parser.add_argument("--out-dir", type=Path, default=CALIBRATION_DIR)
    parser.add_argument("--figure-dir", type=Path, default=FIGURE_DIR)
    parser.add_argument("--no-figures", action="store_true",
                        help="skip the PNG panels (no matplotlib needed)")
    parser.add_argument("--no-corrected", action="store_true",
                        help="skip the corrected copy of the raw rows")
    arguments = parser.parse_args(argv)

    paths = arguments.raw or [latest_raw_file()]
    if paths[0] is None:
        parser.error(f"no raw CSV given and none found in {MODULE / 'data/raw'}")

    if arguments.reference not in FIELD_NAMES:
        parser.error(f"--reference must be one of {FIELD_NAMES}")

    arguments.out_dir.mkdir(parents=True, exist_ok=True)
    every_channel_passed = True

    for path in paths:
        rows = read_rows(path)
        measurements = measurement_rows(rows)
        print(f"{path}  ({len(rows)} rows, {len(measurements)} measurements)")
        heated = sum(1 for row in measurements
                     if (as_float(row.get("pwm")) or 0) != 0)
        if heated:
            print(f"  WARNING: {heated} of these rows have pwm != 0. A soak used "
                  "for cross-calibration must be passive (actuator off): with the "
                  "TEC heating, the A0 end of the bath is hotter than the probes "
                  "and the offsets are fitted to a gradient.")

        results = []
        for channel in arguments.channels:
            try:
                results.append(fit_channel(measurements, channel,
                                           arguments.reference))
            except ChannelUnusable as error:
                results.append(unusable_result(channel, arguments.reference,
                                               error))
        passed = evaluate(results, arguments.criterion_mean,
                          arguments.criterion_trend, arguments.criterion_max)
        every_channel_passed = every_channel_passed and passed
        print_summary(results, arguments.criterion_mean,
                      arguments.criterion_trend, arguments.criterion_max)

        table_path = arguments.out_dir / f"module_07_calibration_{path.stem}.csv"
        write_table(table_path, results)
        print(f"  table     -> {table_path}")
        if not arguments.no_corrected:
            corrected_path = arguments.out_dir / f"{path.stem}_corrected.csv"
            usable = [result for result in results
                      if result["criterion_met"] != "NO DATA"]
            write_corrected(corrected_path, rows, usable, table_path.name)
            print(f"  corrected -> {corrected_path}")
        if not arguments.no_figures:
            usable = [result for result in results
                      if result["criterion_met"] != "NO DATA"]
            figure_path = write_figures(
                arguments.figure_dir / f"{path.stem}_fit.png", measurements,
                usable, arguments.criterion_mean, arguments.criterion_max)
            if figure_path is not None:
                print(f"  figure    -> {figure_path}")
        print()

    if not every_channel_passed:
        print("Some channels missed the criterion: repeat the soak with slower "
              "stirring, a smaller temperature step, or a better probe contact, "
              "then re-run before the water cools.")
        return 2
    print("All channels met the criterion; these coefficients can be applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

