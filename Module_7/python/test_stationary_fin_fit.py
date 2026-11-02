"""Hardware-free tests for the Module 7 stationary-fin fit.

    .venv/bin/python Module_7/python/test_stationary_fin_fit.py

Synthetic rods only: no serial port, no Arduino. The tests check that a known m
is recovered from a synthetic steady profile, that the semi-infinite fit is
biased on a long rod (the Part 3 physics claim), that eps_T matches its closed
form, that the steady-state criterion ignores a drifting prologue and refuses a
run that never settles, a run shorter than the hold and a gap in the trailing
window, and that the raw CSV is never modified.
"""
import csv
import contextlib
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1]
SCRIPT = MODULE / "python/analysis/stationary_fin_fit.py"
sys.path.insert(0, str(MODULE / "python"))

from rod_protocol import ROD_CHANNELS  # noqa: E402

spec = importlib.util.spec_from_file_location("stationary_fin_fit", SCRIPT)
fit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fit)

XS = fit.POSITIONS_M
LENGTH = fit.ANALYSIS_LENGTH_M
TRUE_M = 3.5
TRUE_AMBIENT = 21.0
TRUE_THETA0 = 15.0


def profile_temperatures(m=TRUE_M, ambient=TRUE_AMBIENT, theta0=TRUE_THETA0):
    return [ambient + theta0 * fit.theta_finite(x, m, LENGTH) for x in XS]


def make_rows(duration=1200.0, step=0.5, offset=None, gap_rows=()):
    """Rows in the GUI's CSV layout.

    ``offset(t)`` adds a temperature offset that depends only on time, which is
    how a drifting prologue is simulated; ``gap_rows`` lists the row indices at
    which rod3 reads nan, as if the probe were unplugged.
    """
    rows = []
    count = int(round(duration / step)) + 1
    steady = profile_temperatures()
    for index in range(count):
        time_s = index * step
        shift = offset(time_s) if offset else 0.0
        row = {"host_time": "2026-11-02T10:00:00", "event": "measurement",
               "time_s": f"{time_s:.1f}", "tec_C": f"{steady[0] + shift:.4f}",
               "pwm": "0", "heat_cool": "0", "safety": "OK", "rod_ok": "5"}
        for channel, value in zip(ROD_CHANNELS, steady):
            row[f"{channel}_C"] = f"{value + shift:.4f}"
        if index in gap_rows:
            row["rod3_C"] = "nan"
        rows.append(row)
    return rows


def write_rows(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class RecoveryTests(unittest.TestCase):
    def test_recovers_a_known_m_from_a_synthetic_steady_profile(self):
        result, profile = fit.analyse(
            fit.measurement_rows(make_rows()), XS, LENGTH, ambient=TRUE_AMBIENT)
        self.assertEqual(result["status"], "fitted")
        self.assertAlmostEqual(result["finite_model"]["m_per_m"], TRUE_M, places=3)
        self.assertAlmostEqual(result["finite_model"]["one_over_m_m"], 1 / TRUE_M,
                               places=3)
        self.assertLess(result["finite_model"]["rms_C"], 1e-3)
        self.assertEqual(result["finite_model"]["degrees_of_freedom"], len(XS) - 1)
        self.assertEqual(len(profile), len(XS))

    def test_fitted_ambient_recovers_the_room_temperature(self):
        result, _ = fit.analyse(fit.measurement_rows(make_rows()), XS, LENGTH)
        self.assertEqual(result["ambient_mode"], "fitted")
        self.assertAlmostEqual(result["ambient_C"], TRUE_AMBIENT, delta=0.1)
        self.assertAlmostEqual(result["finite_model"]["m_per_m"], TRUE_M, delta=0.05)
        # sigma is deliberately not quoted for the joint fit.
        self.assertTrue(math.isnan(result["finite_model"]["sigma_m_per_m"]))

    def test_semi_infinite_fit_is_biased_on_a_long_rod(self):
        # cosh and exp cannot both describe the same five points: the semi
        # infinite fit comes out flatter, and eps_T grows with x.
        result, _ = fit.analyse(
            fit.measurement_rows(make_rows()), XS, LENGTH, ambient=TRUE_AMBIENT)
        finite = result["finite_model"]["m_per_m"]
        semi = result["semi_infinite_model"]["m_per_m"]
        self.assertLess(semi, finite)
        self.assertGreater(result["semi_infinite_model"]["rms_C"],
                           result["finite_model"]["rms_C"] * 10)
        errors = [row["epsilon_T"] for row in result["epsilon_table"]]
        self.assertAlmostEqual(errors[0], 0.0, places=12)
        self.assertEqual(errors, sorted(errors))
        self.assertGreater(errors[-1], 0.05)

    def test_epsilon_matches_the_closed_form(self):
        result, _ = fit.analyse(
            fit.measurement_rows(make_rows()), XS, LENGTH, ambient=TRUE_AMBIENT)
        m = result["finite_model"]["m_per_m"]
        for row in result["epsilon_table"]:
            finite = math.cosh(m * (LENGTH - row["x_m"])) / math.cosh(m * LENGTH)
            semi = math.exp(-m * row["x_m"])
            self.assertAlmostEqual(row["epsilon_T"],
                                   abs(finite - semi) / abs(finite), places=12)

    def test_bi_numbers_follow_the_measured_m(self):
        result, _ = fit.analyse(
            fit.measurement_rows(make_rows()), XS, LENGTH, ambient=TRUE_AMBIENT,
            diameter=0.0127, diameter_is_measured=True)
        m = result["finite_model"]["m_per_m"]
        self.assertAlmostEqual(result["bi_parallel"], (m * LENGTH) ** 2, places=10)
        self.assertAlmostEqual(result["bi_perp"], (m * 0.0127 / 4.0) ** 2, places=12)
        self.assertTrue(result["diameter_is_measured"])
        self.assertAlmostEqual(result["geometry"]["area_over_perimeter_m"],
                               0.0127 / 4.0, places=10)

    def test_the_skipped_calibration_has_a_measurable_cost(self):
        result, _ = fit.analyse(fit.measurement_rows(make_rows()), XS, LENGTH,
                                ambient=TRUE_AMBIENT)
        sensitivity = result["probe_offset_sensitivity"]
        self.assertAlmostEqual(sensitivity["base_m_per_m"], TRUE_M, places=3)
        by_label = {row["label"]: row for row in sensitivity["probes"]}
        self.assertEqual(len(by_label), len(XS))
        # A hot base probe stretches theta_0 and steepens the fitted decay; a hot
        # tip probe flattens it. Both shifts are far above the fit noise, which is
        # exactly why skipping the cross-calibration soak has to be quoted.
        self.assertGreater(by_label["rod1"]["relative_delta_m"], 0.03)
        self.assertLess(by_label["rod5"]["relative_delta_m"], -0.02)
        for row in sensitivity["probes"]:
            self.assertAlmostEqual(row["m_per_m"],
                                   sensitivity["base_m_per_m"] + row["delta_m_per_m"],
                                   places=12)


class SteadyWindowTests(unittest.TestCase):
    def test_a_transient_prologue_is_excluded(self):
        # 2.5 C of cooling offset until t = 500 s, then a flat profile: the
        # window must start after the transient, and the fit must still be right.
        def offset(time_s):
            return 2.5 * max(0.0, (500.0 - time_s) / 500.0)

        rows = fit.measurement_rows(make_rows(offset=offset))
        result, _ = fit.analyse(rows, XS, LENGTH, ambient=TRUE_AMBIENT)
        self.assertEqual(result["status"], "fitted")
        self.assertGreaterEqual(result["steady_window"]["start_s"], 350.0)
        self.assertAlmostEqual(result["steady_window"]["stop_s"], 1200.0, places=1)
        # The residual 0.1 C common-mode offset the budget tolerates shifts m by
        # ~0.15 %, which is why the budget is quoted rather than assumed.
        self.assertAlmostEqual(result["finite_model"]["m_per_m"], TRUE_M, delta=0.01)

    def test_the_drift_budget_rejects_a_window_that_opens_inside_a_transient(self):
        # The whole-window slope alone is too forgiving here: a fast transient at
        # the left edge of a ten-minute window barely moves the slope. The
        # first-third/last-third budget is what actually rejects those windows.
        def offset(time_s):
            return 2.5 * max(0.0, (500.0 - time_s) / 500.0)

        rows = fit.measurement_rows(make_rows(offset=offset))
        strict, _ = fit.analyse(rows, XS, LENGTH, ambient=TRUE_AMBIENT)
        lax, _ = fit.analyse(rows, XS, LENGTH, ambient=TRUE_AMBIENT, drift_budget=0.0)
        self.assertGreater(strict["steady_window"]["start_s"],
                           lax["steady_window"]["start_s"])
        self.assertLessEqual(strict["steady_window"]["worst_drift_C"],
                             fit.DRIFT_BUDGET_C)

    def test_a_run_that_never_settles_is_refused(self):
        def offset(time_s):
            return 0.05 * time_s  # 3 C/min, forever

        result, profile = fit.analyse(
            fit.measurement_rows(make_rows(offset=offset)), XS, LENGTH,
            ambient=TRUE_AMBIENT)
        self.assertEqual(result["status"], "no-steady-interval")
        self.assertEqual(profile, [])
        self.assertGreater(result["window"]["worst_slope_C_per_min"], 1.0)

    def test_a_run_shorter_than_the_hold_is_refused(self):
        result, _ = fit.analyse(fit.measurement_rows(make_rows(duration=300.0)),
                                XS, LENGTH, ambient=TRUE_AMBIENT)
        self.assertEqual(result["status"], "no-steady-interval")
        self.assertAlmostEqual(result["run_duration_s"], 300.0, places=1)
        self.assertIn("shorter than", result["window"]["reason"])

    def test_a_gap_inside_the_trailing_window_is_refused(self):
        # rod3 drops out 200 s before the end, so every 600 s trailing window
        # contains the gap: there is no stationary profile to fit.
        rows = fit.measurement_rows(make_rows(gap_rows={2000, 2001, 2002}))
        result, _ = fit.analyse(rows, XS, LENGTH, ambient=TRUE_AMBIENT)
        self.assertEqual(result["status"], "no-steady-interval")
        self.assertEqual(result["window"]["slope_channel"], "rod3_C")
        self.assertIn("gap", result["window"]["reason"])

    def test_a_gap_in_the_middle_is_excluded_from_the_window(self):
        rows = fit.measurement_rows(make_rows(gap_rows={1000, 1001}))
        result, _ = fit.analyse(rows, XS, LENGTH, ambient=TRUE_AMBIENT)
        self.assertEqual(result["status"], "fitted")
        self.assertGreater(result["steady_window"]["start_s"], 500.0)
        self.assertAlmostEqual(result["finite_model"]["m_per_m"], TRUE_M, places=3)

    def test_a_gap_at_the_very_end_does_not_throw_away_the_soak(self):
        rows = make_rows()
        for row in rows[-11:]:
            row["rod3_C"] = "nan"
        result, _ = fit.analyse(fit.measurement_rows(rows), XS, LENGTH,
                                ambient=TRUE_AMBIENT)
        self.assertEqual(result["status"], "fitted")
        self.assertEqual(result["rows_used"], len(rows) - 11)
        self.assertAlmostEqual(result["steady_window"]["stop_s"], 1194.5, places=1)



class NumericTests(unittest.TestCase):
    def test_prefix_sums_slope_matches_a_direct_least_squares_fit(self):
        times = [0.5 * index for index in range(200)]
        values = [20.0 + 0.004 * t for t in times]
        table = fit.PrefixSums(times, values)
        self.assertAlmostEqual(table.slope_c_per_min(0, 199), 60 * 0.004, places=9)
        self.assertAlmostEqual(table.slope_c_per_min(50, 120), 60 * 0.004, places=9)

    def test_prefix_sums_reports_a_gap_as_none(self):
        times = [0.5 * index for index in range(10)]
        values = [20.0] * 10
        values[5] = math.nan
        table = fit.PrefixSums(times, values)
        self.assertIsNone(table.slope_c_per_min(0, 9))
        self.assertIsNotNone(table.slope_c_per_min(6, 9))

    def test_golden_minimum_finds_a_parabola_vertex(self):
        vertex = fit.golden_minimum(lambda x: (x - 2.25) ** 2 + 1.0, 0.0, 5.0)
        self.assertAlmostEqual(vertex, 2.25, places=6)


def run_main(rows, tmpdir, figures=False):
    raw = Path(tmpdir) / "synthetic_steady.csv"
    write_rows(raw, rows)
    before = hashlib.sha256(raw.read_bytes()).hexdigest()
    arguments = [str(raw), "--out-dir", tmpdir, "--ambient", f"{TRUE_AMBIENT:g}",
                 "--figure-dir", tmpdir, "--figure-name", "profile.png"]
    if not figures:
        arguments.append("--no-figures")
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        code = fit.main(arguments)
    after = hashlib.sha256(raw.read_bytes()).hexdigest()
    return code, raw, before, after, stream.getvalue()


class CommandLineTests(unittest.TestCase):
    def test_success_writes_strict_portable_outputs_and_keeps_the_raw_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, raw, before, after, _ = run_main(make_rows(), tmp)
            self.assertEqual(code, 0)
            self.assertEqual(before, after)
            json_path = Path(tmp) / "synthetic_steady_stationary_fit.json"
            csv_path = Path(tmp) / "synthetic_steady_stationary_profile.csv"
            self.assertTrue(json_path.exists())
            self.assertTrue(csv_path.exists())
            text = json_path.read_text()

            def reject(constant):
                raise ValueError(f"non-strict JSON constant {constant}")

            result = json.loads(text, parse_constant=reject)
            self.assertEqual(result["source"], raw.name)
            self.assertTrue(result["raw_unchanged"])
            self.assertEqual(result["ambient_mode"], "measured")
            self.assertNotIn(tmp, text)
            with csv_path.open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), len(XS))
            self.assertEqual(rows[0]["label"], "rod1")
            # LF only: a checkout under text=auto must equal what a rerun writes,
            # otherwise the committed CSV shows up as modified after every run.
            self.assertNotIn(b"\r", csv_path.read_bytes())

    def test_refusal_exits_two_and_writes_nothing(self):
        def drifting(time_s):
            return 0.05 * time_s

        with tempfile.TemporaryDirectory() as tmp:
            code, _, before, after, message = run_main(make_rows(offset=drifting), tmp)
            self.assertEqual(code, 2)
            self.assertEqual(before, after)
            self.assertEqual(list(Path(tmp).glob("*_stationary_fit.json")), [])
            self.assertEqual(list(Path(tmp).glob("*_stationary_profile.csv")), [])
            self.assertIn("no trailing window", message)

    def test_a_relaxed_criterion_marks_its_own_output(self):
        def drifting(time_s):
            return 0.01 * time_s

        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "drifting.csv"
            write_rows(raw, make_rows(offset=drifting))
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                code = fit.main([str(raw), "--out-dir", tmp,
                                 "--ambient", f"{TRUE_AMBIENT:g}",
                                 "--slope-limit", "1", "--drift-budget", "10",
                                 "--no-figures"])
            self.assertEqual(code, 0)
            self.assertIn("CRITERION RELAXED", stream.getvalue())
            result = json.loads(
                (Path(tmp) / "drifting_stationary_fit.json").read_text())
            self.assertTrue(result["criterion"]["relaxed"])
            self.assertEqual(result["criterion"]["slope_limit_C_per_min"], 1.0)

    def test_the_pre_registered_criterion_is_not_flagged_as_relaxed(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _, _, message = run_main(make_rows(), tmp)
            self.assertEqual(code, 0)
            self.assertNotIn("CRITERION RELAXED", message)
            result = json.loads(
                (Path(tmp) / "synthetic_steady_stationary_fit.json").read_text())
            self.assertFalse(result["criterion"]["relaxed"])

    def test_positions_must_start_at_zero_and_stay_inside_the_rod(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_rows(Path(tmp) / "rows.csv", make_rows(duration=700.0))
            bad = ("0.0,0.0385,0.0895,0.1405",                  # four values
                   "0.01,0.0385,0.0895,0.1405,0.1915",           # base not at 0
                   "0,0.04,0.09,0.14,0.30")                      # beyond the tip
            for positions in bad:
                stream = io.StringIO()
                with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                    code = fit.main([str(Path(tmp) / "rows.csv"),
                                     "--positions", positions,
                                     "--out-dir", tmp, "--no-figures"])
                self.assertEqual(code, 4, positions)

    def test_the_deliverable_figure_is_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _, _, _ = run_main(make_rows(), tmp, figures=True)
            self.assertEqual(code, 0)
            figure = Path(tmp) / "profile.png"
            self.assertTrue(figure.exists())
            self.assertGreater(figure.stat().st_size, 5000)


if __name__ == "__main__":
    unittest.main(verbosity=2)


