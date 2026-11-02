"""Fit the stationary rod profile of one raw run against both fin models.

Usage: .venv/bin/python Module_7/python/analysis/stationary_fin_fit.py RAW.csv \
           [--positions 0,0.0385,0.0895,0.1405,0.1915] [--length 0.2715] [--ambient 21.4]

What it does, in order:

1. Reads the raw CSV read-only and keeps only ``event=measurement`` rows.
2. Looks for a *trailing* steady interval: a window ending at the last
   measurement in which every temperature channel drifts less than
   --slope-limit (default 0.02 C/min, the course starting criterion) for at
   least --hold seconds (default 600 s) of Arduino time. Without such a window
   there is no stationary profile, so the script refuses instead of fitting a
   drift.
3. Averages the window, subtracts the ambient temperature to get
   theta(x) = T(x) - T_inf, and fits both models with the base temperature
   measured at x = 0 (a Dirichlet boundary condition, not a free amplitude):

       finite, insulated tip :  theta = theta_0 cosh[m(L - x)] / cosh(mL)
       semi-infinite limit   :  theta = theta_0 exp(-m x)

4. Reports m +- sigma (from the curvature of the sum of squares), 1/m, the
   residuals of both models, the analytic finite-length error eps_T(x) at every
   probe, and both Biot numbers. Bi_perp needs the rod diameter: it comes from
   --diameter (default 12.7 mm nominal) and is labelled nominal in the output
   until somebody measures it.

``--ambient`` is the room temperature measured away from the apparatus. If it is
omitted, T_inf is fitted jointly with m and the output records
``ambient_mode: fitted``, so a fitted value cannot be presented as a measured
one.

No per-channel calibration is applied: the six-probe soak was waived, so the rod
readings are used as recorded and the channel-to-channel offset belongs in the
uncertainty budget (see docs/module_notes/module_07_stationary_fin.md).

Exit codes: 0 = fitted, 2 = no steady interval (nothing was written),
3 = unusable input, 4 = inconsistent positions/length.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sys
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2]

# Recorded installation: physical holes 2, 5, 7, 8, 9, origin at hole 2.
# From docs/module_notes/module_07_rod_instrument.md; the measuring uncertainty
# of these distances has not been recorded yet.
POSITIONS_M = (0.0, 0.0385, 0.0895, 0.1405, 0.1915)
ANALYSIS_LENGTH_M = 0.2715
NOMINAL_DIAMETER_M = 0.0127

CHANNELS = ("tec_C",) + tuple(f"rod{i}_C" for i in range(1, 6))
ROD_CHANNELS = CHANNELS[1:]

SLOPE_LIMIT_C_PER_MIN = 0.02
HOLD_S = 600.0
DRIFT_BUDGET_C = 0.10
SENSITIVITY_OFFSET_C = 0.5


def relaxed_criterion(limit, hold, drift_budget):
    """True when the caller did not use the pre-registered steady criterion.

    The three limits in §2 of module_07_stationary_fin.md were fixed before the
    run, so a fit made under other limits has to be recognisable from its own
    output: it is a diagnostic of a drifting record, not the Part 3 result.
    """
    return (limit != SLOPE_LIMIT_C_PER_MIN or hold != HOLD_S
            or drift_budget != DRIFT_BUDGET_C)


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def read_rows(path):
    with Path(path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def measurement_rows(rows):
    return [row for row in rows if row.get("event") == "measurement"]


# ---------------------------------------------------------------- steady state

class PrefixSums:
    """O(1) least-squares slope of one channel over any row interval."""

    def __init__(self, times, values):
        self.n = [0]
        self.st = [0.0]
        self.sy = [0.0]
        self.stt = [0.0]
        self.sty = [0.0]
        for t, y in zip(times, values):
            usable = math.isfinite(t) and math.isfinite(y)
            self.n.append(self.n[-1] + (1 if usable else 0))
            self.st.append(self.st[-1] + (t if usable else 0.0))
            self.sy.append(self.sy[-1] + (y if usable else 0.0))
            self.stt.append(self.stt[-1] + (t * t if usable else 0.0))
            self.sty.append(self.sty[-1] + (t * y if usable else 0.0))

    def slope_c_per_min(self, start, stop):
        """Slope over rows [start, stop]; None if the window holds a gap."""
        count = self.n[stop + 1] - self.n[start]
        if count < 2 or count != stop - start + 1:
            return None
        st = self.st[stop + 1] - self.st[start]
        sy = self.sy[stop + 1] - self.sy[start]
        stt = self.stt[stop + 1] - self.stt[start]
        sty = self.sty[stop + 1] - self.sty[start]
        denominator = count * stt - st * st
        if denominator <= 0.0:
            return None
        return 60.0 * (count * sty - st * sy) / denominator


def _worst_slope(sums, start, stop):
    worst = -1.0
    worst_channel = None
    for channel, table in sums.items():
        slope = table.slope_c_per_min(start, stop)
        if slope is None:
            return math.nan, channel
        if abs(slope) > worst:
            worst = abs(slope)
            worst_channel = channel
    return worst, worst_channel


def _window_mean(table, start, stop):
    """Mean of one channel over inclusive row indices, via prefix sums."""
    count = table.n[stop + 1] - table.n[start]
    if count != stop - start + 1 or count < 1:
        return math.nan
    return (table.sy[stop + 1] - table.sy[start]) / count


def _worst_drift(sums, start, stop, third):
    """Largest first-third minus last-third mean difference, in C."""
    worst, worst_channel = -1.0, None
    for channel, table in sums.items():
        first = _window_mean(table, start, start + third - 1)
        final = _window_mean(table, stop - third + 1, stop)
        if not (math.isfinite(first) and math.isfinite(final)):
            return math.nan, channel
        difference = abs(first - final)
        if difference > worst:
            worst, worst_channel = difference, channel
    return worst, worst_channel


def steady_window(rows, limit=SLOPE_LIMIT_C_PER_MIN, hold=HOLD_S,
                  drift_budget=DRIFT_BUDGET_C, channels=CHANNELS):
    """Longest trailing interval that is flat on both scales we care about.

    Two conditions per channel, because they fail differently:

    * the least-squares slope over the whole window is below `limit`. That is
      the runbook criterion (|dT/dt| < 0.02 C/min sustained for >= hold seconds)
      and it catches slow monotonic decay;
    * the mean of the first third and the mean of the last third of the window
      differ by less than `drift_budget`. A window that opens inside a fast
      transient can still have a small overall slope, because the transient is a
      small part of the window -- yet its mean temperature is biased by exactly
      that transient, which would bias the fitted profile. This second condition
      bounds that bias directly instead of hoping the slope catches it.

    Returns a dict with inclusive row indices ``start``/``stop`` (None when the
    run never settles) plus the diagnostics of the closest attempt and a short
    ``reason``, so the caller can name the channel that was still moving.
    """
    report = {"start": None, "stop": None, "worst_slope_C_per_min": math.nan,
              "slope_channel": None, "worst_drift_C": math.nan,
              "drift_channel": None, "reason": "not evaluated"}
    if len(rows) < 2:
        return {**report, "reason": "fewer than two measurement rows"}
    times = [number(row.get("time_s")) for row in rows]
    if not all(math.isfinite(t) for t in times):
        return {**report, "reason": "nonfinite Arduino timestamp"}
    sums = {channel: PrefixSums(times, [number(row.get(channel)) for row in rows])
            for channel in channels}
    last = len(rows) - 1
    if times[last] - times[0] < hold:
        worst, channel = _worst_slope(sums, 0, last)
        return {**report, "worst_slope_C_per_min": worst, "slope_channel": channel,
                "reason": f"the run is shorter than the {hold:g} s hold"}

    best_score = math.inf
    best = dict(report)
    best["reason"] = "no candidate window"
    # The earliest start that still covers `hold` seconds gives the longest
    # window; the loop returns the first candidate that passes both conditions.
    for start in range(last):
        if times[last] - times[start] < hold:
            break
        slope, channel = _worst_slope(sums, start, last)
        if not math.isfinite(slope):
            if best["reason"] == "no candidate window":
                best.update({"reason": f"{channel} has a gap inside every window",
                             "slope_channel": channel})
            continue
        third = max((last - start + 1) // 3, 1)
        drift, drift_channel = _worst_drift(sums, start, last, third)
        score = slope / limit
        if drift_budget:
            score = max(score, drift / drift_budget)
        if score < best_score:
            best_score = score
            best = {"start": None, "stop": None,
                    "worst_slope_C_per_min": slope, "slope_channel": channel,
                    "worst_drift_C": drift, "drift_channel": drift_channel,
                    "reason": ("the slope is above the criterion" if slope > limit
                               else "the first and last third of the window differ "
                                    "by more than the drift budget")}
        if slope <= limit and (not drift_budget or drift <= drift_budget):
            return {"start": start, "stop": last,
                    "worst_slope_C_per_min": slope, "slope_channel": channel,
                    "worst_drift_C": drift, "drift_channel": drift_channel,
                    "reason": "ok"}
    return best



def window_mean(rows, start, stop, channel):
    """Mean, sample standard deviation and count of one channel in a window."""
    values = [number(row.get(channel)) for row in rows[start:stop + 1]]
    values = [value for value in values if math.isfinite(value)]
    if not values:
        return math.nan, math.nan, 0
    mean = sum(values) / len(values)
    if len(values) < 2:
        return mean, 0.0, len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return mean, math.sqrt(variance), len(values)


# ----------------------------------------------------------------- fin models

def theta_finite(x, m, length):
    """Insulated-tip solution, normalised to 1 at x = 0."""
    return math.cosh(m * (length - x)) / math.cosh(m * length)


def theta_semi_infinite(x, m):
    """Semi-infinite limit of the same problem."""
    return math.exp(-m * x)


def sum_of_squares(m, xs, thetas, length):
    """SSR of the finite model with theta_0 pinned to the x = 0 measurement."""
    theta0 = thetas[0]
    return sum((theta0 * theta_finite(x, m, length) - theta) ** 2
               for x, theta in zip(xs, thetas))


def golden_minimum(function, low, high, iterations=90, tolerance=1e-12):
    """Deterministic 1-D minimiser (this environment has no scipy)."""
    ratio = (math.sqrt(5.0) - 1.0) / 2.0
    a, b = low, high
    c = b - ratio * (b - a)
    d = a + ratio * (b - a)
    fc, fd = function(c), function(d)
    for _ in range(iterations):
        if b - a <= tolerance * (abs(a) + abs(b) + 1e-30):
            break
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - ratio * (b - a)
            fc = function(c)
        else:
            a, c, fc = c, d, fd
            d = a + ratio * (b - a)
            fd = function(d)
    return 0.5 * (a + b)


def fit_finite(xs, thetas, length, lower=0.05, upper=200.0):
    """Fit m along the ray with theta_0 fixed by the measurement at x = 0."""
    best_value, best_m = math.inf, math.nan
    steps = 400
    for index in range(steps + 1):
        m = lower * (upper / lower) ** (index / steps)
        value = sum_of_squares(m, xs, thetas, length)
        if value < best_value:
            best_value, best_m = value, m
    m = golden_minimum(
        lambda candidate: sum_of_squares(candidate, xs, thetas, length),
        best_m * 0.8, best_m * 1.25)
    ssr = sum_of_squares(m, xs, thetas, length)
    return {"m_per_m": m, "ssr_C2": ssr, "rms_C": math.sqrt(ssr / len(xs)),
            "theta0_measured_C": thetas[0]}


def fit_semi_infinite(xs, thetas):
    """Closed form ln(theta/theta_0) = -m x through the origin.

    The fit is unweighted in log space, so its residual scale is not the same
    currency as the finite model's SSR in C; only the residual columns of the
    output table are compared in C.
    """
    numerator = 0.0
    denominator = 0.0
    for x, theta in zip(xs, thetas):
        if x <= 0.0 or theta <= 0.0 or thetas[0] <= 0.0:
            continue
        numerator += x * math.log(theta / thetas[0])
        denominator += x * x
    m = -numerator / denominator if denominator else math.nan
    residuals = [thetas[0] * theta_semi_infinite(x, m) - theta
                 for x, theta in zip(xs, thetas)]
    ssr = sum(residual ** 2 for residual in residuals)
    return {"m_per_m": m, "ssr_C2": ssr, "rms_C": math.sqrt(ssr / len(xs)),
            "method": "log-linear, theta_0 fixed at x = 0"}


def m_uncertainty(m, xs, thetas, length, degrees_of_freedom):
    """Standard error of m from the curvature of SSR at the minimum."""
    if not math.isfinite(m) or degrees_of_freedom <= 0:
        return math.nan
    step = max(abs(m) * 1e-3, 1e-6)
    up = sum_of_squares(m + step, xs, thetas, length)
    here = sum_of_squares(m, xs, thetas, length)
    down = sum_of_squares(m - step, xs, thetas, length)
    curvature = (up - 2.0 * here + down) / (step ** 2)
    if not math.isfinite(curvature) or curvature <= 0.0:
        return math.nan
    return math.sqrt(max(2.0 * here / degrees_of_freedom / curvature, 0.0))


def fit_free_ambient(xs, temperatures, length, lower=0.05, upper=200.0):
    """Fit T_inf and m together, with the amplitude still pinned to x = 0.

    Used only when the ambient temperature was not recorded away from the
    apparatus. It is a two-parameter fit to five points, so it is reported with
    its own degrees of freedom and is never presented as a measured T_inf.

    The two parameters are correlated (raising T_inf shrinks theta_0 and asks for
    a smaller m), so the fit is done as a profile likelihood: m is re-optimised
    for every trial T_inf instead of being relaxed alternately, which can stall
    in the valley between them.
    """
    floor = min(temperatures) - 20.0
    ceiling = min(temperatures) - 0.01

    def cost(ambient, m):
        theta0 = temperatures[0] - ambient
        return sum((ambient + theta0 * theta_finite(x, m, length) - temperature) ** 2
                   for x, temperature in zip(xs, temperatures))

    def best_m(ambient):
        steps = 200
        values = [cost(ambient, lower * (upper / lower) ** (index / steps))
                  for index in range(steps + 1)]
        index = values.index(min(values))
        m = lower * (upper / lower) ** (index / steps)
        m = golden_minimum(lambda candidate: cost(ambient, candidate),
                           max(lower, m * 0.9), min(upper, m * 1.1))
        return cost(ambient, m), m

    steps = 200
    spacing = (ceiling - floor) / steps
    best = (math.inf, math.nan, math.nan)
    for index in range(steps + 1):
        ambient = floor + spacing * index
        value, m = best_m(ambient)
        if value < best[0]:
            best = (value, ambient, m)
    low = max(floor, best[1] - spacing)
    high = min(ceiling, best[1] + spacing)
    ambient = golden_minimum(lambda candidate: best_m(candidate)[0], low, high)
    ssr, m = best_m(ambient)
    return {"ambient_C": ambient, "m_per_m": m, "ssr_C2": ssr,
            "rms_C": math.sqrt(ssr / len(xs)),
            "method": "profile likelihood over T_inf, m re-optimised inside"}



def probe_sensitivity(xs, temperatures, estimator, delta=0.5):
    """How much m moves when a single probe reads `delta` too high.

    The cross-calibration soak was skipped for Module 7, so a per-probe offset of
    the order of the observed spread is possible. One refit per probe turns "we
    did not calibrate" into a number: it shows which probe has to be trusted and
    how much of the quoted m it can move.
    """
    base = estimator(temperatures)
    probes = []
    for index, x in enumerate(xs):
        perturbed = list(temperatures)
        perturbed[index] += delta
        m = estimator(perturbed)
        probes.append({"label": f"rod{index + 1}", "x_m": x, "offset_C": delta,
                       "m_per_m": m, "delta_m_per_m": m - base,
                       "relative_delta_m": (m - base) / base if base else math.nan})
    return {"offset_C": delta, "base_m_per_m": base, "probes": probes}


def epsilon_table(xs, m, length):
    """Analytic finite-length error |Theta_fin - Theta_inf| / |Theta_fin|."""
    table = []
    for x in xs:
        finite = theta_finite(x, m, length)
        semi = theta_semi_infinite(x, m)
        table.append({"x_m": x,
                      "theta_finite_normalised": finite,
                      "theta_semi_normalised": semi,
                      "epsilon_T": abs(finite - semi) / abs(finite) if finite else math.nan})
    return table


def rod_geometry(diameter):
    """Cross-section quantities of a round rod, in SI."""
    radius = diameter / 2.0
    area = math.pi * radius ** 2
    perimeter = math.pi * diameter
    return {"diameter_m": diameter, "radius_m": radius, "area_m2": area,
            "perimeter_m": perimeter, "area_over_perimeter_m": area / perimeter}


def analyse(rows, xs, length, ambient=None, diameter=NOMINAL_DIAMETER_M,
            limit=SLOPE_LIMIT_C_PER_MIN, hold=HOLD_S,
            drift_budget=DRIFT_BUDGET_C, channels=CHANNELS,
            sensitivity_offset=SENSITIVITY_OFFSET_C,
            diameter_is_measured=False):
    """Run the whole chain on already-loaded measurement rows.

    Returns (result, profile). ``result["status"]`` is ``fitted``,
    ``no-steady-interval`` or ``unusable-profile``; ``profile`` is the per-probe
    table written to CSV and is empty unless the fit ran.
    """
    criterion = {"slope_limit_C_per_min": limit, "hold_s": hold,
                 "drift_budget_C": drift_budget, "channels": list(channels),
                 "relaxed": relaxed_criterion(limit, hold, drift_budget)}
    times = [number(row.get("time_s")) for row in rows]
    complete = [index for index, row in enumerate(rows)
                if all(math.isfinite(number(row.get(channel)))
                       for channel in channels)]
    if not complete:
        return {"status": "unusable-profile", "criterion": criterion,
                "reason": "no row has all six channels finite",
                "measurement_rows": len(rows)}, []
    # Analyse only up to the last complete row: a probe unplugged after the soak
    # must not discard the soak, while a gap inside it still forbids every
    # window that contains the gap.
    used = rows[:complete[-1] + 1]
    window = steady_window(used, limit, hold, drift_budget, channels)
    if window["start"] is None:
        duration = (times[complete[-1]] - times[0]
                    if complete[-1] > 0 else math.nan)
        return {"status": "no-steady-interval", "criterion": criterion,
                "window": window, "run_duration_s": duration,
                "measurement_rows": len(rows), "rows_used": len(used)}, []

    start, stop = window["start"], window["stop"]
    means, deviations, counts = {}, {}, {}
    for channel in channels:
        mean, deviation, count = window_mean(used, start, stop, channel)
        means[channel], deviations[channel], counts[channel] = mean, deviation, count
    temperatures = [means[channel] for channel in ROD_CHANNELS]
    if not all(math.isfinite(value) for value in temperatures):
        return {"status": "unusable-profile", "criterion": criterion,
                "reason": "a rod channel has no finite value inside the steady "
                          "window", "measurement_rows": len(rows)}, []


    free_fit = None
    if ambient is None:
        free_fit = fit_free_ambient(xs, temperatures, length)
        ambient_value, ambient_mode = free_fit["ambient_C"], "fitted"
    else:
        ambient_value, ambient_mode = float(ambient), "measured"
    thetas = [temperature - ambient_value for temperature in temperatures]
    if min(thetas) <= 0.0:
        return {"status": "unusable-profile", "criterion": criterion,
                "reason": "a probe reads at or below the ambient temperature, so "
                          "theta is not positive", "measurement_rows": len(rows)}, []

    if free_fit is None:
        finite = fit_finite(xs, thetas, length)
        sigma = m_uncertainty(finite["m_per_m"], xs, thetas, length, len(xs) - 1)
        sigma_note = "from the curvature of SSR, one fitted parameter"
        degrees_of_freedom = len(xs) - 1
    else:
        finite = {"m_per_m": free_fit["m_per_m"], "ssr_C2": free_fit["ssr_C2"],
                  "rms_C": free_fit["rms_C"], "theta0_measured_C": thetas[0]}
        sigma = math.nan
        sigma_note = "not computed: m and T_inf were fitted together"
        degrees_of_freedom = len(xs) - 2
    semi = fit_semi_infinite(xs, thetas)

    if free_fit is None:
        def estimate_m(values):
            return fit_finite(xs, values, length)["m_per_m"]
        sensitivity = probe_sensitivity(xs, thetas, estimate_m, sensitivity_offset)
    else:
        def estimate_m(values):
            return fit_free_ambient(xs, values, length)["m_per_m"]
        sensitivity = probe_sensitivity(xs, temperatures, estimate_m,
                                        sensitivity_offset)

    m = finite["m_per_m"]
    profile = []
    for index, x in enumerate(xs):
        theta = thetas[index]
        model_finite = thetas[0] * theta_finite(x, m, length)
        model_semi = thetas[0] * theta_semi_infinite(x, semi["m_per_m"])
        profile.append({"label": f"rod{index + 1}", "x_m": x,
                        "temperature_C": temperatures[index],
                        "std_C": deviations[ROD_CHANNELS[index]],
                        "samples": counts[ROD_CHANNELS[index]],
                        "theta_C": theta,
                        "theta_finite_model_C": model_finite,
                        "theta_semi_model_C": model_semi,
                        "residual_finite_C": model_finite - theta,
                        "residual_semi_C": model_semi - theta})

    result = {
        "status": "fitted",
        "criterion": criterion,
        "measurement_rows": len(rows),
        "rows_used": len(used),
        "steady_window": {"start_s": times[start], "stop_s": times[stop],
                          "duration_s": times[stop] - times[start],
                          "rows": stop - start + 1,
                          "worst_slope_C_per_min": window["worst_slope_C_per_min"],
                          "slope_channel": window["slope_channel"],
                          "worst_drift_C": window["worst_drift_C"],
                          "drift_channel": window["drift_channel"]},
        "window_means_C": means,
        "window_std_C": deviations,
        "ambient_mode": ambient_mode,
        "ambient_C": ambient_value,
        "positions_m": list(xs),
        "analysis_length_m": length,
        "geometry": rod_geometry(diameter),
        "diameter_is_measured": diameter_is_measured,
        "finite_model": {**finite, "sigma_m_per_m": sigma,
                         "sigma_note": sigma_note,
                         "one_over_m_m": 1.0 / m if m else math.nan,
                         "degrees_of_freedom": degrees_of_freedom},
        "semi_infinite_model": semi,
        "epsilon_table": epsilon_table(xs, m, length),
        "probe_offset_sensitivity": sensitivity,
        "theta_tip_finite": theta_finite(length, m, length),
        "bi_parallel": (m * length) ** 2,
        "bi_perp": (m * diameter / 4.0) ** 2,
        "profiles": profile,
    }
    return result, profile


# -------------------------------------------------------------------- outputs

def json_safe(value):
    """Replace non-finite floats with null so the JSON stays strict."""
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_json(path, result):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(json_safe(result), ensure_ascii=False,
                                     indent=2) + "\n")


def write_profile_csv(path, profile):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    columns = ("label", "x_m", "temperature_C", "std_C", "samples", "theta_C",
               "theta_finite_model_C", "theta_semi_model_C",
               "residual_finite_C", "residual_semi_C")
    with Path(path).open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        for row in profile:
            writer.writerow([row[column] for column in columns])


def print_summary(result):
    window = result["steady_window"]
    criterion = result["criterion"]
    print(f"steady window: {window['start_s']:.1f}-{window['stop_s']:.1f} s "
          f"({window['duration_s'] / 60.0:.1f} min, {window['rows']} rows)")
    print(f"  worst slope {window['worst_slope_C_per_min']:.4f} C/min on "
          f"{window['slope_channel']} (limit {criterion['slope_limit_C_per_min']} C/min)")
    print(f"  worst third-to-third drift {window['worst_drift_C']:.3f} C on "
          f"{window['drift_channel']} (budget {criterion['drift_budget_C']} C)")
    if criterion.get("relaxed"):
        print("  *** CRITERION RELAXED: these limits are not the pre-registered "
              "ones (0.02 C/min, 0.10 C, 600 s),")
        print("  *** so this window is a diagnostic of a drifting record and the "
              "fit below is NOT the Part 3 result")
    print(f"ambient T_inf: {result['ambient_C']:.2f} C ({result['ambient_mode']})")
    print()
    print("  probe     x (m)    T (C)   theta (C)   finite     semi   resid_f   resid_s")
    for row in result["profiles"]:
        print(f"  {row['label']:<6} {row['x_m']:8.4f} {row['temperature_C']:8.2f} "
              f"{row['theta_C']:10.2f} {row['theta_finite_model_C']:8.2f} "
              f"{row['theta_semi_model_C']:8.2f} {row['residual_finite_C']:8.3f} "
              f"{row['residual_semi_C']:8.3f}")
    finite = result["finite_model"]
    semi = result["semi_infinite_model"]
    sigma = finite["sigma_m_per_m"]
    sigma_text = "n/a" if sigma is None or sigma != sigma else f"{sigma:.3f}"
    print()
    print(f"finite (cosh):  m = {finite['m_per_m']:.3f} +- {sigma_text} 1/m  ->  "
          f"1/m = {finite['one_over_m_m'] * 100:.2f} cm, rms = {finite['rms_C']:.3f} C, "
          f"dof = {finite['degrees_of_freedom']}")
    print(f"  sigma: {finite['sigma_note']}")
    print(f"semi-infinite:  m = {semi['m_per_m']:.3f} 1/m   rms = {semi['rms_C']:.3f} C "
          f"({semi['method']})")
    print(f"  |m_finite - m_semi| = {abs(finite['m_per_m'] - semi['m_per_m']):.3f} 1/m")
    print()
    print("  finite-length error eps_T at the recorded probes:")
    for row in result["epsilon_table"]:
        flag = "   > 5 % criterion" if row["epsilon_T"] > 0.05 else ""
        print(f"    x = {row['x_m'] * 100:5.2f} cm   eps_T = "
              f"{row['epsilon_T'] * 100:5.1f} %{flag}")
    print()
    note = "" if result["diameter_is_measured"] else "   (diameter is NOMINAL, not measured)"
    print(f"Theta_tip = {result['theta_tip_finite']:.3f}   mL = "
          f"{math.sqrt(result['bi_parallel']):.3f}   Bi_parallel = "
          f"{result['bi_parallel']:.3f}   Bi_perp = {result['bi_perp']:.2e}{note}")

    sensitivity = result.get("probe_offset_sensitivity")
    if sensitivity and sensitivity["probes"]:
        print()
        print(f"  cost of one probe reading {sensitivity['offset_C']:+.1f} C high "
              f"(no cross-calibration soak):")
        worst = sensitivity["probes"][0]
        for row in sensitivity["probes"]:
            print(f"    {row['label']:<6} m = {row['m_per_m']:6.3f} 1/m   "
                  f"{row['relative_delta_m'] * 100:+6.2f} %")
            if abs(row["relative_delta_m"]) > abs(worst["relative_delta_m"]):
                worst = row
        print(f"  worst case: {worst['label']} moves m by "
              f"{worst['relative_delta_m'] * 100:+.2f} %")


def write_figure(path, result):
    """Deliverable figure: profile with both models, plus both residual sets."""
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/module7-matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 2, figsize=(12.5, 5.2),
                                gridspec_kw={"width_ratios": [1.25, 1]},
                                constrained_layout=True)
    xs = [row["x_m"] for row in result["profiles"]]
    thetas = [row["theta_C"] for row in result["profiles"]]
    errors = [row["std_C"] for row in result["profiles"]]
    theta0 = thetas[0]
    length = result["analysis_length_m"]
    m = result["finite_model"]["m_per_m"]
    semi_m = result["semi_infinite_model"]["m_per_m"]
    relaxed = bool(result["criterion"].get("relaxed"))

    grid = [length * index / 400.0 for index in range(401)]
    axes[0].plot(grid, [theta0 * theta_finite(x, m, length) for x in grid],
                 color="#1f4e79", lw=2.0,
                 label=f"finite, insulated tip: m = {m:.3f} 1/m")
    axes[0].plot(grid, [theta0 * theta_semi_infinite(x, semi_m) for x in grid],
                 color="#c0392b", lw=1.6, ls="--",
                 label=f"semi-infinite: m = {semi_m:.3f} 1/m")
    axes[0].errorbar(xs, thetas, yerr=errors, fmt="o", ms=7, capsize=4,
                     color="#111111",
                     label="window mean" if relaxed else "steady-window mean")
    axes[0].axvline(length, color="#999999", lw=1.0, ls=":")
    axes[0].annotate("tip x = L", (length, max(thetas) * 0.98), ha="right",
                     va="top", fontsize=9, color="#666666")
    axes[0].set_xlabel("x from rod1 / hole 2 (m)")
    axes[0].set_ylabel("theta = T - T_inf (C)")
    axes[0].set_title("Steady profile, both models"
                      if not relaxed else "Trailing-window profile, both models")
    axes[0].grid(alpha=0.25)
    axes[0].legend(fontsize=9)

    axes[1].axhline(0.0, color="#999999", lw=1.0)
    axes[1].plot(xs, [row["residual_finite_C"] for row in result["profiles"]],
                 "o-", ms=7, color="#1f4e79", label="finite residual")
    axes[1].plot(xs, [row["residual_semi_C"] for row in result["profiles"]],
                 "s--", ms=6, mfc="none", color="#c0392b",
                 label="semi-infinite residual")
    axes[1].set_xlabel("x (m)")
    axes[1].set_ylabel("model - measurement (C)")
    axes[1].set_title("Residuals")
    axes[1].grid(alpha=0.25)
    axes[1].legend(fontsize=9)

    window = result["steady_window"]
    criterion = result["criterion"]
    limits = (f"|dT/dt| <= {criterion['slope_limit_C_per_min']:g} C/min, "
              f"drift <= {criterion['drift_budget_C']:g} C, "
              f"window >= {criterion['hold_s']:g} s")
    title = (f"window {window['start_s']:.0f}-{window['stop_s']:.0f} s "
             f"({limits}), T_inf = {result['ambient_C']:.2f} C "
             f"({result['ambient_mode']})")
    if relaxed:
        title = ("CRITERION RELAXED: this record is not a certified steady "
                 "profile\n" + title)
    figure.suptitle(title, fontsize=10)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return Path(path)


# ----------------------------------------------------------------------- main

def parse_positions(text):
    return tuple(float(item) for item in text.split(",") if item.strip())


def portable_path(path):
    """Path relative to the repository when possible, so JSON stays portable."""
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(MODULE.parent))
    except ValueError:
        return resolved.name


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fit the stationary rod profile of one raw run against the "
                    "finite-length and semi-infinite fin models.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--positions", default=",".join(f"{x:g}" for x in POSITIONS_M),
                        help="probe positions from rod1, in metres, comma separated")
    parser.add_argument("--length", type=float, default=ANALYSIS_LENGTH_M,
                        help="analysis length L from the base to the tip, in metres")
    parser.add_argument("--ambient", type=float, default=None,
                        help="measured room temperature in C; omit to fit it")
    parser.add_argument("--diameter", type=float, default=NOMINAL_DIAMETER_M,
                        help="rod diameter in metres, for Bi_perp")
    parser.add_argument("--diameter-is-measured", action="store_true",
                        help="record the diameter as measured rather than nominal")
    parser.add_argument("--slope-limit", type=float, default=SLOPE_LIMIT_C_PER_MIN,
                        help="steady-state criterion in C/min per channel")
    parser.add_argument("--hold", type=float, default=HOLD_S,
                        help="minimum length of the steady window in Arduino seconds")
    parser.add_argument("--drift-budget", type=float, default=DRIFT_BUDGET_C,
                        help="largest allowed difference between the first-third "
                             "and last-third means inside the steady window, in C "
                             "(0 disables the check)")
    parser.add_argument("--sensitivity-offset", type=float, default=SENSITIVITY_OFFSET_C,
                        help="probe error, in C, used for the one-probe-at-a-time "
                             "sensitivity table written to the JSON")
    parser.add_argument("--out-dir", type=Path, default=MODULE / "data/processed")
    parser.add_argument("--figure-dir", type=Path, default=MODULE / "figures")
    parser.add_argument("--figure-name", default="part_03_stationary_profile.png")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args(argv)

    xs = parse_positions(args.positions)
    if len(xs) != len(ROD_CHANNELS):
        print(f"--positions needs {len(ROD_CHANNELS)} values", file=sys.stderr)
        return 4
    if xs[0] != 0.0:
        print("the first position must be 0: rod1 fixes the base boundary",
              file=sys.stderr)
        return 4
    if any(x >= args.length for x in xs):
        print("every position must be smaller than --length", file=sys.stderr)
        return 4

    raw = args.raw
    before = hashlib.sha256(raw.read_bytes()).hexdigest()
    rows = measurement_rows(read_rows(raw))
    if len(rows) < 2:
        print(f"{raw.name}: fewer than two measurement rows", file=sys.stderr)
        return 3

    result, profile = analyse(rows, xs, args.length, ambient=args.ambient,
                              diameter=args.diameter, limit=args.slope_limit,
                              hold=args.hold, drift_budget=args.drift_budget,
                              sensitivity_offset=args.sensitivity_offset,
                              diameter_is_measured=args.diameter_is_measured)
    result.update({"source": portable_path(raw), "source_sha256": before})

    if result["status"] == "no-steady-interval":
        window = result["window"]
        print(f"{raw.name}: no trailing window meets the steady-state criterion",
              file=sys.stderr)
        print(f"  criterion: |dT/dt| <= {args.slope_limit:g} C/min on all six "
              f"channels for at least {args.hold:g} s, and first/last third means "
              f"within {args.drift_budget:g} C", file=sys.stderr)
        print(f"  closest attempt failed because {window['reason']}", file=sys.stderr)
        if window["slope_channel"]:
            print(f"    worst slope {window['worst_slope_C_per_min']:.3f} C/min on "
                  f"{window['slope_channel']}", file=sys.stderr)
        if window["drift_channel"]:
            print(f"    worst third-to-third drift {window['worst_drift_C']:.3f} C on "
                  f"{window['drift_channel']}", file=sys.stderr)
        duration = result.get("run_duration_s")
        if duration is not None and duration == duration and duration < args.hold:
            print(f"  the usable run lasts only {duration:.1f} s, shorter than "
                  f"--hold {args.hold:g} s", file=sys.stderr)
        print("  nothing written: a drifting run is not a stationary profile",
              file=sys.stderr)
        return 2
    if result["status"] != "fitted":
        print(f"{raw.name}: {result.get('reason', 'unusable profile')}",
              file=sys.stderr)
        return 3

    if hashlib.sha256(raw.read_bytes()).hexdigest() != before:
        print(f"{raw.name}: raw file changed while it was being analysed",
              file=sys.stderr)
        return 3
    result["raw_unchanged"] = True

    json_path = args.out_dir / f"{raw.stem}_stationary_fit.json"
    csv_path = args.out_dir / f"{raw.stem}_stationary_profile.csv"
    write_json(json_path, result)
    write_profile_csv(csv_path, profile)
    print_summary(result)
    print()
    print(portable_path(json_path))
    print(portable_path(csv_path))
    if not args.no_figures:
        print(portable_path(write_figure(args.figure_dir / args.figure_name, result)))
    return 0


if __name__ == "__main__":
    sys.exit(main())






