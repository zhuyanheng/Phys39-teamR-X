"""Offline smoke tests for the A2 plotter; all data here are synthetic."""

import csv
import tempfile
import unittest
from pathlib import Path

import plot_a2


class PlotA2Test(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.raw_path = self.root / "synthetic_raw.csv"
        self.summary_path = self.root / "synthetic_steady_state.csv"
        raw_rows = []
        summary_rows = []
        for prefix, direction, bit in (("H", "HEAT", 1), ("C", "COOL", 0)):
            for index, pwm in enumerate((0, 10, 20, 30, 40)):
                base = (0 if prefix == "H" else 1000) + index * 100
                temperature = 22 + (index if prefix == "H" else -index)
                for offset in (0, 1, 2, 3):
                    raw_rows.append({
                        "time_s": base + offset,
                        "temperature_C": temperature,
                        "pwm": pwm,
                        "heat_cool": bit,
                        "safety": "OK",
                        "heat_pwm_firmware": pwm if prefix == "H" else 0,
                        "cool_pwm_firmware": pwm if prefix == "C" else 0,
                        "limit_C": 60,
                    })
                summary_rows.append({
                    "run_id": f"{prefix}{index}",
                    "direction": direction,
                    "pwm": pwm,
                    "start_temperature_C": 22,
                    "steady_temperature_C": temperature,
                    "time_waited_s": "" if pwm == 0 else 1,
                    "source_csv": str(self.raw_path),
                    "steady_start_s": base + 1,
                    "steady_end_s": base + 3,
                    "range_exception_approved": "no",
                    "notes": "synthetic fixture",
                })
        self.write_rows(self.raw_path, raw_rows)
        self.write_rows(self.summary_path, summary_rows)

    @staticmethod
    def write_rows(path, rows):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def test_figure_generation_from_valid_windows(self):
        summary = plot_a2.read_summary(self.summary_path)
        raw_cache = {}
        plot_a2.validate_windows(summary, raw_cache)
        output = self.root / "figures"
        plot_a2.create_figures(summary, raw_cache, output, "synthetic test rule",
                               {"HEAT": (0, 40), "COOL": (0, 40)})
        for name in ("part_4_heating_trace.svg", "part_4_cooling_trace.svg", "part_4_steady_temperature_vs_pwm.svg"):
            self.assertIn("<svg", (output / name).read_text(encoding="utf-8"))
        main_figure = (output / "part_4_steady_temperature_vs_pwm.svg").read_text(encoding="utf-8")
        self.assertIn("Signed PWM", main_figure)
        self.assertIn('stroke-dasharray="9 5"', main_figure)

    def test_shutdown_window_is_rejected(self):
        fields, rows = plot_a2.read_csv(self.raw_path)
        self.assertIn("safety", fields)
        rows[1]["safety"] = "SHUTDOWN"
        self.write_rows(self.raw_path, rows)
        summary = plot_a2.read_summary(self.summary_path)
        with self.assertRaisesRegex(ValueError, "safety is not OK"):
            plot_a2.validate_windows(summary, {})

    def test_unapproved_out_of_range_window_is_rejected(self):
        _, rows = plot_a2.read_csv(self.raw_path)
        for row in rows:
            if float(row["time_s"]) in (301, 302, 303):
                row["temperature_C"] = "45.3"
        self.write_rows(self.raw_path, rows)
        _, summary_rows = plot_a2.read_csv(self.summary_path)
        next(row for row in summary_rows if row["run_id"] == "H3")["steady_temperature_C"] = "45.3"
        self.write_rows(self.summary_path, summary_rows)
        with self.assertRaisesRegex(ValueError, "outside 10–45"):
            plot_a2.read_summary(self.summary_path)

    def test_approved_exception_is_plotted(self):
        _, rows = plot_a2.read_csv(self.raw_path)
        for row in rows:
            if float(row["time_s"]) in (301, 302, 303):
                row["temperature_C"] = "45.3"
        self.write_rows(self.raw_path, rows)
        _, summary_rows = plot_a2.read_csv(self.summary_path)
        flagged = next(row for row in summary_rows if row["run_id"] == "H3")
        flagged["steady_temperature_C"] = "45.3"
        flagged["range_exception_approved"] = "yes"
        self.write_rows(self.summary_path, summary_rows)
        summary = plot_a2.read_summary(self.summary_path)
        raw_cache = {}
        plot_a2.validate_windows(summary, raw_cache)
        output = self.root / "figures"
        plot_a2.create_figures(summary, raw_cache, output, "test criterion",
                               {"HEAT": (0, 40), "COOL": (0, 40)})
        main_figure = (output / "part_4_steady_temperature_vs_pwm.svg").read_text(encoding="utf-8")
        self.assertIn("instructor-approved", main_figure)

    def test_zero_pwm_direction_is_checked(self):
        _, rows = plot_a2.read_csv(self.raw_path)
        rows[1]["heat_cool"] = "0"
        self.write_rows(self.raw_path, rows)
        summary = plot_a2.read_summary(self.summary_path)
        with self.assertRaisesRegex(ValueError, "raw direction differs"):
            plot_a2.validate_windows(summary, {})


if __name__ == "__main__":
    unittest.main()
