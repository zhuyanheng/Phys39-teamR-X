"""Quantify what a drifting record does to the stationary-fin fit.

Usage: .venv/bin/python Module_7/python/analysis/stationary_diagnostics.py \
           Module_7/data/raw/module_07_rod_stationary_40C.csv --ambient 23.95
Writes Module_7/data/processed/<raw stem>_stationary_diagnostics.json.

`stationary_fin_fit.py` owns the pre-registered steady-state criterion and
refuses a record that does not meet it. This script is the honest companion for
such a record: it takes the same trailing window and asks how far the fitted
`m` can still move, term by term, so that a number quoted in a document is
traceable to a committed artefact instead of to a shell session.

Four terms, all in per cent of the base `m`:

* `window_slide`   - fit `m` in trailing windows that end earlier in the same
                    hold; a settled record gives the same `m` everywhere.
* `extrapolation`  - fit each probe's exponential approach to its own
                    asymptote, then fit `m` to that asymptote profile: what the
                    profile would be if the hold had lasted forever.
* `ambient`        - `m(T_inf + delta)` for a few plausible thermometer errors.
* `geometry`       - `m` for a 1 mm error in `L`, in all probe positions, and in
                    the tip probe alone.
* `origin_swap`    - the substitute check of module_07_stationary_fin.md §6:
                    rod2 as the origin, four probes, `L` shortened by the
                    rod1-to-rod2 spacing.

Nothing here replaces the pre-registered criterion and nothing here is written
into the fit JSON: these are systematics of a diagnostic fit.
"""
import argparse
import hashlib
import importlib.util
import math
from pathlib import Path
import sys

MODULE = Path(__file__).resolve().parents[2]
FIT_PATH = Path(__file__).resolve().parent / "stationary_fin_fit.py"
spec = importlib.util.spec_from_file_location("stationary_fin_fit", FIT_PATH)
fit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fit)

WINDOW_S = 600.0
WINDOW_STEP_S = 100.0
TAU_RANGE_S = (60.0, 20000.0)
AMBIENT_DELTAS_C = (0.25, 0.5, 1.0)
GEOMETRY_STEP_M = 0.001
# The exponential approach is fitted from this many seconds after the first row,
# which leaves out the controller's fast rise at the start of the step.
APPROACH_SINCE_S = 600.0


def window_means(rows, keys, low, high):
    """Per-channel mean of the measurement rows with low <= time_s <= high."""
    out = []
    for key in keys:
        values = [float(row[key]) for row in rows
                  if low <= float(row["time_s"]) <= high and row[key]]
        if not values:
            return None
        out.append(sum(values) / len(values))
    return out


def fit_asymptote(pairs):
    """Fit y = level + amplitude * exp(-(t - t0)/tau) by golden search on tau.

    ``pairs`` is [(t, y)]; the linear parameters are solved exactly for each
    trial tau, so the search is one-dimensional and needs no start value.
    """
    pairs = [(t, y) for t, y in pairs if t is not None and y is not None]
    if len(pairs) < 8:
        return None
    t0 = pairs[0][0]
    times = [t - t0 for t, _ in pairs]
    values = [y for _, y in pairs]

    def linear(basis, ys):
        n = len(basis)
        mean_b = sum(basis) / n
        mean_y = sum(ys) / n
        sbb = sum((b - mean_b) ** 2 for b in basis)
        sby = sum((b - mean_b) * (y - mean_y) for b, y in zip(basis, ys))
        slope = sby / sbb if sbb else 0.0
        return mean_y - slope * mean_b, slope

    def ssr(log_tau):
        tau = math.exp(log_tau)
        basis = [math.exp(-t / tau) for t in times]
        level, slope = linear(basis, values)
        return sum((y - level - slope * b) ** 2
                   for b, y in zip(basis, values))

    log_tau = fit.golden_minimum(ssr, math.log(TAU_RANGE_S[0]),
                                 math.log(TAU_RANGE_S[1]))
    tau = math.exp(log_tau)
    basis = [math.exp(-t / tau) for t in times]
    level, slope = linear(basis, values)
    return {"tau_s": tau, "asymptote_C": level, "amplitude_C": abs(slope),
            "rise_left_C": level - values[-1],
            "rms_C": math.sqrt(ssr(log_tau) / len(values)), "rows": len(values)}


def relative(m, base):
    return (m / base - 1.0) * 100.0


def base_fit(rows, keys, xs, length, ambient):
    """The window the fit uses: the whole record after `--since`, or all of it."""
    means = [sum(float(row[key]) for row in rows) / len(rows) for key in keys]
    thetas = [value - ambient for value in means]
    return means, thetas


def window_slide(rows, keys, xs, length, ambient, window, step):
    """m for trailing windows anchored at the record end and walked backwards."""
    start = float(rows[0]["time_s"])
    stop = float(rows[-1]["time_s"])
    out = []
    end = stop
    while end - window >= start - 1e-9:
        means = window_means(rows, keys, end - window, end)
        thetas = [value - ambient for value in means]
        result = fit.fit_finite(xs, thetas, length)
        out.append({"start_s": end - window, "stop_s": end,
                    "m_per_m": result["m_per_m"], "rms_C": result["rms_C"]})
        end -= step
    return list(reversed(out))


def summarise(rows, keys, xs, length, ambient, window=WINDOW_S,
              step=WINDOW_STEP_S, since=None, approach_since=None):
    """Base fit plus every systematic term, all keyed for the JSON."""
    start = float(rows[0]["time_s"])
    stop = float(rows[-1]["time_s"])
    base_low = max(stop - window, start) if since is None else max(since, start)
    means = window_means(rows, keys, base_low, stop)
    thetas = [value - ambient for value in means]
    base = fit.fit_finite(xs, thetas, length)
    m0 = base["m_per_m"]

    slide = window_slide(rows, keys, xs, length, ambient, window, step)

    ambient_rows = []
    for delta in AMBIENT_DELTAS_C:
        for sign in (+1, -1):
            shifted = [value - ambient - sign * delta for value in means]
            if min(shifted) <= 0.0:
                continue
            result = fit.fit_finite(xs, shifted, length)
            ambient_rows.append({"delta_C": sign * delta,
                                 "m_per_m": result["m_per_m"],
                                 "change_percent": relative(result["m_per_m"], m0)})

    geometry_rows = []
    cases = [("L {:+.0f} mm".format(sign * GEOMETRY_STEP_M * 1e3),
              list(xs), length + sign * GEOMETRY_STEP_M)
             for sign in (+1, -1)]
    cases += [("all x {:+.0f} mm".format(sign * GEOMETRY_STEP_M * 1e3),
               [xs[0]] + [x + sign * GEOMETRY_STEP_M for x in xs[1:]], length)
              for sign in (+1, -1)]
    cases += [("tip probe x {:+.0f} mm".format(sign * GEOMETRY_STEP_M * 1e3),
               list(xs[:-1]) + [xs[-1] + sign * GEOMETRY_STEP_M], length)
              for sign in (+1, -1)]
    for label, case_xs, case_length in cases:
        try:
            result = fit.fit_finite(case_xs, thetas, case_length)
        except (ValueError, ZeroDivisionError):
            continue
        geometry_rows.append({"case": label, "m_per_m": result["m_per_m"],
                              "change_percent": relative(result["m_per_m"], m0)})

    swapped = {"positions_m": [0.0] + [x - xs[1] for x in xs[2:]],
               "length_m": length - xs[1], "probes": list(keys[1:])}
    swap = fit.fit_finite(swapped["positions_m"], thetas[1:],
                          swapped["length_m"])
    swapped.update({"m_per_m": swap["m_per_m"], "rms_C": swap["rms_C"],
                    "change_percent": relative(swap["m_per_m"], m0)})

    asymptotes, per_probe = [], []
    approach_low = start + APPROACH_SINCE_S if approach_since is None else approach_since
    if sum(1 for row in rows
           if float(row["time_s"]) >= approach_low and row[keys[0]]) < 8:
        approach_low = base_low
    for key in keys:
        pairs = [(float(row["time_s"]), float(row[key])) for row in rows
                 if float(row["time_s"]) >= approach_low and row[key]]
        result = fit_asymptote(pairs)
        if result is None:
            asymptotes = []
            break
        asymptotes.append(result["asymptote_C"])
        per_probe.append({"channel": key, **result})
    extrapolation = None
    if asymptotes:
        result = fit.fit_finite(xs, [value - ambient for value in asymptotes],
                                length)
        extrapolation = {"m_per_m": result["m_per_m"], "rms_C": result["rms_C"],
                         "change_percent": relative(result["m_per_m"], m0),
                         "approach_since_s": approach_low,
                         "profile_C": asymptotes, "probes": per_probe}

    return {
        "window": {"start_s": base_low, "stop_s": stop,
                   "rows": len(rows), "window_s": window},
        "ambient_C": ambient,
        "positions_m": list(xs),
        "analysis_length_m": length,
        "base": {"m_per_m": m0, "rms_C": base["rms_C"],
                 "one_over_m_m": 1.0 / m0 if m0 else math.nan,
                 "theta0_C": thetas[0], "theta_tip_C": thetas[-1]},
        "window_slide": slide,
        "extrapolation": extrapolation,
        "ambient": ambient_rows,
        "geometry": geometry_rows,
        "origin_swap": swapped,
    }


def worst(rows, key="change_percent"):
    """Largest |change| in one systematic section, as a signed number."""
    values = [row[key] for row in rows or [] if row.get(key) is not None]
    if not values:
        return None
    return max(values, key=abs)


def report(result):
    """A short table: the base fit, then one line per systematic term."""
    base = result["base"]
    print(f"window {result['window']['start_s']:.1f}-"
          f"{result['window']['stop_s']:.1f} s, T_inf = {result['ambient_C']:.2f} C")
    print(f"base: m = {base['m_per_m']:.3f} 1/m, 1/m = {base['one_over_m_m'] * 100:.2f} cm, "
          f"rms = {base['rms_C']:.3f} C")
    print()
    print("600 s windows sliding to the end of the record:")
    for row in result["window_slide"]:
        print(f"  {row['start_s']:7.0f}-{row['stop_s']:7.0f} s  "
              f"m = {row['m_per_m']:6.3f} 1/m  "
              f"({relative(row['m_per_m'], base['m_per_m']):+5.1f} %)  "
              f"rms = {row['rms_C']:.3f} C")
    extrapolation = result["extrapolation"]
    if extrapolation:
        print()
        print("per-probe exponential approach, fitted to the same start time:")
        for row in extrapolation["probes"]:
            print(f"  {row['channel']:7s} tau = {row['tau_s']:6.0f} s  "
                  f"asymptote = {row['asymptote_C']:6.2f} C  "
                  f"rise left = {row['rise_left_C']:5.2f} C")
        print(f"  -> m from the asymptote profile = "
              f"{extrapolation['m_per_m']:.3f} 1/m "
              f"({extrapolation['change_percent']:+.1f} % vs the window fit)")
    print()
    print("ambient term (a thermometer error of this size):")
    for row in result["ambient"]:
        print(f"  dT_inf = {row['delta_C']:+5.2f} C  m = {row['m_per_m']:6.3f} 1/m  "
              f"({row['change_percent']:+5.1f} %)")
    print()
    print("geometry term (a 1 mm error):")
    for row in result["geometry"]:
        print(f"  {row['case']:<22} m = {row['m_per_m']:6.3f} 1/m  "
              f"({row['change_percent']:+5.1f} %)")
    swap = result["origin_swap"]
    print()
    print(f"origin swap (rod2 as the origin, 4 probes, L = {swap['length_m']:.4f} m): "
          f"m = {swap['m_per_m']:.3f} 1/m ({swap['change_percent']:+.1f} %)")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--ambient", type=float, required=True,
                        help="ambient temperature in C used for every fit here")
    parser.add_argument("--positions", default=",".join(f"{x:g}" for x in fit.POSITIONS_M),
                        help="probe positions from rod1, in metres, comma separated")
    parser.add_argument("--length", type=float, default=fit.ANALYSIS_LENGTH_M,
                        help="analysis length L from the base to the tip, in metres")
    parser.add_argument("--window", type=float, default=WINDOW_S,
                        help="length of the trailing window in Arduino seconds")
    parser.add_argument("--since", type=float, default=None,
                        help="start of the fitted window in Arduino seconds; "
                             "default is the last --window seconds of the record")
    parser.add_argument("--approach-since", type=float, default=None,
                        help="first row used for the exponential approach, in "
                             "Arduino seconds; default is the 600 s mark")
    parser.add_argument("--step", type=float, default=WINDOW_STEP_S,
                        help="spacing of the sliding windows in Arduino seconds")
    parser.add_argument("--out-dir", type=Path, default=MODULE / "data/processed")
    args = parser.parse_args(argv)

    xs = fit.parse_positions(args.positions)
    if len(xs) != len(fit.ROD_CHANNELS):
        print(f"--positions needs {len(fit.ROD_CHANNELS)} values", file=sys.stderr)
        return 4
    if xs[0] != 0.0 or any(x >= args.length for x in xs):
        print("positions must start at 0 and stay inside --length", file=sys.stderr)
        return 4

    before = hashlib.sha256(args.raw.read_bytes()).hexdigest()
    rows = fit.measurement_rows(fit.read_rows(args.raw))
    if len(rows) < 2:
        print(f"{args.raw.name}: fewer than two measurement rows", file=sys.stderr)
        return 3
    if float(rows[-1]["time_s"]) - float(rows[0]["time_s"]) < args.window:
        print(f"{args.raw.name}: record shorter than the {args.window:g} s window",
              file=sys.stderr)
        return 2

    result = summarise(rows, list(fit.ROD_CHANNELS), xs, args.length,
                       args.ambient, window=args.window, step=args.step,
                       since=args.since, approach_since=args.approach_since)
    result.update({"source": fit.portable_path(args.raw), "source_sha256": before,
                   "raw_unchanged": hashlib.sha256(args.raw.read_bytes()).hexdigest() == before})
    result["worst_change_percent"] = {
        key: worst(result[key]) for key in ("ambient", "geometry")}
    result["worst_change_percent"]["window_slide"] = worst(
        [{"change_percent": relative(row["m_per_m"], result["base"]["m_per_m"])}
         for row in result["window_slide"]])

    path = Path(args.out_dir) / f"{args.raw.stem}_stationary_diagnostics.json"
    fit.write_json(path, result)
    report(result)
    print()
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
