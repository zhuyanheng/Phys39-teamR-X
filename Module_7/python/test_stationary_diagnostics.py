"""Hardware-free tests for the Module 7 stationary-fit diagnostics.

    .venv/bin/python Module_7/python/test_stationary_diagnostics.py

Synthetic rods only. The tests check that the exponential-approach helper
recovers a known time constant, that a window mean ignores rows outside the
window, that on a rod whose probes settle with different lags the asymptote
extrapolation lands closer to the true m than the trailing-window fit (the
reason the script exists), and that the CLI writes strict JSON and leaves the
raw CSV byte-identical.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

import csv

MODULE = Path(__file__).resolve().parents[1]
SCRIPT = MODULE / "python/analysis/stationary_diagnostics.py"

spec = importlib.util.spec_from_file_location("stationary_diagnostics", SCRIPT)
diagnostics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostics)
fit = diagnostics.fit

XS = fit.POSITIONS_M
LENGTH = fit.ANALYSIS_LENGTH_M
TRUE_M = 3.5
TRUE_AMBIENT = 21.0
TRUE_THETA0 = 15.0


def settling_rows(duration=2400.0, step=1.0, lag0=300.0, lag_step=150.0,
                  ambient=TRUE_AMBIENT, m=TRUE_M):
    """Rows in which probe i approaches its steady value with lag0 + i*lag_step.

    Probes further from the base lag more, which is what makes a fit on an
    unfinished hold biased: the profile read at one instant is not the steady
    profile any more.
    """
    rows = []
    count = int(round(duration / step)) + 1
    for index in range(count):
        time_s = index * step
        row = {"host_time": "2026-11-02T10:00:00", "event": "measurement",
               "time_s": f"{time_s:.1f}", "safety": "OK", "rod_ok": "5"}
        for probe, x in enumerate(XS):
            steady = ambient + TRUE_THETA0 * fit.theta_finite(x, m, LENGTH)
            lag = lag0 + probe * lag_step
            value = ambient + (steady - ambient) * (1.0 - math.exp(-time_s / lag))
            row[f"rod{probe + 1}_C"] = f"{value:.6f}"
        rows.append(row)
    return rows


def write_rows(path, rows):
    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


class AsymptoteTests(unittest.TestCase):
    def test_a_known_time_constant_and_level_are_recovered(self):
        for tau in (300.0, 900.0, 1800.0):
            pairs = [(float(t), 30.0 + 6.0 * math.exp(-(t - 600.0) / tau))
                     for t in range(600, 2400, 5)]
            result = diagnostics.fit_asymptote(pairs)
            self.assertAlmostEqual(result["tau_s"] / tau, 1.0, places=2)
            self.assertAlmostEqual(result["asymptote_C"], 30.0, places=6)
            self.assertLess(result["rms_C"], 1e-6)

    def test_the_rise_left_is_the_part_of_the_record_that_is_still_coming(self):
        pairs = [(float(t), 30.0 - 4.0 * math.exp(-t / 1000.0))
                 for t in range(0, 1001, 5)]
        result = diagnostics.fit_asymptote(pairs)
        self.assertAlmostEqual(result["rise_left_C"], 4.0 * math.exp(-1.0), places=3)
        self.assertAlmostEqual(result["asymptote_C"] - pairs[-1][1],
                               result["rise_left_C"], places=6)
        self.assertGreater(result["amplitude_C"], result["rise_left_C"])

    def test_too_few_rows_is_refused_rather_than_guessed(self):
        self.assertIsNone(diagnostics.fit_asymptote([(0.0, 1.0), (1.0, 2.0)]))


class WindowTests(unittest.TestCase):
    def test_the_window_mean_ignores_rows_outside_it(self):
        rows = [{"time_s": f"{t:.1f}",
                 **{key: f"{t:.1f}" for key in fit.ROD_CHANNELS}}
                for t in range(0, 101)]
        means = diagnostics.window_means(rows, list(fit.ROD_CHANNELS), 10.0, 20.0)
        self.assertEqual(means, [15.0] * len(fit.ROD_CHANNELS))
        self.assertIsNone(
            diagnostics.window_means(rows, list(fit.ROD_CHANNELS), 200.0, 300.0))


class SummariseTests(unittest.TestCase):
    def setUp(self):
        self.rows = settling_rows()
        self.result = diagnostics.summarise(
            self.rows, list(fit.ROD_CHANNELS), XS, LENGTH, TRUE_AMBIENT,
            window=600.0, step=300.0)

    def test_the_extrapolation_recovers_the_steady_m(self):
        extrapolation = self.result["extrapolation"]
        self.assertIsNotNone(extrapolation)
        self.assertLess(abs(extrapolation["m_per_m"] / TRUE_M - 1.0), 0.01)

    def test_the_unfinished_window_fit_is_the_worse_estimate(self):
        base = self.result["base"]["m_per_m"]
        extrapolation = self.result["extrapolation"]["m_per_m"]
        self.assertGreater(abs(base / TRUE_M - 1.0),
                           abs(extrapolation / TRUE_M - 1.0))
        # probes near the base catch up first, so the unfinished profile is too
        # steep and the window fit overshoots m; the record then relaxes towards
        # the steady value from above.
        self.assertGreater(base, TRUE_M)
        self.assertLess(extrapolation, base)

    def test_every_systematic_term_is_present(self):
        self.assertEqual(set(self.result),
                         {"window", "ambient_C", "positions_m", "analysis_length_m",
                          "base", "window_slide", "extrapolation", "ambient",
                          "geometry", "origin_swap"})
        self.assertEqual(len(self.result["geometry"]), 6)
        self.assertEqual(len(self.result["ambient"]), 6)
        self.assertEqual(len(self.result["window_slide"]), 7)
        self.assertAlmostEqual(self.result["window_slide"][-1]["stop_s"],
                               self.result["window"]["stop_s"])
        self.assertEqual(self.result["origin_swap"]["probes"],
                         list(fit.ROD_CHANNELS[1:]))

    def test_the_ambient_term_has_the_sign_of_the_shift(self):
        changes = {row["delta_C"]: row["change_percent"]
                   for row in self.result["ambient"]}
        self.assertGreater(changes[0.5], 0.0)
        self.assertLess(changes[-0.5], 0.0)
        self.assertGreater(changes[0.5], changes[0.25])


class CommandLineTests(unittest.TestCase):
    def test_the_cli_writes_strict_json_and_leaves_the_raw_file_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "run.csv"
            write_rows(raw, settling_rows(duration=1500.0))
            before = hashlib.sha256(raw.read_bytes()).hexdigest()
            with tempfile.TemporaryDirectory() as out:
                status = diagnostics.main([str(raw), "--ambient", "21.0",
                                           "--window", "600", "--step", "300",
                                           "--out-dir", out])
                self.assertEqual(status, 0)
                path = Path(out) / "run_stationary_diagnostics.json"
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("NaN", text)
                payload = json.loads(text)
            self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(), before)
            self.assertTrue(payload["raw_unchanged"])
            self.assertEqual(payload["source_sha256"], before)
            self.assertEqual(payload["source"], "run.csv")
            self.assertEqual(set(payload["worst_change_percent"]),
                             {"ambient", "geometry", "window_slide"})

    def test_a_record_shorter_than_the_window_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "short.csv"
            write_rows(raw, settling_rows(duration=300.0))
            with tempfile.TemporaryDirectory() as out:
                status = diagnostics.main([str(raw), "--ambient", "21.0",
                                           "--out-dir", out])
                self.assertEqual(status, 2)
                self.assertFalse(list(Path(out).iterdir()))

    def test_positions_outside_the_rod_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "run.csv"
            write_rows(raw, settling_rows(duration=1500.0))
            with tempfile.TemporaryDirectory() as out:
                status = diagnostics.main([str(raw), "--ambient", "21.0",
                                           "--positions", "0,0.03,0.08,0.14,0.40",
                                           "--out-dir", out])
                self.assertEqual(status, 4)


if __name__ == "__main__":
    unittest.main()
