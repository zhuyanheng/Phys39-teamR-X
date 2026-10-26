"""Hardware-free tests for the Module 7 serial protocol.

    python3 Module_7/python/test_rod_protocol.py

No Qt, no pyqtgraph, no serial port, no Arduino, and no ``.venv`` required. The
tests also check that the parser field names still match the header printed by
the Arduino sketch, so the two cannot drift apart silently.

With the project environment available, the same tests can be run as

    QT_QPA_PLATFORM=offscreen .venv/bin/python Module_7/python/test_rod_protocol.py
"""
import ast
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rod_protocol import (CHANNELS, FIELD_NAMES, ROD_CHANNELS, RodSample,
                          build_data_line, parse_data_line, parse_lines)

MODULE = Path(__file__).resolve().parents[1]
SKETCH = MODULE / "arduino/module_07_rod_controller/module_07_rod_controller.ino"
GUI = MODULE / "python/module_07_rod_acquisition_gui.py"

BANNER = ("#firmware,module_07_rod_controller,2026-10-26\n"
          "#channels,tec=A0,rod1=A1,rod2=A2,rod3=A3,rod4=A4,rod5=A5\n"
          "#pins,heat=D9,cool=D10,baud=9600,report_ms=500\n")


def line(rods=(23.4, 23.3, 23.2, 23.1, 23.0), tec=23.41, time_s=12.5, pwm=120,
         heat_cool=1, safety="OK", rod_ok=5):
    return build_data_line(time_s, tec, rods, pwm, heat_cool, pwm, 0, 60.0,
                           safety, rod_ok)


class FieldOrderTests(unittest.TestCase):
    def test_field_order_is_the_documented_contract(self):
        self.assertEqual(FIELD_NAMES, (
            "time_s", "tec_C", "rod1_C", "rod2_C", "rod3_C", "rod4_C", "rod5_C",
            "pwm", "heat_cool", "heat_pwm", "cool_pwm", "limit_C", "safety",
            "rod_ok"))
        self.assertEqual(len(CHANNELS), 6)
        self.assertEqual(ROD_CHANNELS, ("rod1", "rod2", "rod3", "rod4", "rod5"))

    def test_parser_matches_the_arduino_header(self):
        """Rebuild printHeader() output from the sketch source and compare."""
        source = SKETCH.read_text()
        body = source.split("void printHeader()", 1)[1].split("\n}", 1)[0]
        literals = re.findall(r'"([^"]*)"', body)
        self.assertEqual(len(literals), 4, literals)
        count = int(re.search(r"const int ROD_COUNT = (\d+);", source).group(1))
        self.assertEqual(count, len(ROD_CHANNELS))
        header = (literals[0]
                  + "".join(f"{literals[1]}{index}{literals[2]}"
                            for index in range(1, count + 1))
                  + literals[3])
        self.assertEqual(header, "#DATA," + ",".join(FIELD_NAMES))

    def test_gui_csv_columns_are_generated_from_the_protocol(self):
        """The GUI's FIELDS is evaluated without importing Qt or pyqtgraph."""
        source = GUI.read_text()
        tree = ast.parse(source)
        assignment = next(
            node for node in tree.body
            if isinstance(node, ast.Assign)
            and any(getattr(target, "id", None) == "FIELDS" for target in node.targets))
        fields = eval(compile(ast.Expression(assignment.value), "<FIELDS>", "eval"),
                      {"__builtins__": {"list": list}},
                      {"FIELD_NAMES": FIELD_NAMES})
        start = fields.index("time_s")
        # The CSV measurement block must equal the DATA line, name for name.
        self.assertEqual(fields[start:start + len(FIELD_NAMES)], list(FIELD_NAMES))
        for name in ("host_time", "event", "run_id", "setpoint_C", "error_C", "note"):
            self.assertIn(name, fields)
        self.assertEqual(len(fields), len(set(fields)), "duplicate CSV column")


class ParseTests(unittest.TestCase):
    def test_round_trip_preserves_every_field(self):
        sample = parse_data_line(line())
        self.assertIsInstance(sample, RodSample)
        self.assertEqual(sample.time_s, 12.5)
        self.assertEqual(sample.tec_c, 23.41)
        self.assertEqual(sample.rods_c, (23.4, 23.3, 23.2, 23.1, 23.0))
        self.assertEqual((sample.pwm, sample.heat_cool), (120, 1))
        self.assertEqual((sample.heat_pwm, sample.cool_pwm), (120, 0))
        self.assertEqual(sample.limit_c, 60.0)
        self.assertEqual(sample.safety, "OK")
        self.assertEqual(sample.rod_ok, 5)
        self.assertIsNone(sample.issue())
        self.assertEqual(len(sample.measurement), len(FIELD_NAMES))
        self.assertEqual(sample.measurement[:7], (12.5, 23.41, 23.4, 23.3, 23.2, 23.1, 23.0))

    def test_first_data_line_of_a_real_session_parses(self):
        sample = parse_data_line(
            "DATA,0.50,23.41,23.38,23.36,23.34,23.31,23.29,0,0,0,0,60.00,OK,5")
        self.assertEqual(sample.signed_pwm, 0)
        self.assertEqual(sample.valid_rod_channels, 5)

    def test_diagnostics_blanks_and_headers_are_ignored(self):
        for text in ("#DATA,time_s,tec_C",
                     "#firmware,module_07_rod_controller,2026-10-26",
                     "", "   ", "SET PWM 10 DIR HEAT", "DATA", "DATA,"):
            self.assertIsNone(parse_data_line(text), text)

    def test_crlf_and_padding_are_tolerated(self):
        sample = parse_data_line("  " + line() + "\r")
        self.assertIsNotNone(sample)
        self.assertEqual(sample.rod_ok, 5)

    def test_truncated_and_overlong_lines_are_rejected(self):
        full = line()
        self.assertIsNone(parse_data_line(full[:len(full) // 2]))
        self.assertIsNone(parse_data_line(full + ",extra"))

    def test_malformed_numbers_are_rejected(self):
        self.assertIsNone(parse_data_line(line().replace(",23.40,", ",abc,", 1)))
        self.assertIsNone(parse_data_line(line().replace(",120,1,", ",x,1,", 1)))

    def test_out_of_range_fields_are_rejected(self):
        self.assertIsNone(parse_data_line(line(pwm=300)))
        self.assertIsNone(parse_data_line(line(pwm=-5)))
        self.assertIsNone(parse_data_line(line(heat_cool=2)))
        self.assertIsNone(parse_data_line(line(rod_ok=6)))
        self.assertIsNone(parse_data_line(line(rod_ok=-1)))
        self.assertIsNone(parse_data_line(line(safety="MAYBE")))
        self.assertIsNone(parse_data_line(line(time_s=-1.0)))
        self.assertIsNone(parse_data_line(line(time_s=float("nan"))))

    def test_safety_is_case_insensitive_but_normalised(self):
        self.assertEqual(parse_data_line(line(safety="ok")).safety, "OK")
        self.assertEqual(parse_data_line(line(safety="shutdown")).safety, "SHUTDOWN")

    def test_missing_firmware_echo_fields_stay_optional(self):
        text = line().replace(",120,0,60.00", ",,,")
        sample = parse_data_line(text)
        self.assertIsNotNone(sample)
        self.assertIsNone(sample.heat_pwm)
        self.assertIsNone(sample.cool_pwm)
        self.assertIsNone(sample.limit_c)



class ChannelValidityTests(unittest.TestCase):
    def test_nan_rod_channel_keeps_the_line_and_is_counted(self):
        sample = parse_data_line(
            line(rods=(23.4, float("nan"), 23.2, 23.1, 23.0), rod_ok=4))
        self.assertIsNotNone(sample)
        self.assertEqual(sample.rod_ok, 4)
        self.assertEqual(sample.valid_rod_channels, 4)
        # The actuator path is unaffected by a bad rod probe.
        self.assertIsNone(sample.issue())

    def test_nan_tec_channel_blocks_control(self):
        sample = parse_data_line(line(tec=float("nan")))
        self.assertIsNotNone(sample)
        self.assertIn("not a finite number", sample.issue())

    def test_tec_outside_operating_range_blocks_control(self):
        self.assertIn("outside", parse_data_line(line(tec=52.0)).issue())
        self.assertIn("outside", parse_data_line(line(tec=4.0)).issue())
        self.assertIsNone(parse_data_line(line(tec=45.0)).issue())

    def test_shutdown_state_blocks_control(self):
        self.assertIn("SHUTDOWN", parse_data_line(line(safety="SHUTDOWN")).issue())

    def test_signed_pwm_follows_the_module_6_convention(self):
        self.assertEqual(parse_data_line(line(pwm=120, heat_cool=1)).signed_pwm, 120)
        self.assertEqual(parse_data_line(line(pwm=120, heat_cool=0)).signed_pwm, -120)


class StreamTests(unittest.TestCase):
    def test_a_whole_session_block_parses_in_order(self):
        block = (BANNER + "#DATA," + ",".join(FIELD_NAMES) + "\n"
                 + line(time_s=0.5) + "\n"
                 + "garbage line\n"
                 + line(time_s=1.0) + "\n"
                 + line(time_s=1.5))
        samples = parse_lines(block)
        self.assertEqual([sample.time_s for sample in samples], [0.5, 1.0, 1.5])
        self.assertEqual(samples[-1].tec_c, 23.41)

    def test_repeated_arduino_time_is_not_a_new_sample(self):
        """The GUI stops control when the Arduino time does not advance."""
        first, repeated = parse_lines(line(time_s=10.0) + "\n" + line(time_s=10.0))
        self.assertEqual(first.time_s, repeated.time_s)
        self.assertFalse(repeated.time_s > first.time_s)


if __name__ == "__main__":
    unittest.main(verbosity=2)

