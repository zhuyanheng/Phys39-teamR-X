"""Six-channel rod acquisition GUI with the Module 6 P/PI control path.

Copied from Module_6/python/pi_tec_control_gui.py. The control path, safety
gates, and setpoint-step handling are unchanged, so Module 6 stays a verified
checkpoint. Three things are added:

    * five measurement-only rod channels (A1..A5) next to the TEC channel,
    * the DATA, serial format from rod_protocol.py,
    * one CSV column per channel plus a rod_ok counter.

The TEC channel remains the only PI feedback and the only safety input; an
unusable rod channel is displayed and logged but never stops the actuator,
because a loose rod probe must not abort a long steady-state run.

Use Module_7/run_rod_acquisition.command. --preview never opens a serial port.
"""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
if __name__ == "__main__":
    env = ROOT / ".venv"
    executable = env / "bin/python"
    if executable.is_file() and Path(sys.prefix) != env:
        os.execv(str(executable), [str(executable), *sys.argv])

import argparse
import csv
from datetime import datetime
import math
import time
import pyqtgraph as pg
import serial
from serial.tools import list_ports
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QGridLayout, QGroupBox, QLabel, QPushButton, QComboBox, QDoubleSpinBox,
    QSpinBox, QCheckBox, QLineEdit, QMessageBox)

# Reuse the tested Module 6 arithmetic instead of copying the controller.
sys.path.insert(0, str(ROOT / "Module_6/python"))
from pi_controller import PIController

# The serial format lives in a Qt-free module so it can be unit tested.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rod_protocol import (FIELD_NAMES, DIAGNOSTIC_PREFIX, ROD_CHANNELS,
                          parse_data_line)

# Columns 4..17 are the DATA-line fields in DATA-line order (they are generated
# from the protocol, so a channel can never be dropped by hand-editing a list).
# heat_pwm/cool_pwm are the firmware's own report of its outputs, not a
# measurement of the pins. The control columns follow so that one CSV row still
# explains the actuator command.
FIELDS = (["host_time", "event", "run_id"] + list(FIELD_NAMES)
    + ["control_active", "mode", "setpoint_C",
       "Kp_pwm_per_C", "Ki_pwm_per_C_s", "pwm_limit", "anti_windup", "dt_s",
       "error_C", "integral_error_C_s", "p_term_pwm", "i_term_pwm",
       "requested_signed_pwm", "clamped_signed_pwm", "sent_signed_pwm",
       "reported_signed_pwm", "saturated", "integration_blocked",
       "backlog_sample", "note"])


# Plot window. The rod takes tens of minutes to settle, so the default window is
# far longer than Module 6's 180 s; "Show whole run" keeps everything, capped by
# HISTORY_LIMIT (50000 rows is 6.9 h at the 500 ms report period and keeps every
# redraw cheap enough to stay responsive).
WINDOW_S = 900
HISTORY_LIMIT = 50000

# Fixed colours per channel (index 0 = TEC base, 1..5 = rod 1..5) so that a
# temperature trace keeps the same colour across runs and figures.
CHANNEL_PENS = ["#111111", "#245a81", "#2f7d4f", "#927919", "#b45b22", "#693f85"]


class RodAcquisitionWindow(QMainWindow):
    def __init__(self, preview=False):
        super().__init__()
        self.preview = preview
        self.serial_port = None
        self.csv_file = None
        self.csv_writer = None
        self.buffer = ""
        self.active = False
        self.controller = None
        self.last_measurement_at = None
        self.latest = None
        self.run_id = 0
        self.history = []
        self.last_result = None
        self.last_sent = 0
        self.accepted = 0
        self.rejected = 0
        self.csv_path = None
        self.setWindowTitle("Module 7 Six-Channel Rod Acquisition"
                            + (" — OFFLINE PREVIEW" if preview else ""))
        self.resize(1180, 1000)
        layout = QVBoxLayout()
        body = QWidget();body.setLayout(layout);self.setCentralWidget(body)
        banner = QLabel("OFFLINE PREVIEW — no serial connection, no experimental data saved" if preview
                        else "Physical rod instrument — instructor review before actuator power")
        banner.setStyleSheet("font-weight:bold; color:#a34d14")
        layout.addWidget(banner)
        connection = QGroupBox("Arduino connection");grid = QGridLayout(connection)
        self.port = QComboBox();self.port.setEditable(True)
        self.refresh = QPushButton("Refresh ports");self.refresh.clicked.connect(self.refresh_ports)
        self.connect_button = QPushButton("Connect (PWM 0)");self.connect_button.clicked.connect(self.connect_port)
        self.disconnect_button = QPushButton("Disconnect / PWM 0");self.disconnect_button.clicked.connect(self.disconnect_port)
        grid.addWidget(self.port,0,0);grid.addWidget(self.refresh,0,1)
        grid.addWidget(self.connect_button,0,2);grid.addWidget(self.disconnect_button,0,3)
        layout.addWidget(connection)
        controls = QGroupBox("P / PI settings");grid=QGridLayout(controls)
        self.mode = QComboBox();self.mode.addItems(["P","PI"])
        self.target=self.number(10,45,30,4)
        self.kp=self.number(0,1000,2,5)
        self.ki=self.number(0,100,0.01,6)
        self.limit=QSpinBox();self.limit.setRange(1,255);self.limit.setValue(255)
        self.anti=QCheckBox("Conditional integration anti-windup");self.anti.setChecked(True)
        for i,(label,widget) in enumerate([("Mode",self.mode),("Setpoint (C)",self.target),
                ("Kp (PWM/C)",self.kp),("Ki (PWM/(C s))",self.ki),("PWM limit",self.limit)]):
            grid.addWidget(QLabel(label),0,i);grid.addWidget(widget,1,i)
        self.start=QPushButton("Start P / PI");self.start.clicked.connect(self.start_control)
        self.stop=QPushButton("STOP — PWM 0");self.stop.clicked.connect(lambda:self.stop_control("Operator stop"))
        self.stop.setStyleSheet("font-weight:bold; background:#b22222; color:white")
        self.reset=QPushButton("Zero integral + STOP");self.reset.clicked.connect(self.zero_integral)
        self.apply=QPushButton("Apply setpoint step");self.apply.clicked.connect(self.apply_setpoint)
        self.mark_note=QLineEdit();self.mark_note.setPlaceholderText(
            "Note for the log (e.g. steady reached, probe moved, calibration start)")
        self.mark=QPushButton("Mark event");self.mark.clicked.connect(self.mark_event)
        self.whole_run=QCheckBox("Show whole run");self.whole_run.setChecked(False)
        grid.addWidget(self.anti,2,0,1,3);grid.addWidget(self.whole_run,2,3,1,2)
        grid.addWidget(self.start,3,0);grid.addWidget(self.apply,3,1)
        grid.addWidget(self.reset,3,2);grid.addWidget(self.stop,3,3,1,2)
        grid.addWidget(self.mark_note,4,0,1,3);grid.addWidget(self.mark,4,3,1,2)
        layout.addWidget(controls)
        self.readout=QLabel("Waiting for Arduino measurements. Output is disabled.")
        self.readout.setWordWrap(True);layout.addWidget(self.readout)
        pg.setConfigOptions(antialias=True,foreground='#222222')
        self.plots=[];self.curves={}
        channel_series=[("tec_C","TEC base",CHANNEL_PENS[0],3)]
        channel_series+=[(f"{channel}_C",f"rod {index}",CHANNEL_PENS[index],2)
                         for index,channel in enumerate(ROD_CHANNELS,start=1)]
        channel_series.append(("setpoint_C","Setpoint",'#c0392b',2))
        for title,unit,series in [
            ("Temperature: TEC base, rod 1-5 and setpoint","C",channel_series),
            ("Signed PWM: reported, requested and sent","PWM",[("reported_signed_pwm","Firmware applied",'#222222',2),("requested_signed_pwm","Next requested",'#999999',2),("sent_signed_pwm","Next sent",'#b45b22',2)]),
            ("Proportional and integral contributions","PWM",[("p_term_pwm","P term",'#245a81',2),("i_term_pwm","I term",'#b45b22',2)]),
            ("Setpoint minus measured TEC temperature","C",[("error_C","Error",'#693f85',2)])]:
            plot=pg.PlotWidget(title=title);plot.setBackground('w')
            plot.addLegend(colCount=min(4,len(series)),offset=(10,0),labelTextColor='#222222')
            plot.showGrid(x=True,y=True,alpha=.2);plot.setLabel('left',unit);plot.setLabel('bottom','Arduino time',units='s')
            for key,label,color,width in series:
                pen=pg.mkPen(color,width=width,style=pg.QtCore.Qt.DashLine if key=='setpoint_C' else pg.QtCore.Qt.SolidLine)
                self.curves[key]=plot.plot([],[],pen=pen,name=label)
            self.plots.append(plot);layout.addWidget(plot)
        self.refresh_ports()
        self.timer=QTimer(self);self.timer.timeout.connect(self.poll_serial);self.timer.start(100)
        self.mode.currentTextChanged.connect(self.change_mode)
        self.change_mode()
        self.connect_button.setEnabled(not preview)
        self.statusBar().showMessage("Disconnected — no actuator commands")

    def number(self,minimum,maximum,value,decimals):
        box=QDoubleSpinBox();box.setDecimals(decimals);box.setRange(minimum,maximum);box.setValue(value)
        return box

    def refresh_ports(self):
        old=self.port.currentText()
        devices=[p.device for p in list_ports.comports()]
        self.port.clear();self.port.addItems(devices)
        if old and old in devices:self.port.setCurrentText(old)
        else:
            preferred=next((p for p in devices if 'usbmodem' in p.lower() or 'usbserial' in p.lower()),None)
            if preferred:self.port.setCurrentText(preferred)

    def log(self,event="measurement",**data):
        if self.csv_writer is None:return
        row=dict(host_time=datetime.now().astimezone().isoformat(),event=event,run_id=self.run_id,
                 control_active=int(self.active),mode=self.mode.currentText(),pwm_limit=self.limit.value(),
                 anti_windup=int(self.anti.isChecked()))
        if self.controller:
            row.update(setpoint_C=self.controller.setpoint,Kp_pwm_per_C=self.controller.kp,
                       Ki_pwm_per_C_s=self.controller.ki if self.controller.mode=="PI" else 0.)
        row.update(data)
        try:
            self.csv_writer.writerow(row);self.csv_file.flush()
        except (OSError,ValueError) as exc:
            # Disable logging before stopping so a failed log cannot recurse.
            self.csv_writer=None
            self.stop_control(f"CSV logging failed: {exc}")

    def open_log(self):
        # Raw data only. Corrected values and calibration coefficients live in
        # other folders so that a measured number is never overwritten.
        folder=ROOT/'Module_7/data/raw';folder.mkdir(parents=True,exist_ok=True)
        self.csv_path=folder/f"module_07_rod_{datetime.now():%Y%m%d_%H%M%S_%f}.csv"
        self.csv_file=self.csv_path.open('x',newline='',encoding='utf-8')
        self.csv_writer=csv.DictWriter(self.csv_file,fieldnames=FIELDS)
        self.csv_writer.writeheader();self.csv_file.flush()

    def connect_port(self):
        if self.preview or self.serial_port is not None:return
        try:
            self.serial_port=serial.Serial(self.port.currentText(),9600,timeout=0,write_timeout=.25)
            self.open_log();self.send(0)
        except (serial.SerialException,OSError) as exc:
            self.disconnect_port();QMessageBox.warning(self,"Connection failed",str(exc));return
        self.buffer="";self.latest=None;self.last_measurement_at=None
        self.connect_button.setEnabled(False);self.port.setEnabled(False)
        self.start.setEnabled(True)
        self.statusBar().showMessage(f"Connected; wait for a fresh Safety: OK line. CSV: {self.csv_path}")
        self.log("connect",note="Connected with zero output; control remains OFF")

    def send(self,signed_pwm):
        if self.serial_port is None or not self.serial_port.is_open:
            raise serial.SerialException("Arduino is not connected")
        signed=int(signed_pwm)
        if abs(signed)>self.limit.value():raise ValueError("Output exceeds configured PWM limit")
        command=f"SET PWM {abs(signed)} DIR {'HEAT' if signed>0 else 'COOL'}\n".encode()
        if self.serial_port.write(command)!=len(command):raise serial.SerialException("Incomplete serial write")
        self.last_sent=signed

    def stop_control(self,reason):
        self.active=False
        if self.controller:self.controller.reset()
        self.last_result=None
        if self.serial_port is not None and self.serial_port.is_open:
            try:self.send(0)
            except (serial.SerialException,OSError) as exc:reason+=f"; ZERO SEND FAILED: {exc}"
        for widget in (self.kp,self.ki,self.limit,self.anti,self.mode):widget.setEnabled(True)
        self.ki.setEnabled(self.mode.currentText()=="PI")
        connected=self.serial_port is not None and self.serial_port.is_open
        self.start.setEnabled(not self.preview and connected);self.apply.setEnabled(False)
        self.statusBar().showMessage(reason+" — control OFF; PWM 0 requested")
        self.log("stop",note=reason,sent_signed_pwm=self.last_sent)

    def zero_integral(self):
        self.stop_control("Integral reset")
        self.readout.setText("Integral cleared. Output zero requested. Start again when ready.")

    def change_mode(self,*_):
        self.stop_control("Mode selected")

    def fresh_safe(self,require_zero=True):
        if self.serial_port is None or not self.serial_port.is_open:
            raise ValueError("Serial port is not open. Select the Arduino USB port above, "
                             "then click Connect (PWM 0) before Start P / PI.")
        if self.latest is None or self.last_measurement_at is None or time.monotonic()-self.last_measurement_at>2:
            raise ValueError("Wait for a fresh Arduino measurement")
        _t,tec,pwm,_direction,safety,*_=self.latest
        if not math.isfinite(tec) or not 10<=tec<=45 or safety!="OK":
            raise ValueError("Need a plausible 10-45 C TEC reading and Safety: OK")
        if require_zero and pwm != 0:
            raise ValueError("Wait for firmware-reported PWM 0")

    def start_control(self):
        if self.active:return
        try:
            self.fresh_safe()
            self.send(0)
            self.controller=PIController(self.mode.currentText(),self.target.value(),self.kp.value(),
                                         self.ki.value(),self.limit.value(),self.anti.isChecked())
        except (ValueError,serial.SerialException) as exc:
            self.stop_control(str(exc));QMessageBox.warning(self,"Cannot start",str(exc));return
        self.run_id+=1;self.active=True;self.last_result=None
        for widget in (self.kp,self.ki,self.limit,self.anti,self.mode):widget.setEnabled(False)
        self.start.setEnabled(False);self.apply.setEnabled(True)
        self.log("start",note="Integral zero; first accepted sample uses dt=0")
        self.statusBar().showMessage(f"{self.controller.mode} active; gains locked. Apply setpoint for up/down steps.")

    def apply_setpoint(self):
        if not self.active:return
        try:self.fresh_safe(require_zero=False)
        except ValueError as exc:self.stop_control(str(exc));return
        self.controller.setpoint=self.target.value()
        self.log("setpoint_step",note="Integral retained for a within-run setpoint step")
        self.statusBar().showMessage(f"Applied target {self.controller.setpoint:g} C; integral retained")

    def mark_event(self):
        note=self.mark_note.text().strip() or "manual mark"
        if self.csv_writer is None:
            self.statusBar().showMessage("Not connected: the note was not logged")
            return
        self.log("operator_mark",note=note)
        self.mark_note.clear()
        self.statusBar().showMessage(f"Logged operator_mark: {note}")

    def poll_serial(self):
        if self.active and (self.last_measurement_at is None or time.monotonic()-self.last_measurement_at>2):
            self.stop_control("Measurement timeout")
        if self.serial_port is None:return
        try:
            count=self.serial_port.in_waiting
            if not count:return
            self.buffer+=self.serial_port.read(count).decode('utf-8',errors='replace')
            if len(self.buffer)>65536:raise ValueError("Oversized/incomplete serial report")
            complete=self.buffer.split('\n');self.buffer=complete.pop()
            samples=[]
            for line in complete:
                sample=parse_data_line(line)
                if sample is None:
                    # Startup banner and header lines start with # and are not
                    # errors; anything else that fails to parse is counted.
                    if line.strip() and not line.strip().startswith(DIAGNOSTIC_PREFIX):
                        self.rejected+=1
                    continue
                self.accepted+=1
                samples.append(sample)
            for i,sample in enumerate(samples):
                self.process_measurement(sample,backlog=i<len(samples)-1)
        except (serial.SerialException,OSError) as exc:self.connection_fault(exc)
        except ValueError as exc:self.stop_control(str(exc))

    def connection_fault(self,error):
        self.stop_control(f"Serial error: {error}")
        if self.serial_port is not None:
            try:self.serial_port.close()
            except (serial.SerialException,OSError):pass
        self.serial_port=None;self.latest=None;self.last_measurement_at=None
        self.start.setEnabled(False)
        if self.csv_file:
            try:self.csv_file.close()
            except (OSError,ValueError):pass
        self.csv_file=None;self.csv_writer=None
        self.connect_button.setEnabled(not self.preview);self.port.setEnabled(True)
        self.statusBar().showMessage(f"Serial disconnected: {error}. Zero output could not be confirmed.")

    def process_measurement(self,sample,backlog=False):
        previous=self.latest
        problem=sample.issue()
        valid=problem is None
        advancing=previous is None or sample.time_s>previous[0]
        if self.active and (not valid or not advancing):
            self.stop_control(f"Unsafe report ({problem or 'Arduino time reset/duplicate'})")
        if valid and advancing and not backlog:
            self.latest=(sample.time_s,sample.tec_c,sample.pwm,sample.heat_cool,sample.safety,
                         sample.heat_pwm,sample.cool_pwm,sample.limit_c)
            self.last_measurement_at=time.monotonic()
        elif not valid or not advancing:
            self.latest=None;self.last_measurement_at=None
        result=None
        if self.active and not backlog:
            try:result=self.controller.step(sample.time_s,sample.tec_c);self.send(result.sent_pwm)
            except (serial.SerialException,OSError) as exc:
                self.connection_fault(exc);result=None
            except ValueError as exc:self.stop_control(str(exc));result=None
        row=dict(zip(FIELD_NAMES,sample.measurement))
        row.update(reported_signed_pwm=sample.signed_pwm,backlog_sample=int(backlog))
        if self.controller:row['setpoint_C']=self.controller.setpoint
        if result:
            row.update(dt_s=result.dt_s,error_C=result.error_c,integral_error_C_s=result.integral_c_s,
                p_term_pwm=result.p_pwm,i_term_pwm=result.i_pwm,requested_signed_pwm=result.requested_pwm,
                clamped_signed_pwm=result.clamped_pwm,sent_signed_pwm=result.sent_pwm,
                saturated=int(result.saturated),integration_blocked=int(result.integration_blocked))
            self.last_result=result
        else:row['sent_signed_pwm']=self.last_sent
        self.log(**row)
        if not self.active:result=None
        if math.isfinite(sample.time_s):
            if self.history and sample.time_s<=self.history[-1]['time_s']:self.history=[]
            self.history.append(row)
            if self.whole_run.isChecked():
                if len(self.history)>HISTORY_LIMIT:self.history=self.history[-HISTORY_LIMIT:]
            else:
                cutoff=sample.time_s-WINDOW_S
                self.history=[r for r in self.history if r['time_s']>=cutoff]
            for key,curve in self.curves.items():
                curve.setData([r['time_s'] for r in self.history],[r.get(key,math.nan) for r in self.history])
        rods=" ".join(f"{value:.2f}" if math.isfinite(value) else "nan" for value in sample.rods_c)
        self.readout.setText(
            f"TEC={sample.tec_c:.2f} C | rods={rods} C | valid {sample.rod_ok}/{len(ROD_CHANNELS)} | "
            f"Arduino t={sample.time_s:.1f} s | PWM={sample.signed_pwm:+d} | Safety={sample.safety} | "
            f"rows ok/bad={self.accepted}/{self.rejected}"+
            (f"\nError={result.error_c:+.4f} C | dt={result.dt_s:.3f} s | q={result.integral_c_s:.4f} C s | "
             f"P={result.p_pwm:+.3f}, I={result.i_pwm:+.3f}, requested={result.requested_pwm:+.3f}, "
             f"next sent={result.sent_pwm:+d} | AW blocked={result.integration_blocked}" if result
             else "\nControl OFF or historical backlog sample"))

    def disconnect_port(self):
        self.stop_control("Disconnected")
        if self.serial_port is not None:
            self.serial_port.close();self.serial_port=None
        self.log("disconnect",note="Serial closed")
        if self.csv_file:
            try:self.csv_file.close()
            except (OSError,ValueError):pass
        self.csv_file=None;self.csv_writer=None;self.latest=None;self.last_measurement_at=None
        self.start.setEnabled(False)
        self.connect_button.setEnabled(not self.preview);self.port.setEnabled(True)

    def closeEvent(self,event):
        self.timer.stop();self.disconnect_port();event.accept()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview',action='store_true',help='Open disconnected GUI; never access Arduino')
    args=parser.parse_args()
    app=QApplication(sys.argv);window=RodAcquisitionWindow(args.preview);window.show();return app.exec()


if __name__=='__main__':sys.exit(main())
