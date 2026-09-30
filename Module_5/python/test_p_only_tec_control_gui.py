"""Hardware-free checks for the Module 5 controller."""

import csv
import io
import math
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

import p_only_tec_control_gui as controller


class FakeSerial:
    def __init__(self, **_kwargs):
        self.commands = []
        self.is_open = True
        self.in_waiting = 0

    def reset_input_buffer(self):
        pass

    def write(self, data):
        self.commands.append(data.decode("utf-8").strip())

    def close(self):
        self.is_open = False


class ControllerChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_signed_command_and_saturation(self):
        self.assertEqual(controller.p_command(30, 25, 2), (5, 10, 10, True))
        self.assertEqual(controller.p_command(20, 25, 2), (-5, -10, 10, False))
        self.assertEqual(controller.p_command(30, 25, 100), (5, 500, 255, True))
        with self.assertRaises(ValueError):
            controller.p_command(30, math.nan, 2)

    def test_gui_feedback_and_safety_stop(self):
        def open_in_memory(window):
            window.csv_path = Path("fake.csv")
            window.csv_file = io.StringIO()
            window.csv_writer = csv.writer(window.csv_file)

        with patch.object(controller.serial, "Serial", FakeSerial), \
                patch.object(controller.time, "sleep"), \
                patch.object(controller.TecControlWindow, "open_csv_file", open_in_memory):
            window = controller.TecControlWindow()
            try:
                self.assertEqual(window.serial_port.commands[-1], "SET PWM 0 DIR COOL")
                window.process_measurement(1.0, 25.0, 0, 0, "OK", "0", "0", "60")
                window.gain_input.setText("2")
                window.start_p_control()
                window.process_measurement(1.5, 25.0, 0, 0, "OK", "0", "0", "60")
                self.assertEqual(window.serial_port.commands[-1], "SET PWM 10 DIR HEAT")
                window.process_measurement(2.0, 35.0, 10, 1, "OK", "10", "0", "60")
                self.assertEqual(window.serial_port.commands[-1], "SET PWM 10 DIR COOL")
                window.last_measurement_at -= 3.0
                window.read_serial_data()
                self.assertFalse(window.p_control_active)
                self.assertEqual(window.serial_port.commands[-1], "SET PWM 0 DIR COOL")
                window.process_measurement(2.25, 35.0, 0, 0, "OK", "0", "0", "60")
                window.start_p_control()
                window.process_measurement(2.5, 35.0, 0, 0, "SHUTDOWN", "0", "0", "60")
                self.assertFalse(window.p_control_active)
                self.assertEqual(window.serial_port.commands[-1], "SET PWM 0 DIR COOL")
            finally:
                window.close()


if __name__ == "__main__":
    unittest.main()
