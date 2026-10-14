"""Hardware-free tests: arithmetic, timing, anti-windup and serial transitions.

QT_QPA_PLATFORM=offscreen .venv/bin/python Module_6/python/test_pi_control.py
"""
import csv
import io
import math
from pathlib import Path
import unittest
from unittest.mock import patch
from pi_controller import PIController


class ArithmeticTests(unittest.TestCase):
    def test_p_compatibility_and_signed_clamp(self):
        p=PIController("P",30,2,100,45)
        first=p.step(10,25)
        self.assertEqual((first.error_c,first.p_pwm,first.i_pwm,first.sent_pwm),(5,10,0,10))
        p.setpoint=20
        self.assertEqual(p.step(10.5,25).sent_pwm,-10)
        p.kp=100
        result=p.step(11,25)
        self.assertEqual(result.sent_pwm,-45)
        self.assertTrue(result.saturated)
        self.assertEqual(result.integral_c_s,0)

    def test_integral_uses_actual_accepted_sample_interval(self):
        p=PIController("PI",30,2,.1,45)
        self.assertEqual(p.step(100,25).dt_s,0)
        r=p.step(100.7,25)
        self.assertAlmostEqual(r.dt_s,.7)
        self.assertAlmostEqual(r.integral_c_s,3.5)
        self.assertAlmostEqual(r.i_pwm,.35)
        r=p.step(101,25)
        self.assertAlmostEqual(r.integral_c_s,5)

    def test_anti_windup_both_directions(self):
        for target,T in [(30,20),(20,30)]:
            p=PIController("PI",target,10,1,45,True)
            p.step(0,T);r=p.step(.5,T)
            self.assertTrue(r.integration_blocked)
            self.assertEqual(r.integral_c_s,0)
            self.assertEqual(abs(r.sent_pwm),45)
            p.anti_windup=False;r=p.step(1,T)
            self.assertEqual(abs(r.integral_c_s),5)

    def test_integrator_can_unwind_and_preserve_drive_at_zero_error(self):
        p=PIController("PI",30,0,1,45)
        p.integral=100;p.previous_time=0
        r=p.step(.5,31)
        self.assertFalse(r.integration_blocked)
        self.assertEqual(r.integral_c_s,99.5)
        p.integral=10
        r=p.step(1,30)
        self.assertEqual((r.p_pwm,r.i_pwm,r.sent_pwm),(0,10,10))

    def test_bad_time_temperature_and_reset(self):
        for stamp in [10,9,13,math.nan]:
            p=PIController("PI");p.step(10,25)
            with self.assertRaises(ValueError):p.step(stamp,25)
        for T in [math.nan,math.inf,9,46]:
            with self.assertRaises(ValueError):PIController().step(0,T)
        p=PIController("PI");p.integral=100;p.previous_time=10;p.reset()
        self.assertEqual(p.integral,0);self.assertIsNone(p.previous_time)


class FakeSerial:
    def __init__(self,*args,**kwargs):self.is_open=True;self.commands=[];self.in_waiting=0
    def write(self,payload):self.commands.append(payload.decode().strip());return len(payload)
    def close(self):self.is_open=False


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pi_tec_control_gui as gui
        cls.gui=gui
        cls.app=gui.QApplication.instance() or gui.QApplication([])

    def setUp(self):
        self.window=self.gui.PIControlWindow()
        self.window.timer.stop()
        self.fake=FakeSerial()
        self.window.serial_port=self.fake
        self.window.csv_file=io.StringIO()
        self.window.csv_writer=csv.DictWriter(self.window.csv_file,fieldnames=self.gui.FIELDS)
        self.window.csv_writer.writeheader()
        self.window.process_measurement(10,25,0,0,"OK","0","0","60")

    def tearDown(self):self.window.close()

    def begin_pi(self):
        w=self.window;w.mode.setCurrentText("PI");w.kp.setValue(2);w.ki.setValue(.1)
        w.start_control();self.assertTrue(w.active)

    def test_gui_pi_csv_stop_reset_and_mode(self):
        w=self.window;self.begin_pi()
        w.process_measurement(10.5,25,0,0,"OK","0","0","60")
        w.process_measurement(11.2,25,10,1,"OK","10","0","60")
        self.assertAlmostEqual(w.last_result.i_pwm,.35)
        rows=list(csv.DictReader(io.StringIO(w.csv_file.getvalue())))
        r=rows[-1]
        self.assertAlmostEqual(float(r['dt_s']),.7)
        self.assertAlmostEqual(float(r['i_term_pwm']),.35)
        self.assertEqual(r['reported_signed_pwm'],'10')
        self.assertEqual(r['sent_signed_pwm'],'10')
        w.zero_integral()
        self.assertFalse(w.active);self.assertEqual(w.controller.integral,0)
        self.assertEqual(self.fake.commands[-1],"SET PWM 0 DIR COOL")
        w.mode.setCurrentText('P')
        self.assertEqual(self.fake.commands[-1],"SET PWM 0 DIR COOL")

    def test_setpoint_steps_preserve_integral_but_only_apply_on_button(self):
        w=self.window;self.begin_pi()
        w.process_measurement(10.5,25,0,0,"OK","0","0","60")
        w.process_measurement(11,25,10,1,"OK","10","0","60")
        q=w.controller.integral;w.target.setValue(20)
        self.assertEqual(w.controller.setpoint,30)
        w.apply_setpoint();self.assertEqual(w.controller.integral,q)
        w.process_measurement(11.5,25,10,1,"OK","10","0","60")
        self.assertLess(w.last_result.sent_pwm,0)
        self.assertFalse(w.kp.isEnabled());self.assertFalse(w.mode.isEnabled())

    def test_safety_fault_and_time_reset_stop(self):
        for args in [(11,25,0,0,"SHUTDOWN","0","0","60"),
                     (11,math.nan,0,0,"OK","0","0","60"),
                     (9,25,0,0,"OK","0","0","60")]:
            self.window.latest=None
            self.window.process_measurement(10,25,0,0,"OK","0","0","60")
            self.begin_pi();self.window.process_measurement(*args)
            self.assertFalse(self.window.active)
            self.assertEqual(self.fake.commands[-1],"SET PWM 0 DIR COOL")

    def test_timeout_and_serial_error_stop(self):
        w=self.window;self.begin_pi();w.last_measurement_at-=3;w.poll_serial()
        self.assertFalse(w.active);self.assertEqual(self.fake.commands[-1],"SET PWM 0 DIR COOL")
        w.last_measurement_at=self.gui.time.monotonic();w.start_control()
        with patch.object(self.fake,'write',side_effect=self.gui.serial.SerialException('disconnected')):
            w.process_measurement(11,25,0,0,"OK","0","0","60")
        self.assertFalse(w.active)

    def test_serial_backlog_does_not_replay_actuator_commands(self):
        w=self.window;self.begin_pi();n=len(self.fake.commands)
        w.process_measurement(10.5,25,0,0,"OK","0","0","60",backlog=True)
        self.assertEqual(len(self.fake.commands),n)
        w.process_measurement(11,25,0,0,"OK","0","0","60")
        self.assertEqual(len(self.fake.commands),n+1)

    def test_disconnected_start_does_not_arm(self):
        w=self.window;w.serial_port=None
        with patch.object(self.gui.QMessageBox,'warning'):
            w.start_control()
        self.assertFalse(w.active)
        self.assertFalse(w.start.isEnabled())

    def test_usb_port_is_preselected_without_opening_it(self):
        from types import SimpleNamespace
        devices=[SimpleNamespace(device='/dev/cu.debug-console'),
                 SimpleNamespace(device='/dev/cu.usbmodem101')]
        with patch.object(self.gui.list_ports,'comports',return_value=devices), \
             patch.object(self.gui.serial,'Serial') as opener:
            w=self.gui.PIControlWindow()
            try:
                self.assertEqual(w.port.currentText(),'/dev/cu.usbmodem101')
                self.assertFalse(w.start.isEnabled());opener.assert_not_called()
            finally:w.close()

    def test_nonzero_firmware_output_blocks_start(self):
        w=self.window;w.process_measurement(10.5,25,30,1,"OK","30","0","60")
        with patch.object(self.gui.QMessageBox,'warning'):w.start_control()
        self.assertFalse(w.active);self.assertEqual(self.fake.commands[-1],"SET PWM 0 DIR COOL")

    def test_log_failure_requests_zero_and_does_not_recurse(self):
        w=self.window;self.begin_pi()
        with patch.object(w.csv_writer,'writerow',side_effect=OSError('disk full')):
            w.process_measurement(10.5,25,0,0,"OK","0","0","60")
        self.assertFalse(w.active);self.assertIsNone(w.csv_writer)
        self.assertEqual(self.fake.commands[-1],"SET PWM 0 DIR COOL")

    def test_partial_serial_write_disarms(self):
        w=self.window;self.begin_pi()
        with patch.object(self.fake,'write',return_value=1):
            w.process_measurement(10.5,25,0,0,"OK","0","0","60")
        self.assertFalse(w.active);self.assertIsNone(w.serial_port)

    def test_preview_never_opens_serial(self):
        with patch.object(self.gui.serial,'Serial') as opener:
            w=self.gui.PIControlWindow(preview=True)
            try:
                w.connect_port();opener.assert_not_called()
                self.assertIsNone(w.csv_file);self.assertFalse(w.start.isEnabled())
            finally:w.close()


if __name__=='__main__':unittest.main(verbosity=2)
