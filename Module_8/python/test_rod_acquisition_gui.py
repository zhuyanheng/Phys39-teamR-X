"""Qt/fake-serial integration. No physical serial port or real output is used."""
import csv
import json
import math
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch,Mock
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import rod_acquisition_gui as gui
from rod_protocol import build_data_line

class FakeSerial:
    def __init__(self):self.is_open=True;self.pending=b'';self.commands=[];self.transmit=b'';self.write_sizes=[]
    @property
    def in_waiting(self):return len(self.pending)
    def read(self,n):result,self.pending=self.pending[:n],self.pending[n:];return result
    def write(self,command):
        self.write_sizes.append(len(command));self.transmit+=command
        while b'\n' in self.transmit:
            line,self.transmit=self.transmit.split(b'\n',1);text=line.decode().strip()
            if not text:continue
            self.commands.append(text);tag=text.split()[0]
            if tag!='PING':self.pending+=(f'#ACK,{tag}'+(',module_08_angstrom_v1' if tag=='HELLO' else '')+'\n').encode()
        return len(command)
    def close(self):self.is_open=False

class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=gui.QApplication.instance() or gui.QApplication([])
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.rootpatch=patch.object(gui,'ROOT',self.root);self.rootpatch.start();self.addCleanup(self.rootpatch.stop)
        with patch.object(gui.list_ports,'comports',return_value=[]):self.window=gui.RodAcquisitionWindow()
        self.window.timer.stop();self.addCleanup(self.window.close)
        self.serial=FakeSerial();self.seq=0
        with patch.object(gui.serial,'Serial',return_value=self.serial):self.window.connect_port()
    def feed(self,**values):
        values={'seq':self.seq,'time_s':1+self.seq*.5,'time_ms':1000+self.seq*500,**values};self.seq+=1
        raw=(build_data_line(**values)+'\n').encode();self.serial.pending+=raw;self.window.poll_serial();return raw
    def drain(self):
        for _ in range(40):
            self.window.poll_serial()
            if not self.window.pending and not self.window.queue and not self.serial.in_waiting:return
        self.fail('Command queue did not drain')
    def handshake(self):self.feed();self.drain();self.assertTrue(self.window.protocol_ready)
    def upload(self):self.handshake();self.window.upload_schedule();self.drain();self.assertTrue(self.window.ready)
    def start(self):self.upload();self.window.start_control();self.drain();self.assertTrue(self.window.active)
    def running(self,**overrides):
        values=dict(run_state='RUNNING',control_mode='OPEN',step=0,Ta_C=35,Tb_C=5,period_s=100,
                    setpoint_C=35,phase_rad=0,feedforward_pwm=20,controller_pwm=math.nan,
                    error_C=10,integral_error_C_s=0,compensated_pwm=20,Kp_pwm_per_C=50,Ki_pwm_per_C_s=.3)
        values.update(overrides);return self.feed(**values)
    def rows(self):
        with self.window.csv_path.open() as stream:return list(csv.DictReader(stream))

    def test_preview_never_discovers_opens_or_logs(self):
        with patch.object(gui.list_ports,'comports',side_effect=AssertionError('Discovery')),patch.object(gui.serial,'Serial',side_effect=AssertionError('Open')):
            w=gui.RodAcquisitionWindow(preview=True)
            try:
                w.timer.stop();w.refresh_ports();w.connect_port();self.assertIsNone(w.csv_file);self.assertFalse(w.start.isEnabled())
            finally:w.close()

    def test_module8_output_complete_raw_bytes_and_six_channels(self):
        raw=self.feed(tec_C=26,rod5_C=24)
        self.assertEqual(self.window.csv_path.parent,self.root/'Module_8/data/raw')
        self.assertTrue(self.window.csv_path.name.startswith('module_08_rod_'))
        self.assertFalse((self.root/'Module_7').exists())
        serial_bytes=self.window.csv_path.with_suffix('.serial.log').read_bytes()
        self.assertIn(raw,serial_bytes);self.assertNotIn(b'\r',self.window.csv_path.read_bytes())
        row=next(x for x in self.rows() if x['event']=='measurement')
        for key in ('tec_C','rod1_C','rod2_C','rod3_C','rod4_C','rod5_C'):self.assertTrue(math.isfinite(float(row[key])))

    def test_upload_acknowledgements_do_not_start_and_snapshot_is_saved(self):
        self.upload();self.assertFalse(self.window.active);self.assertNotIn('START',self.serial.commands)
        self.assertTrue(self.serial.commands[-1].startswith('COMMIT '))
        paths=list(self.window.csv_path.parent.glob('*_plan_*.json'));self.assertEqual(len(paths),1)
        document=json.loads(paths[0].read_text());self.assertEqual(document['plan_sha256'],self.window.plan_sha)
        self.assertIn('sensor_map_snapshot',document)

    def test_long_commands_are_paced_without_interleaving_heartbeat(self):
        self.handshake()
        command='STEP 1800.123456 34.1234567 4.1234567 123.456789 PI 123.456789 12.3456789'
        self.window.enqueue([command])
        self.assertTrue(self.window.tx_remaining)
        self.assertNotIn(command,self.serial.commands)
        stamp=time.monotonic()+.4
        with patch.object(gui.time,'monotonic',return_value=stamp):self.window.poll_serial()
        self.assertIn(command,self.serial.commands)
        self.assertFalse(self.window.tx_remaining)
        self.assertLessEqual(max(self.serial.write_sizes),48)

    def test_stop_terminates_a_partial_configuration_command(self):
        self.handshake()
        self.window.enqueue(['STEP 1800.123456 34.1234567 4.1234567 123.456789 PI 123.456789 12.3456789'])
        self.assertTrue(self.window.tx_remaining)
        self.window.stop_control('cancel upload')
        self.assertFalse(self.window.tx_remaining)
        self.assertEqual(self.serial.commands[-1],'STOP')

    def test_explicit_start_and_stop(self):
        self.start();self.running();self.window.stop_control('test stop')
        self.assertFalse(self.window.active);self.assertEqual(self.serial.commands[-1],'STOP')
        self.assertFalse(self.window.start.isEnabled())

    def test_edits_invalidate_uploaded_plan(self):
        self.upload();self.window.table.item(0,3).setText('150')
        self.assertFalse(self.window.ready);self.assertFalse(self.window.start.isEnabled())

    def test_stale_measurement_cannot_start(self):
        self.upload();self.window.last_measurement_at=time.monotonic()-3
        with patch.object(gui.QMessageBox,'warning'):self.window.start_control()
        self.assertNotIn('START',self.serial.commands);self.assertFalse(self.window.active)

    def test_measurement_timeout_requests_stop(self):
        self.start();self.window.last_measurement_at=time.monotonic()-3;self.window.poll_serial()
        self.assertFalse(self.window.active);self.assertIn('STOP',self.serial.commands)

    def test_t1_invalid_and_arduino_clock_reset_stop(self):
        self.start();self.running(rod1_C=math.nan,rod_ok=4)
        self.assertFalse(self.window.active)
        self.assertIn('T1',self.window.statusBar().currentMessage())

    def test_clock_reset_while_running_stops_and_invalidates_plan(self):
        self.start();self.running();self.running(time_s=.1,time_ms=100,seq=0)
        self.assertFalse(self.window.active);self.assertFalse(self.window.ready)
        self.assertIn('reset',self.window.statusBar().currentMessage())

    def test_fault_requires_explicit_reset_and_new_upload(self):
        self.start();self.feed(run_state='FAULT',safety='SHUTDOWN',fault_code='LINK_TIMEOUT')
        self.assertFalse(self.window.active);self.assertFalse(self.window.ready)
        self.window.clear_fault();self.drain()
        self.assertEqual(self.serial.commands[-1],'CLEAR');self.assertFalse(self.window.ready)

    def test_fault_reset_refuses_invalid_boundary(self):
        self.handshake();self.feed(run_state='FAULT',safety='SHUTDOWN',fault_code='BASE_SENSOR',rod1_C=math.nan,rod_ok=4)
        before=len(self.serial.commands)
        with patch.object(gui.QMessageBox,'warning'):self.window.clear_fault()
        self.assertNotIn('CLEAR',self.serial.commands[before:])

    def test_running_data_before_explicit_start_is_stopped(self):
        self.handshake();self.running();self.assertFalse(self.window.active)
        self.assertIn('Unexpected',self.window.statusBar().currentMessage())

    def test_missing_and_malformed_records_are_preserved(self):
        self.handshake();self.seq=10;self.feed();self.assertGreater(self.window.missing,0)
        raw=b'DATA,truncated\r\n';self.serial.pending+=raw;self.window.poll_serial()
        self.assertEqual(self.window.rejected,1)
        self.assertIn(raw,self.window.csv_path.with_suffix('.serial.log').read_bytes())
        self.assertTrue(any(r['event']=='malformed' for r in self.rows()))

    def test_command_ack_timeout_aborts_upload(self):
        self.handshake();self.window.upload_schedule()
        self.window.pending=(self.window.pending[0],time.monotonic()-4)
        self.window.poll_serial();self.assertFalse(self.window.ready);self.assertFalse(self.window.queue)
        self.assertEqual(self.serial.commands[-1],'STOP')

    def test_wrong_firmware_never_enables_start(self):
        self.feed();self.serial.pending=b'#ACK,HELLO,other_firmware\n';self.window.poll_serial()
        self.assertFalse(self.window.protocol_ready);self.assertFalse(self.window.start.isEnabled())

    def test_done_and_fault_events_remain_in_log(self):
        self.start();self.serial.pending+=b'#EVENT,DONE,2000\n';self.window.poll_serial()
        self.assertFalse(self.window.active)
        self.assertTrue(any('DONE' in r['note'] for r in self.rows()))

    def test_csv_failure_stops_output(self):
        self.start();self.window.csv_writer=Mock();self.window.csv_writer.writerow.side_effect=OSError('disk full')
        self.running();self.assertFalse(self.window.active);self.assertTrue(self.window.logging_failed)
        self.assertFalse(self.window.start.isEnabled())

    def test_reconnect_preserves_old_files(self):
        self.feed();old=self.window.csv_path;self.window.disconnect_port();before=old.read_bytes()
        self.serial=FakeSerial()
        with patch.object(gui.serial,'Serial',return_value=self.serial):self.window.connect_port()
        self.feed();self.assertNotEqual(old,self.window.csv_path);self.assertEqual(old.read_bytes(),before)

    def test_two_linked_plots_and_whole_run_view(self):
        self.feed();self.feed();self.window.redraw();self.assertEqual(len(self.window.plots),2)
        self.assertEqual(len(self.window.curves),7)
        self.window.plots[0].setXRange(1,1.5,padding=0)
        self.assertFalse(self.window.whole_run.isChecked())
        self.window.fit_whole_run();self.assertTrue(self.window.whole_run.isChecked())

if __name__=='__main__':unittest.main()
