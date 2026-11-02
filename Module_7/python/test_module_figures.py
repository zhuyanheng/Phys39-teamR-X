"""Hardware-free tests for the Module 7 deliverable figures.

    .venv/bin/python Module_7/python/test_module_figures.py

Both figure scripts read raw data or a fixed geometry and write one PNG. The
tests check that the geometry figure is really drawn, that event rows without a
`time_s` are placed on the Arduino axis from their wall clock, that commanded
regions and the limit-cycle numbers are computed from the CSV rather than typed
in, and that a CSV with no measurement rows is refused instead of producing an
empty plot.
"""
import csv
import importlib.util
import math
from datetime import datetime
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1]
ANALYSIS = MODULE / "python/analysis"
KEYS = ["tec_C"] + [f"rod{i}_C" for i in range(1, 6)]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ANALYSIS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sensor_map = load("sensor_map_figure")
step_response = load("step_response_figure")

ORIGIN_WALL = "2026-11-02T10:00:00-05:00"


def measurement(seconds, tec, offset=0.0, kp=1.0, ki=0.0):
    row = {"host_time": f"2026-11-02T10:{int(seconds) // 60:02d}:{seconds % 60:05.2f}-05:00",
           "event": "measurement", "time_s": f"{seconds:.1f}",
           "safety": "OK", "Kp_pwm_per_C": f"{kp}", "Ki_pwm_per_C_s": f"{ki}",
           "tec_C": f"{tec:.4f}"}
    for index, key in enumerate(KEYS[1:]):
        row[key] = f"{tec - 0.5 * (index + 1) + offset:.4f}"
    return row


def event(seconds, name, setpoint="", note=""):
    return {"host_time": f"2026-11-02T10:{int(seconds) // 60:02d}:{seconds % 60:05.2f}-05:00",
            "event": name, "time_s": "", "setpoint_C": setpoint, "note": note,
            "safety": "OK"}


def run_rows(duration=240.0, step=2.0):
    rows = [event(0.0, "start", "40")]
    rows.append(event(120.0, "setpoint_step", "45"))
    for index in range(int(duration / step) + 1):
        seconds = index * step
        tec = 40.0 + 0.5 * math.sin(2 * math.pi * seconds / 120.0)
        rows.append(measurement(seconds, tec))
    rows.append(event(duration, "stop", "", note="Interlock: probe above limit"))
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


class SensorMapTests(unittest.TestCase):
    def test_the_map_is_drawn_and_the_file_is_not_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = sensor_map.draw(Path(tmp) / "map.png")
            self.assertEqual(path, Path(tmp) / "map.png")
            self.assertGreater(path.stat().st_size, 10_000)

    def test_the_cli_writes_where_it_is_told(self):
        with tempfile.TemporaryDirectory() as tmp:
            status = sensor_map.main(["--out", str(Path(tmp) / "map.png")])
            self.assertEqual(status, 0)
            self.assertTrue((Path(tmp) / "map.png").exists())

    def test_the_geometry_matches_the_field_record(self):
        self.assertEqual(sensor_map.HOLES, (2, 5, 7, 8, 9))
        self.assertAlmostEqual(sensor_map.POSITIONS_CM[-1], 19.15)
        self.assertAlmostEqual(sensor_map.LENGTH_CM, 27.15)
        self.assertTrue(all(b > a for a, b in
                            zip(sensor_map.POSITIONS_CM, sensor_map.POSITIONS_CM[1:])))


class EventTests(unittest.TestCase):
    def test_an_event_without_a_time_s_is_placed_by_its_wall_clock(self):
        origin_wall = datetime.fromisoformat(ORIGIN_WALL)
        row = event(90.0, "setpoint_step", "45")
        self.assertEqual(step_response.event_seconds(row, origin_wall, 0.5), 90.5)

    def test_a_row_without_a_usable_wall_clock_has_no_time(self):
        origin_wall = datetime.fromisoformat(ORIGIN_WALL)
        self.assertIsNone(step_response.event_seconds({"host_time": "nonsense"},
                                                      origin_wall, 0.0))
        self.assertIsNone(step_response.event_seconds({}, origin_wall, 0.0))

    def test_commanded_regions_come_from_start_step_and_stop(self):
        records = run_rows(duration=240.0, step=2.0)
        regions = step_response.commanded_regions(
            records, datetime.fromisoformat(ORIGIN_WALL), 0.0)
        self.assertEqual([(round(a, 1), round(b, 1), setpoint)
                          for a, b, setpoint in regions],
                         [(0.0, 120.0, 40.0), (120.0, 240.0, 45.0)])

    def test_a_region_that_never_closes_is_dropped(self):
        records = [event(0.0, "start", "40"), event(60.0, "setpoint_step", "40")]
        regions = step_response.commanded_regions(
            records, datetime.fromisoformat(ORIGIN_WALL), 0.0)
        self.assertEqual(len(regions), 1)


class LimitCycleTests(unittest.TestCase):
    def test_the_cycle_is_measured_from_the_trace(self):
        rows = run_rows(duration=600.0, step=1.0)
        cycle = step_response.limit_cycle(rows, start_after=0.0)
        self.assertAlmostEqual(cycle["mean_C"], 40.0, delta=0.05)
        self.assertAlmostEqual(cycle["half_range_C"], 0.5, delta=0.05)
        self.assertAlmostEqual(cycle["period_s"], 120.0, delta=2.0)
        self.assertGreater(cycle["samples"], 500)

    def test_a_quiet_or_short_record_has_no_cycle_to_report(self):
        self.assertIsNone(step_response.limit_cycle(run_rows(duration=10.0),
                                                    start_after=0.0))
        self.assertIsNone(step_response.limit_cycle(run_rows(duration=600.0),
                                                    start_after=1e9))


class StepResponseFigureTests(unittest.TestCase):
    def test_the_figure_is_drawn_from_the_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "run.csv"
            write_rows(raw, run_rows())
            path = step_response.draw(raw, Path(tmp) / "step.png")
            self.assertEqual(path, Path(tmp) / "step.png")
            self.assertGreater(path.stat().st_size, 10_000)

    def test_a_csv_without_measurements_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "empty.csv"
            write_rows(raw, [event(0.0, "start", "40"), event(1.0, "stop")])
            with self.assertRaises(ValueError):
                step_response.draw(raw, Path(tmp) / "step.png")


if __name__ == "__main__":
    unittest.main()
