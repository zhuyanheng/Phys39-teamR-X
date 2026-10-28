"""Exercise the real acquisition window using a fake serial port and temp CSVs.

Run with QT_QPA_PLATFORM=offscreen and the project's .venv Python.
No physical serial connection or actuator command is made.
"""
import csv
import math
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import module_07_rod_acquisition_gui as gui
except ModuleNotFoundError as error:
    gui = None
    IMPORT_ERROR = str(error)

from rod_protocol import build_data_line


class FakeSerial:
    def __init__(self):
        self.is_open = True
        self.pending = b""
        self.commands = []

    @property
    def in_waiting(self):
        return len(self.pending)

    def read(self, count):
        result, self.pending = self.pending[:count], self.pending[count:]
        return result

    def write(self, command):
        self.commands.append(command.decode().strip())
        return len(command)

    def close(self):
        self.is_open = False


@unittest.skipIf(gui is None, "GUI dependencies unavailable")
class AcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = gui.QApplication.instance() or gui.QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root_patch = patch.object(gui, "ROOT", Path(self.temp.name))
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        with patch.object(gui.list_ports, "comports", return_value=[]):
            self.window = gui.RodAcquisitionWindow()
        self.window.timer.stop()
        self.addCleanup(self.window.close)
        self.serial = FakeSerial()
        with patch.object(gui.serial, "Serial", return_value=self.serial):
            self.window.connect_port()

    def feed(self, time_s=1.0, tec=25.0, rods=None, pwm=0, safety="OK"):
        if rods is None:
            rods = [25.0] * 5
        self.serial.pending += (build_data_line(
            time_s, tec, rods, pwm, 1, pwm, 0, 60.0, safety,
            sum(math.isfinite(value) for value in rods)) + "\n").encode()
        self.window.poll_serial()

    def rows(self):
        with self.window.csv_path.open(newline="") as stream:
            return list(csv.DictReader(stream))

    def start(self):
        self.feed()
        self.window.mode.setCurrentText("PI")
        self.window.start_control()
        self.assertTrue(self.window.active)

    def test_passive_logging_includes_all_six_channels_and_warm_bath(self):
        self.feed(tec=55, rods=[54.9, 55.1, 55, 54.8, 55.2])
        self.assertFalse(self.window.active)
        rows = [row for row in self.rows() if row["event"] == "measurement"]
        self.assertEqual(len(rows), 1)
        for name in ("tec_C", "rod1_C", "rod2_C", "rod3_C", "rod4_C", "rod5_C"):
            self.assertTrue(math.isfinite(float(rows[0][name])))
        self.assertTrue(all("PWM 0 " in command for command in self.serial.commands))

    def test_active_setpoint_step_keeps_control_and_integral(self):
        self.start()
        self.feed(time_s=1.5, pwm=10)
        self.feed(time_s=2.0, pwm=10)
        integral = self.window.controller.integral
        self.assertGreater(integral, 0)
        self.window.target.setValue(35)
        self.window.apply_setpoint()
        self.assertTrue(self.window.active)
        self.assertEqual(self.window.controller.setpoint, 35)
        self.assertEqual(self.window.controller.integral, integral)
        self.assertEqual(self.rows()[-1]["event"], "setpoint_step")

    def test_nonzero_output_still_blocks_start(self):
        self.feed(pwm=10)
        with self.assertRaisesRegex(ValueError, "PWM 0"):
            self.window.fresh_safe()

    def test_unsafe_reading_blocks_setpoint_change(self):
        self.start()
        self.window.latest = (1.5, 46, 10, 1, "OK", 10, 0, 60)
        self.window.last_measurement_at = time.monotonic()
        self.window.target.setValue(35)
        self.window.apply_setpoint()
        self.assertFalse(self.window.active)
        self.assertEqual(self.window.controller.setpoint, 30)
        self.assertIn("PWM 0 ", self.serial.commands[-1])

    def test_dead_rod_keeps_control_but_dead_tec_stops_it(self):
        self.start()
        self.feed(time_s=1.5, rods=[25, math.nan, 25, 25, 25])
        self.assertTrue(self.window.active)
        self.assertEqual(self.rows()[-1]["rod_ok"], "4")
        self.feed(time_s=2.0, tec=math.nan, safety="SHUTDOWN")
        self.assertFalse(self.window.active)
        self.assertIn("PWM 0 ", self.serial.commands[-1])

    def test_timeout_and_overtemperature_stop_control(self):
        self.start()
        self.window.last_measurement_at = time.monotonic() - 3
        self.window.poll_serial()
        self.assertFalse(self.window.active)
        self.feed(time_s=2.0)
        self.window.start_control()
        self.assertTrue(self.window.active)
        self.feed(time_s=2.5, tec=46)
        self.assertFalse(self.window.active)
        self.assertIn("PWM 0 ", self.serial.commands[-1])

    def test_bad_serial_number_is_skipped_and_next_row_is_saved(self):
        self.serial.pending = (
            b"#firmware,test\n"
            b"DATA,0.5,25,25,25,25,25,25,inf,0,0,0,60,OK,5\n")
        self.feed()
        self.assertEqual(self.window.accepted, 1)
        self.assertEqual(self.window.rejected, 1)
        self.assertEqual(self.rows()[-1]["event"], "measurement")

    def test_reconnect_creates_a_new_file_and_keeps_previous_data(self):
        self.feed()
        old_path = self.window.csv_path
        self.window.disconnect_port()
        old_content = old_path.read_bytes()
        self.serial = FakeSerial()
        with patch.object(gui.serial, "Serial", return_value=self.serial):
            self.window.connect_port()
        self.feed(time_s=2)
        self.assertNotEqual(old_path, self.window.csv_path)
        self.assertEqual(old_content, old_path.read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
