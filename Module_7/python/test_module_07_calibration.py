"""Hardware-free tests for the Module 7 cross-calibration script.

    python3 Module_7/python/test_module_07_calibration.py

Synthetic six-channel runs only: no serial port, no Arduino, no figures required.
The tests check that a known linear sensor error is recovered, that the runbook
criterion actually fails a lagging probe, that ``nan`` and operator rows are
ignored, and that the corrected copy never touches the raw columns.
"""
import csv
import importlib.util
import math
from pathlib import Path
import sys
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1]
SCRIPT = MODULE / "python/analysis/module_07_calibration.py"
sys.path.insert(0, str(MODULE / "python"))

from rod_protocol import FIELD_NAMES, ROD_CHANNELS  # noqa: E402

spec = importlib.util.spec_from_file_location("module_07_calibration", SCRIPT)
calibration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibration)

# One synthetic "true" probe response per channel: T_TEC = a + b * T_i.
TRUE_A = {"rod1": 0.6, "rod2": -0.4, "rod3": 1.1, "rod4": 0.0, "rod5": -1.2}
TRUE_B = {"rod1": 0.985, "rod2": 1.012, "rod3": 0.995, "rod4": 0.973,
          "rod5": 1.004}


def make_rows(reference_values=(20.0, 60.0, 41), extra=None, nan_rods=(),
              events=None):
    """Build raw rows in the GUI's CSV layout.

    ``reference_values`` is ``(start, stop, count)`` for ``tec_C``; each rod
    channel gets a known linear error, plus whatever ``extra`` adds for that
    channel as a function of the reference temperature.
    """
    start, stop, count = reference_values
    rows = []
    for index in range(count):
        tec = start + (stop - start) * index / (count - 1)
        row = {"host_time": "2026-10-26T14:15:02", "event": "measurement",
               "run_id": "synthetic", "time_s": f"{index * 0.5:.1f}",
               "tec_C": f"{tec:.4f}"}
        for channel in ROD_CHANNELS:
            measured = (tec - TRUE_A[channel]) / TRUE_B[channel]
            if extra and channel in extra:
                measured += extra[channel](tec)
            row[f"{channel}_C"] = ("nan" if channel in nan_rods
                                   else f"{measured:.4f}")
        row["pwm"] = "0"
        row["heat_cool"] = "0"
        row["heat_pwm"] = "0"
        row["cool_pwm"] = "0"
        row["limit_C"] = "60.00"
        row["safety"] = "OK"
        row["rod_ok"] = str(len(ROD_CHANNELS) - len(nan_rods))
        rows.append(row)
    for event in events or ():
        line = dict(rows[0])
        line["event"] = event
        rows.insert(0, line)
    return rows


def write_rows(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fit_all(rows):
    return [calibration.fit_channel(rows, channel) for channel in ROD_CHANNELS]


class RecoveryTests(unittest.TestCase):
    def test_recovers_the_known_linear_error(self):
        rows = calibration.measurement_rows(make_rows())
        for channel in ROD_CHANNELS:
            result = calibration.fit_channel(rows, channel)
            # The synthetic CSV stores 4 decimals, so recover to that precision.
            self.assertAlmostEqual(result["a_C_raw"], TRUE_A[channel], places=4)
            self.assertAlmostEqual(result["b_raw"], TRUE_B[channel], places=5)
            self.assertLess(result["residual_max_abs_C"], 1e-3)
            self.assertLess(result["trend_span_C"], 1e-3)

    def test_uncorrected_offset_shows_why_calibration_is_needed(self):
        rows = calibration.measurement_rows(make_rows())
        result = calibration.fit_channel(rows, "rod3")
        # rod 3 sits 1.1 C low, so the uncorrected offset must be negative.
        self.assertLess(result["uncorrected_mean_offset_C"], -0.5)

    def test_corrected_value_lands_on_the_reference(self):
        rows = calibration.measurement_rows(make_rows())
        result = calibration.fit_channel(rows, "rod1")
        tec = float(rows[5]["tec_C"])
        measured = float(rows[5]["rod1_C"])
        corrected = result["a_C_raw"] + result["b_raw"] * measured
        self.assertAlmostEqual(corrected, tec, places=4)


class CriterionTests(unittest.TestCase):
    def test_clean_soak_passes_every_channel(self):
        self.assertTrue(calibration.evaluate(fit_all(make_rows())))

    def test_lagging_probe_fails_the_criterion(self):
        # A probe that lags the bath: residual bows away from zero by > 0.2 C.
        lag = {"rod4": lambda tec: 0.001 * (tec - 40.0) ** 2}
        results = fit_all(make_rows(extra=lag))
        self.assertFalse(calibration.evaluate(results))
        by_channel = {result["channel"]: result for result in results}
        self.assertEqual(by_channel["rod4"]["criterion_met"], "FAIL")
        self.assertEqual(by_channel["rod4"]["criterion_max"], "FAIL")
        self.assertGreater(by_channel["rod4"]["residual_max_abs_C"], 0.2)
        for channel in ("rod1", "rod2", "rod3", "rod5"):
            self.assertEqual(by_channel[channel]["criterion_met"], "PASS")

    def test_one_sided_drift_fails_the_trend_criterion(self):
        # A probe that loses thermal contact above ~50 C: it stops tracking the
        # bath and the corrected reading bows away from the reference. Measured
        # as residual curvature, because a straight-line offset is absorbed by the
        # fit by construction (see fit_channel).
        drift = {"rod5": lambda tec: 0.6 / (1.0 + math.exp(-(tec - 50.0) / 2.0))}
        results = fit_all(make_rows(extra=drift))
        calibration.evaluate(results)
        by_channel = {result["channel"]: result for result in results}
        self.assertEqual(by_channel["rod5"]["criterion_trend"], "FAIL")
        self.assertGreater(by_channel["rod5"]["trend_span_C"], 0.2)

    def test_a_pure_gain_error_is_absorbed_by_b_and_leaves_no_residual(self):
        # Documented limitation: a linear sensor error is exactly what b fixes, so
        # no residual criterion can see it. The corrected column is what removes
        # it - a residual test that flagged it would be a false alarm.
        drift = {"rod3": lambda tec: 0.0015 * (tec - 20.0)}
        results = fit_all(make_rows(extra=drift))
        calibration.evaluate(results)
        by_channel = {result["channel"]: result for result in results}
        self.assertEqual(by_channel["rod3"]["criterion_met"], "PASS")
        self.assertLess(by_channel["rod3"]["residual_max_abs_C"], 0.01)
        self.assertLess(by_channel["rod3"]["trend_span_C"], 0.01)

    def test_residual_mean_is_zero_by_construction(self):
        # Kept as a check that the intercept was actually solved, not as evidence.
        for result in fit_all(make_rows(extra={"rod1": lambda tec: 0.02 * tec})):
            self.assertLess(abs(result["residual_mean_C"]), 1e-3)

    def test_mean_criterion_rejects_a_large_offset(self):
        results = fit_all(make_rows())
        self.assertTrue(calibration.evaluate(results))
        results[0]["residual_mean_C"] = 0.5
        self.assertFalse(calibration.evaluate(results))
        self.assertEqual(results[0]["criterion_mean"], "FAIL")

    def test_max_criterion_rejects_a_large_residual(self):
        results = fit_all(make_rows())
        results[1]["residual_max_abs_C"] = 0.9
        self.assertFalse(calibration.evaluate(results))
        self.assertEqual(results[1]["criterion_max"], "FAIL")
        self.assertEqual(results[1]["criterion_met"], "FAIL")


class InputHandlingTests(unittest.TestCase):
    def test_operator_rows_are_dropped(self):
        rows = make_rows(events=("start", "stop"))
        self.assertEqual(len(rows), 43)
        self.assertEqual(len(calibration.measurement_rows(rows)), 41)

    def test_channel_with_no_usable_samples_is_unusable(self):
        with self.assertRaises(calibration.ChannelUnusable):
            calibration.fit_channel(make_rows(nan_rods=("rod2",)), "rod2")

    def test_usable_rows_count_only_finite_pairs(self):
        rows = make_rows(nan_rods=("rod2",))
        for index, row in enumerate(rows[:5]):
            row["rod2_C"] = f"{23.0 + index:.1f}"
        result = calibration.fit_channel(rows, "rod2")
        self.assertEqual(result["n_points"], 5)
        self.assertEqual(result["n_skipped"], 36)

    def test_too_few_usable_samples_raises(self):
        rows = make_rows(nan_rods=("rod2",))
        rows[0]["rod2_C"] = "23.5"
        rows[1]["rod2_C"] = "24.5"
        with self.assertRaises(calibration.ChannelUnusable):
            calibration.fit_channel(rows, "rod2")

    def test_constant_channel_is_rejected(self):
        rows = make_rows()
        for row in rows:
            row["rod5_C"] = "23.0"
        with self.assertRaises(calibration.ChannelUnusable):
            calibration.fit_channel(rows, "rod5")

    def test_missing_columns_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "not_module_7.csv"
            path.write_text("time_s,temperature_C\n1,20\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                calibration.read_rows(path)


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.rows = make_rows()
        self.results = fit_all(self.rows)
        calibration.evaluate(self.results)
        self.directory = tempfile.TemporaryDirectory()
        self.out = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_table_has_one_row_per_channel_and_every_field(self):
        path = calibration.write_table(self.out / "table.csv", self.results)
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            table = list(reader)
        self.assertEqual(tuple(reader.fieldnames), calibration.TABLE_FIELDS)
        self.assertEqual([row["channel"] for row in table], list(ROD_CHANNELS))
        self.assertEqual([row["criterion_met"] for row in table], ["PASS"] * 5)

    def test_corrected_copy_keeps_raw_columns_untouched(self):
        path = calibration.write_corrected(self.out / "corrected.csv",
                                           self.rows, self.results, "table.csv")
        with path.open(newline="", encoding="utf-8") as stream:
            output = list(csv.DictReader(stream))
        self.assertEqual(len(output), len(self.rows))
        for column in FIELD_NAMES:
            self.assertEqual([row[column] for row in output],
                             [row[column] for row in self.rows])
        for row in output:
            self.assertEqual(row["calibration_file"], "table.csv")
            tec = float(row["tec_C"])
            for channel in ROD_CHANNELS:
                self.assertAlmostEqual(float(row[f"{channel}_corrected_C"]),
                                       tec, places=3)

    def test_nan_stays_nan_in_the_corrected_copy(self):
        rows = make_rows(nan_rods=("rod3",))
        results = [calibration.fit_channel(rows, channel)
                   for channel in ROD_CHANNELS if channel != "rod3"]
        results.append(calibration.fit_channel(make_rows(), "rod3"))
        path = calibration.write_corrected(self.out / "corrected.csv", rows,
                                           results, "table.csv")
        with path.open(newline="", encoding="utf-8") as stream:
            output = list(csv.DictReader(stream))
        self.assertTrue(all(row["rod3_corrected_C"] == "nan" for row in output))


class ColourTests(unittest.TestCase):
    """The figure must use the same pens as the live GUI plot."""

    def gui_pens(self):
        import ast
        source = (MODULE / "python/module_07_rod_acquisition_gui.py").read_text()
        tree = ast.parse(source)
        assignment = next(
            node for node in tree.body
            if isinstance(node, ast.Assign)
            and any(getattr(target, "id", None) == "CHANNEL_PENS"
                    for target in node.targets))
        return eval(compile(ast.Expression(assignment.value), "<PENS>", "eval"),
                    {"__builtins__": {}}, {})

    def test_pens_match_the_gui(self):
        self.assertEqual(calibration.PENS, self.gui_pens())

    def test_skipped_channel_does_not_shift_the_pen(self):
        rows = calibration.measurement_rows(make_rows())
        results = [calibration.fit_channel(rows, channel)
                   for channel in ("rod1", "rod3", "rod5")]
        pens = self.gui_pens()
        self.assertEqual([calibration.channel_colour(result["channel"])
                          for result in results],
                         [pens[1], pens[3], pens[5]])
        self.assertEqual(calibration.channel_colour("tec"), "#555555")


class CommandLineTests(unittest.TestCase):
    def test_end_to_end_on_a_synthetic_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "module_07_rod_20261026_141502_123456.csv"
            write_rows(raw, make_rows())
            before = raw.read_text(encoding="utf-8")
            code = calibration.main([
                str(raw), "--out-dir", str(root / "calibration"),
                "--figure-dir", str(root / "figures"), "--no-figures"])
            self.assertEqual(code, 0)
            table = root / "calibration" / f"module_07_calibration_{raw.stem}.csv"
            self.assertTrue(table.is_file())
            self.assertTrue(
                (root / "calibration" / f"{raw.stem}_corrected.csv").is_file())
            self.assertEqual(raw.read_text(encoding="utf-8"), before)
            self.assertTrue(table.read_text(encoding="utf-8").startswith(
                "channel,reference,n_points"))

    def test_failing_run_returns_a_nonzero_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "run.csv"
            lag = {"rod2": lambda tec: 0.001 * (tec - 40.0) ** 2}
            write_rows(raw, make_rows(extra=lag))
            code = calibration.main([
                str(raw), "--out-dir", str(root / "calibration"),
                "--figure-dir", str(root / "figures"), "--no-figures"])
            self.assertEqual(code, 2)
    def test_dead_channel_becomes_no_data_and_keeps_the_others(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "run.csv"
            write_rows(raw, make_rows(nan_rods=("rod3",)))
            code = calibration.main([
                str(raw), "--out-dir", str(root / "calibration"),
                "--figure-dir", str(root / "figures"), "--no-figures"])
            self.assertEqual(code, 2)
            table = root / "calibration" / "module_07_calibration_run.csv"
            with table.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            status = {row["channel"]: row["criterion_met"] for row in rows}
            self.assertEqual(status["rod3"], "NO DATA")
            self.assertEqual(status["rod1"], "PASS")
            corrected = (root / "calibration" / "run_corrected.csv").read_text(
                encoding="utf-8")
            self.assertNotIn("rod3_corrected_C", corrected)
            self.assertIn("rod1_corrected_C", corrected)


if __name__ == "__main__":
    unittest.main(verbosity=2)

