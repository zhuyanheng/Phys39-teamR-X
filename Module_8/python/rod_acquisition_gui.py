"""Module 8 six-channel GUI. Arduino owns all real-time control.

--preview never discovers/opens a serial port or creates acquisition files.
A plan is uploaded while output is off; starting it is a separate action.
"""
from pathlib import Path
import os
import sys
ROOT = Path(__file__).resolve().parents[2]
if __name__ == '__main__':
    env = ROOT / '.venv'
    executable = env / 'bin/python'
    if executable.is_file() and Path(sys.prefix) != env:
        os.execv(str(executable), [str(executable), *sys.argv])

import argparse
import csv
from datetime import datetime
import hashlib
import json
import math
import time
from collections import deque
import serial
from serial.tools import list_ports
import pyqtgraph as pg
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QGridLayout, QGroupBox, QLabel, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox,
    QCheckBox, QLineEdit, QMessageBox, QSplitter, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QHBoxLayout)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from angstrom_plan import Plan, Step, preset, reference_calibration, FIRMWARE_ID, BAUD
from rod_protocol import FIELD_NAMES, ROD_CHANNELS, parse_data_line

FIELDS = ['host_time','event','run_id'] + list(FIELD_NAMES) + [
    'control_active','mode','backlog_sample','note','plan_sha256']
TABLE_FIELDS = ('duration_s','Ta_C','Tb_C','period_s','mode','Kp','Ki')
CHANNEL_PENS = ['#111111','#245a81','#2f7d4f','#927919','#b45b22','#693f85']
HISTORY_LIMIT, X_MIN_SPAN = 50000, 60.

class RodAcquisitionWindow(QMainWindow):
    def __init__(self, preview=False):
        super().__init__()
        self.preview=preview
        self.serial_port=self.csv_file=self.csv_writer=self.raw_file=None
        self.csv_path=None
        self.buffer=''
        self.active=self.ready=self.protocol_ready=False
        self.firmware_rejected=False
        self.logging_failed=False
        self.pending=None
        self.queue=deque()
        self.tx_remaining=b''
        self.last_tx=0
        self.last_measurement_at=self.connected_at=None
        self.last_ping=0
        self.latest=None
        self.last_seq=None
        self.accepted=self.rejected=self.missing=self.run_id=self.snapshot_id=0
        self.history=[]
        self.upload_plan=None
        self.plan_sha=''
        self._loading=self._fitting_x=False
        self.setWindowTitle('Module 8 — Angstrom six-channel acquisition'+(' — OFFLINE PREVIEW' if preview else ''))
        self.resize(1460,920); self.setMinimumSize(1100,700)
        body=QWidget(); self.setCentralWidget(body); layout=QVBoxLayout(body)
        banner=QLabel('OFFLINE PREVIEW — no serial access; no experimental files' if preview
            else 'Arduino-timed sinusoid and schedule · T1 is the measured rod boundary · 10–45 C operating range')
        banner.setWordWrap(True); banner.setStyleSheet('font-weight:bold; color:#93430f')
        layout.addWidget(banner)
        self.main_splitter=QSplitter(Qt.Horizontal); layout.addWidget(self.main_splitter,1)
        panel=QWidget(); panel.setMinimumWidth(450); panel.setMaximumWidth(610)
        panel_layout=QVBoxLayout(panel); panel_layout.setContentsMargins(0,0,0,0)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        controls=QWidget(); left=QVBoxLayout(controls); left.setContentsMargins(0,0,8,0)
        scroll.setWidget(controls); panel_layout.addWidget(scroll,1)
        self.main_splitter.addWidget(panel)
        self.plot_splitter=QSplitter(Qt.Vertical); self.main_splitter.addWidget(self.plot_splitter)
        self.main_splitter.setStretchFactor(0,0); self.main_splitter.setStretchFactor(1,1)
        self.main_splitter.setSizes([500,940])
        connection=QGroupBox('Arduino connection'); grid=QGridLayout(connection)
        self.port=QComboBox(); self.port.setEditable(True)
        refresh=QPushButton('Refresh ports'); refresh.clicked.connect(self.refresh_ports)
        self.connect_button=QPushButton('Connect (output off)'); self.connect_button.clicked.connect(self.connect_port)
        self.disconnect_button=QPushButton('Disconnect / STOP'); self.disconnect_button.clicked.connect(self.disconnect_port)
        grid.addWidget(self.port,0,0,1,2); grid.addWidget(refresh,1,0); grid.addWidget(self.connect_button,1,1)
        grid.addWidget(self.disconnect_button,2,0,1,2); left.addWidget(connection)

        group=QGroupBox('Waveform and frequency schedule'); gl=QVBoxLayout(group)
        self.preset_combo=QComboBox(); self.preset_combo.addItems(['Comparison: OPEN / P / PI + second period','Single trial / fixed target','Short schedule rehearsal (not production)'])
        use=QPushButton('Use preset'); use.clicked.connect(self.use_preset)
        row=QHBoxLayout(); row.addWidget(self.preset_combo,1); row.addWidget(use); gl.addLayout(row)
        self.table=QTableWidget(0,len(TABLE_FIELDS)); self.table.setHorizontalHeaderLabels(['Time s','Mean C','Amp C','Period s','Mode','Kp','Ki'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMinimumHeight(180); gl.addWidget(self.table)
        self.table.cellChanged.connect(self.invalidate)
        self.add_button=QPushButton('Add step'); self.add_button.clicked.connect(self.add_step)
        self.remove_button=QPushButton('Remove step'); self.remove_button.clicked.connect(self.remove_step)
        row=QHBoxLayout(); row.addWidget(self.add_button); row.addWidget(self.remove_button); gl.addLayout(row)
        hint=QLabel('Modes: OPEN / P / PI. Amplitude 0 holds a fixed target. Period >= 100 s.\nDuration includes settling AND at least five retained cycles; choose it from pilot evidence.')
        hint.setWordWrap(True); gl.addWidget(hint); left.addWidget(group)
        self.schedule_group=group

        group=QGroupBox('Controller and measured calibration'); grid=QGridLayout(group)
        self.ratio=QDoubleSpinBox(); self.ratio.setRange(.001,20); self.ratio.setDecimals(6)
        self.limit=QSpinBox(); self.limit.setRange(1,255)
        self.anti=QCheckBox('Anti-windup (includes cooling compensation)')
        grid.addWidget(QLabel('Heating / cooling ratio'),0,0); grid.addWidget(self.ratio,0,1)
        grid.addWidget(QLabel('Applied PWM limit'),1,0); grid.addWidget(self.limit,1,1)
        grid.addWidget(self.anti,2,0,1,2)
        cal=QPushButton('Load measured calibration CSV'); cal.clicked.connect(self.load_calibration)
        self.cal_label=QLabel(); self.cal_label.setWordWrap(True)
        grid.addWidget(cal,3,0,1,2); grid.addWidget(self.cal_label,4,0,1,2); left.addWidget(group)
        self.controller_group=group
        self.ratio.valueChanged.connect(self.invalidate); self.limit.valueChanged.connect(self.invalidate); self.anti.toggled.connect(self.invalidate)

        group=QGroupBox('Run metadata'); grid=QGridLayout(group)
        self.ambient=QLineEdit(); self.ambient.setPlaceholderText('Unknown: leave blank')
        self.ambient_method=QLineEdit(); self.ambient_method.setPlaceholderText('Measured / estimated, instrument or method')
        self.settling=QLineEdit(); self.settling.setPlaceholderText('Numerical repeat-cycle acceptance criterion')
        for i,(label,widget) in enumerate([('Room temperature C',self.ambient),('Ambient method',self.ambient_method),('Settling criterion',self.settling)]):
            grid.addWidget(QLabel(label),i,0); grid.addWidget(widget,i,1); widget.textChanged.connect(self.invalidate)
        self.metadata_group=group; left.addWidget(group)
        row=QHBoxLayout(); load=QPushButton('Load plan'); save=QPushButton('Save plan')
        load.clicked.connect(self.load_plan); save.clicked.connect(self.save_plan); row.addWidget(load); row.addWidget(save)
        gl.addLayout(row)  # Plan files are editable local configuration, not measured data.
        self.load_plan_button=load
        self.upload=QPushButton('1. Upload plan (output stays OFF)'); self.upload.clicked.connect(self.upload_schedule)
        self.start=QPushButton('2. Start schedule'); self.start.clicked.connect(self.start_control)
        left.addWidget(self.upload); left.addWidget(self.start)
        self.reset_fault=QPushButton("Reset latched fault (output OFF)")
        self.reset_fault.clicked.connect(self.clear_fault); left.addWidget(self.reset_fault)
        chart=QGroupBox('Chart and event notes'); cl=QVBoxLayout(chart)
        row=QHBoxLayout(); self.whole_run=QCheckBox('Show whole run'); self.whole_run.setChecked(True)
        fit=QPushButton('Fit x'); fit.clicked.connect(self.fit_whole_run); row.addWidget(self.whole_run); row.addWidget(fit); cl.addLayout(row)
        self.mark_note=QLineEdit(); self.mark_note.setPlaceholderText('Run observation or event')
        mark=QPushButton('Mark event'); mark.clicked.connect(self.mark_event)
        cl.addWidget(self.mark_note); cl.addWidget(mark); left.addWidget(chart)
        self.readout=QLabel('Waiting for Arduino. Output is disabled.'); self.readout.setWordWrap(True); left.addWidget(self.readout)
        left.addStretch(1)
        self.stop=QPushButton('STOP — both PWM outputs zero'); self.stop.clicked.connect(lambda:self.stop_control('Operator stop'))
        self.stop.setStyleSheet('font-weight:bold; background:#b22222; color:white'); self.stop.setMinimumHeight(44); panel_layout.addWidget(self.stop)
        pg.setConfigOptions(antialias=True,foreground='#222222')
        self.plots=[]; self.curves={}
        series=[('TEC temperature and requested waveform',[('tec_C','A0: measured TEC',CHANNEL_PENS[0]),('setpoint_C','Requested setpoint','#c0392b')]),
                ('Rod temperatures — remeasure Module 8 positions',[(f'{c}_C',f'A{i} / T{i}',CHANNEL_PENS[i]) for i,c in enumerate(ROD_CHANNELS,1)])]
        for i,(title,channels) in enumerate(series):
            plot=pg.PlotWidget(title=title); plot.setBackground('w'); plot.addLegend(colCount=3,offset=(10,0))
            plot.showGrid(x=True,y=True,alpha=.2); plot.setLabel('left','Temperature',units='C'); plot.setLabel('bottom','Arduino time',units='s')
            plot.getViewBox().setDefaultPadding(.05); plot.getViewBox().setAutoVisible(y=True)
            for key,label,color in channels:
                pen=pg.mkPen(color,width=2,style=Qt.DashLine if key=='setpoint_C' else Qt.SolidLine)
                curve=plot.plot([],[],pen=pen,name=label); curve.setClipToView(True); curve.setDownsampling(auto=True,method='peak'); self.curves[key]=curve
            if self.plots: plot.setXLink(self.plots[0])
            self.plots.append(plot); self.plot_splitter.addWidget(plot)
        self.plot_splitter.setSizes([330,500])
        self.plots[0].getViewBox().sigXRangeChanged.connect(self.x_range_changed)
        self.whole_run.toggled.connect(lambda checked: checked and self.show_whole_run())
        self.populate(preset())
        self.refresh_ports()
        self.timer=QTimer(self); self.timer.timeout.connect(self.poll_serial); self.timer.start(100)
        self.update_enabled(); self.statusBar().showMessage('Disconnected — no actuator commands')

    def populate(self,plan):
        self._loading=True
        try:
            self.table.setRowCount(len(plan.steps))
            for row,step in enumerate(plan.steps):
                for col,key in enumerate(TABLE_FIELDS):
                    value=getattr(step,key)
                    self.table.setItem(row,col,QTableWidgetItem(value if isinstance(value,str) else f'{value:g}'))
            self.ratio.setValue(plan.ratio); self.limit.setValue(plan.pwm_limit); self.anti.setChecked(plan.anti_windup)
            self.calibration=list(plan.calibration); self.metadata=json.loads(json.dumps(plan.metadata))
            self.cal_label.setText(f'{len(self.calibration)} measured lookup points · '+self.metadata.get('calibration',{}).get('source','plan file')+'\nStatic calibration is provisional; no extrapolation.')
            self.ambient.setText('' if self.metadata.get('ambient_C') is None else str(self.metadata['ambient_C']))
            self.ambient_method.setText(self.metadata.get('ambient_method',''))
            self.settling.setText(self.metadata.get('settling_criterion',''))
        finally: self._loading=False
        self.invalidate()

    def get_plan(self):
        steps=[]
        for row in range(self.table.rowCount()):
            values=[]
            for col,key in enumerate(TABLE_FIELDS):
                item=self.table.item(row,col)
                if item is None: raise ValueError(f'Step {row+1}: missing {key}')
                text=item.text().strip()
                values.append(text.upper() if key=='mode' else float(text))
            steps.append(Step(*values))
        metadata=json.loads(json.dumps(self.metadata))
        ambient=self.ambient.text().strip()
        metadata.update(ambient_C=float(ambient) if ambient else None,
                        ambient_method=self.ambient_method.text().strip(),settling_criterion=self.settling.text().strip())
        if ambient and not math.isfinite(metadata['ambient_C']): raise ValueError('Ambient must be finite or blank')
        return Plan(steps,self.ratio.value(),self.limit.value(),self.anti.isChecked(),list(self.calibration),metadata).validate()

    def invalidate(self,*_):
        if self._loading:return
        self.ready=False
        self.update_enabled()

    def use_preset(self):
        self.populate(preset(('comparison','single','rehearsal')[self.preset_combo.currentIndex()]))

    def add_step(self):
        if self.table.rowCount()>=12:return
        row=self.table.rowCount(); self.table.insertRow(row)
        for col,value in enumerate(('1800','35','5','150','PI','50','0.3')):
            self.table.setItem(row,col,QTableWidgetItem(value))
        self.invalidate()

    def remove_step(self):
        if self.table.rowCount()>1:self.table.removeRow(max(0,self.table.currentRow())); self.invalidate()

    def load_calibration(self):
        path,_=QFileDialog.getOpenFileName(self,'Measured static calibration',str(ROOT/'Module_8/data/reference'),'CSV (*.csv)')
        if not path:return
        try:self.calibration,source=reference_calibration(path)
        except (ValueError,OSError,KeyError) as e:self.warn('Invalid calibration',e);return
        self.metadata['calibration']=source
        if 'heating_to_cooling_ratio' in source:
            self.ratio.setValue(source['heating_to_cooling_ratio'])
        self.cal_label.setText(f'{len(self.calibration)} measured points · {source["source"]} · no extrapolation'
            + ('\nHeat/cool ratio recalculated from the two measured slopes.'
               if 'heating_to_cooling_ratio' in source else '\nCooling branch missing: enter the measured heat/cool ratio separately.'))
        self.invalidate()

    def load_plan(self):
        path,_=QFileDialog.getOpenFileName(self,'Load plan',str(ROOT/'Module_8/config'),'JSON (*.json)')
        if not path:return
        try:self.populate(Plan.load(path))
        except (OSError,ValueError,TypeError,KeyError) as e:self.warn('Cannot load plan',e)

    def save_plan(self):
        try:plan=self.get_plan()
        except (ValueError,TypeError) as e:self.warn('Invalid plan',e);return
        path,_=QFileDialog.getSaveFileName(self,'Save plan',str(ROOT/'Module_8/config/experiment_plan.json'),'JSON (*.json)')
        if path:
            try:plan.save(path)
            except OSError as e:self.warn('Cannot save plan',e)

    def warn(self,title,error):
        self.statusBar().showMessage(str(error)); QMessageBox.warning(self,title,str(error))

    def update_enabled(self):
        connected=self.serial_port is not None and self.serial_port.is_open
        busy=self.active or bool(self.queue) or self.pending is not None
        self.connect_button.setEnabled(not self.preview and not connected); self.port.setEnabled(not connected)
        self.upload.setEnabled(not self.preview and connected and self.protocol_ready and not busy and not self.logging_failed)
        self.start.setEnabled(not self.preview and connected and self.protocol_ready and self.ready and not busy and not self.logging_failed)
        self.reset_fault.setEnabled(not self.preview and connected and self.protocol_ready and not busy and not self.logging_failed)
        for group in (self.schedule_group,self.controller_group,self.metadata_group):group.setEnabled(not busy)

    def refresh_ports(self):
        if self.preview:return
        old=self.port.currentText(); devices=[p.device for p in list_ports.comports()]
        self.port.clear(); self.port.addItems(devices)
        preferred=old if old in devices else next((p for p in devices if 'usbmodem' in p.lower() or 'usbserial' in p.lower()),'')
        if preferred:self.port.setCurrentText(preferred)

    def open_log(self):
        folder=ROOT/'Module_8/data/raw'; folder.mkdir(parents=True,exist_ok=True)
        self.csv_path=folder/f'module_08_rod_{datetime.now():%Y%m%d_%H%M%S_%f}.csv'
        self.csv_file=self.csv_path.open('x',newline='',encoding='utf-8')
        self.csv_writer=csv.DictWriter(self.csv_file,fieldnames=FIELDS,lineterminator='\n'); self.csv_writer.writeheader(); self.csv_file.flush()
        self.raw_file=self.csv_path.with_suffix('.serial.log').open('xb')
        self.logging_failed=False

    def log(self,event='measurement',**data):
        if self.csv_writer is None:return
        row=dict(host_time=datetime.now().astimezone().isoformat(),event=event,run_id=self.run_id,
                 control_active=int(self.active),plan_sha256=self.plan_sha)
        row.update(data)
        try:self.csv_writer.writerow(row); self.csv_file.flush()
        except (OSError,ValueError) as e:
            self.csv_writer=None; self.logging_failed=True; self.stop_control(f'CSV write failed: {e}')

    def write_command(self,text,record=True):
        if self.serial_port is None or not self.serial_port.is_open:raise serial.SerialException('Arduino not connected')
        payload=(text+'\n').encode('ascii')
        if text=='STOP' and self.tx_remaining:
            # Terminate an interrupted configuration line before sending STOP.
            self.tx_remaining=b'';payload=b'\nSTOP\n'
        if self.tx_remaining:raise ValueError('Cannot interleave a partial plan command')
        # Uno's UART receive ring is only 64 bytes. ADC scan/record printing may
        # occupy ~0.2 s, so pace long plan lines without blocking the Qt timer.
        first,self.tx_remaining=payload[:48],payload[48:]
        self.last_tx=time.monotonic()
        if self.serial_port.write(first)!=len(first):raise serial.SerialException('Incomplete command write')
        if record:self.log('command',note=text)

    def advance_transmit(self,stamp):
        if not self.tx_remaining or stamp-self.last_tx<.35:return
        chunk,self.tx_remaining=self.tx_remaining[:48],self.tx_remaining[48:]
        if self.serial_port.write(chunk)!=len(chunk):raise serial.SerialException('Incomplete command write')
        self.last_tx=stamp
        if not self.tx_remaining and self.pending:self.pending=(self.pending[0],stamp)

    def connect_port(self):
        if self.preview or self.serial_port is not None:return
        try:
            self.serial_port=serial.Serial(self.port.currentText(),BAUD,timeout=0,write_timeout=.25)
            self.open_log(); self.write_command('STOP')
        except (serial.SerialException,OSError) as e:self.connection_fault(e);self.warn('Connection failed',e);return
        self.buffer=''; self.latest=None; self.last_seq=None; self.last_measurement_at=None
        self.active=self.ready=self.protocol_ready=False; self.firmware_rejected=False; self.queue.clear(); self.pending=None; self.tx_remaining=b''
        self.connected_at=time.monotonic(); self.last_ping=0
        self.update_enabled(); self.statusBar().showMessage(f'Connected; waiting for Module 8 firmware. CSV: {self.csv_path}')
        self.log('connect',note=f'baud={BAUD}; waiting for version handshake')

    def enqueue(self,commands):
        if self.pending or self.queue:raise ValueError('Wait for current upload/command')
        self.queue.extend(commands); self.update_enabled(); self.pump()

    def pump(self):
        if self.pending or not self.queue:return
        command=self.queue.popleft(); self.pending=(command.split()[0],time.monotonic())
        self.write_command(command); self.update_enabled()

    def fresh_safe(self):
        if not self.protocol_ready:raise ValueError('Upload the Module 8 firmware and wait for its version handshake')
        if self.csv_writer is None or self.raw_file is None or self.logging_failed:raise ValueError('Complete logging must be active')
        if self.latest is None or self.last_measurement_at is None or time.monotonic()-self.last_measurement_at>2:raise ValueError('Wait for a fresh measurement')
        problem=self.latest.issue()
        if problem:raise ValueError(problem)
        if self.latest.pwm or self.latest.values['run_state']=='RUNNING':raise ValueError('Wait for firmware-reported output OFF')

    def snapshot(self,plan):
        self.snapshot_id+=1
        document=plan.document()
        sensor=ROOT/'Module_8/config/sensor_map.json'
        document['sensor_map_snapshot']=json.loads(sensor.read_text()) if sensor.exists() else {'status':'missing'}
        code_paths=['Module_8/arduino/module_08_rod_controller/module_08_rod_controller.ino',
                    'Module_8/arduino/module_08_rod_controller/angstrom_core.h',
                    'Module_8/python/rod_acquisition_gui.py','Module_8/python/rod_protocol.py','Module_8/python/angstrom_plan.py']
        document['code_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in code_paths if (ROOT/p).exists()}
        document['plan_sha256']=plan.digest()
        path=self.csv_path.with_name(f'{self.csv_path.stem}_plan_{self.snapshot_id:02}.json')
        with path.open('x',encoding='utf-8') as stream:json.dump(document,stream,indent=2,allow_nan=False);stream.write('\n')
        return path

    def upload_schedule(self):
        try:
            self.fresh_safe(); plan=self.get_plan(); path=self.snapshot(plan)
            self.upload_plan=plan; self.plan_sha=plan.digest(); self.ready=False
            self.log('plan',note=f'{path.name}; purpose={plan.metadata.get("purpose","custom")}')
            self.enqueue(plan.commands())
        except (ValueError,TypeError,OSError,serial.SerialException) as e:self.stop_control(str(e));self.warn('Cannot upload',e)

    def start_control(self):
        try:
            self.fresh_safe()
            if not self.ready or self.get_plan().digest()!=self.plan_sha:raise ValueError('Upload the current plan first')
            self.write_command('PING',record=False); self.enqueue(['START'])
        except (ValueError,OSError,serial.SerialException) as e:self.stop_control(str(e));self.warn('Cannot start',e)

    def clear_fault(self):
        try:
            if not self.protocol_ready or self.latest is None or self.last_measurement_at is None or time.monotonic()-self.last_measurement_at>2:
                raise ValueError('Wait for a fresh Module 8 measurement')
            if self.latest.pwm or self.latest.values['run_state']=='RUNNING':raise ValueError('Stop and verify PWM 0 first')
            if not math.isfinite(self.latest.tec_c) or not 10<=self.latest.tec_c<=45:
                raise ValueError('TEC must be back within 10–45 C')
            if not math.isfinite(self.latest.rods_c[0]) or self.latest.rods_c[0]>=56:
                raise ValueError('T1 must be valid and below 56 C')
            self.ready=False;self.enqueue(['CLEAR'])
        except (ValueError,OSError,serial.SerialException) as e:self.warn('Cannot reset fault',e)

    def stop_control(self,reason):
        self.active=self.ready=False; self.queue.clear(); self.pending=None
        if self.serial_port is not None and self.serial_port.is_open:
            try:self.write_command('STOP')
            except (serial.SerialException,OSError) as e:reason+=f'; zero output not confirmed: {e}'
        self.log('stop',note=reason); self.update_enabled()
        self.statusBar().showMessage(reason+' — STOP requested; verify reported PWM 0')

    def handle_diagnostic(self,line):
        self.log('firmware',note=line)
        fields=line.split(',')
        if line.startswith('#firmware,'):
            self.ready=self.protocol_ready=False
            if self.active or self.pending or self.queue:self.stop_control('Arduino restarted')
            self.update_enabled()
            self.latest=None; self.last_seq=None; self.last_measurement_at=None
        if line.startswith('#ERR,'):
            self.stop_control('Firmware rejected command: '+line);return
        if line.startswith('#ACK,') and len(fields)>=2 and self.pending:
            if fields[1]!=self.pending[0]:return
            expected=self.pending[0]; self.pending=None
            if expected=='HELLO':
                if fields[2:]!=[FIRMWARE_ID]:
                    self.firmware_rejected=True;self.stop_control('Wrong firmware version');return
                self.protocol_ready=True
            elif expected=='CLEAR' and not self.queue:
                self.statusBar().showMessage('Fault/plan reset; upload the plan again before starting')
            elif expected=='COMMIT':
                self.ready=True; self.statusBar().showMessage('Plan accepted; output remains OFF. Start when ready.')
            elif expected=='START':
                self.active=True; self.run_id+=1; self.statusBar().showMessage('Schedule running on Arduino')
            self.pump(); self.update_enabled()
        if line.startswith('#EVENT,FAULT,'):
            self.stop_control('Firmware safety stop: '+line)
        elif line.startswith('#EVENT,DONE,'):
            self.active=False; self.ready=False; self.update_enabled(); self.statusBar().showMessage('Schedule complete — firmware output OFF')

    def process_measurement(self,sample,backlog=False):
        v=sample.values; stamp=time.monotonic()
        previous=self.latest; was_active=self.active
        advancing=previous is None or (sample.time_s>previous.time_s and v['seq']>previous.values['seq'])
        if self.active and (not advancing or sample.issue()):self.stop_control(sample.issue() or 'Arduino timestamp/sequence reset')
        if self.last_seq is not None and v['seq']>self.last_seq+1:
            lost=v['seq']-self.last_seq-1;self.missing+=lost;self.log('missing_records',note=f'{lost} sequence records missing')
        self.last_seq=v['seq']
        if advancing and not backlog:
            self.latest=sample; self.last_measurement_at=stamp
        if v['run_state']=='RUNNING' and not was_active:
            self.stop_control('Unexpected running firmware; upload/start explicitly')
        if v['run_state'] in ('DONE','FAULT'):
            self.active=False;self.ready=False;self.update_enabled()
        row=dict(v);row.update(mode=v['control_mode'],backlog_sample=int(backlog))
        self.log(**row)
        if self.history and sample.time_s<=self.history[-1]['time_s']:self.history=[]
        self.history.append(row)
        if len(self.history)>HISTORY_LIMIT:self.history=self.history[-HISTORY_LIMIT:]
        self.readout.setText(
            f"{v['run_state']} · mode {v['control_mode']} · step {v['step']}\n"
            f"TEC {sample.tec_c:.2f} C · T1 {sample.rods_c[0]:.2f} C · rods valid {sample.rod_ok}/5\n"
            f"Setpoint {v['setpoint_C']:.2f} C · period {v['period_s']:g} s\n"
            f"PWM applied {sample.signed_pwm:+d} · raw {v['controller_pwm']:.2f} · feedforward {v['feedforward_pwm']:.2f}\n"
            f"Safety {v['safety']} / {v['fault_code']} · good/bad/missing {self.accepted}/{self.rejected}/{self.missing}")

    def poll_serial(self):
        if self.serial_port is None:return
        try:
            stamp=time.monotonic()
            if self.active and (self.last_measurement_at is None or stamp-self.last_measurement_at>2):self.stop_control('Measurement timeout')
            self.advance_transmit(stamp)
            if not self.tx_remaining and stamp-self.last_ping>=.4:self.write_command('PING',record=False);self.last_ping=stamp
            if self.pending and stamp-self.pending[1]>3:self.stop_control('Command acknowledgement timeout')
            count=self.serial_port.in_waiting
            if count:
                raw=self.serial_port.read(count)
                self.raw_file.write(raw);self.raw_file.flush()
                self.buffer+=raw.decode('utf-8',errors='replace')
                if len(self.buffer)>65536:raise ValueError('Oversized/incomplete serial report')
                lines=self.buffer.split('\n');self.buffer=lines.pop()
                for line in lines:
                    line=line.rstrip('\r')
                    if line.startswith('#'):self.handle_diagnostic(line);continue
                    sample=parse_data_line(line)
                    if sample is None:
                        if line.strip():self.rejected+=1;self.log('malformed',note=line)
                        continue
                    self.accepted+=1;self.process_measurement(sample)
                self.redraw()
            if not self.protocol_ready and not self.firmware_rejected and self.latest is not None and not self.pending and not self.queue:
                self.enqueue(['HELLO'])
        except (serial.SerialException,OSError,ValueError,AttributeError) as e:self.connection_fault(e)

    def redraw(self):
        if not self.history:return
        times=[r['time_s'] for r in self.history]
        for key,curve in self.curves.items():curve.setData(times,[r.get(key,math.nan) for r in self.history])
        if self.whole_run.isChecked():self.show_whole_run()

    def show_whole_run(self):
        if not self.history:return
        self._fitting_x=True
        try:
            first=self.history[0]['time_s'];last=self.history[-1]['time_s']
            self.plots[0].setXRange(first,max(last,first+X_MIN_SPAN),padding=0)
        finally:self._fitting_x=False

    def fit_whole_run(self):self.whole_run.setChecked(True);self.show_whole_run()
    def x_range_changed(self,*_):
        if not self._fitting_x and self.whole_run.isChecked():self.whole_run.setChecked(False)

    def mark_event(self):
        self.log('operator_mark',note=self.mark_note.text().strip() or 'manual mark');self.mark_note.clear()

    def close_logs(self):
        for stream in (self.csv_file,self.raw_file):
            if stream:
                try:stream.close()
                except OSError:pass
        self.csv_file=self.csv_writer=self.raw_file=None

    def connection_fault(self,error):
        self.stop_control(f'Connection/log failure: {error}')
        if self.serial_port:
            try:self.serial_port.close()
            except (OSError,serial.SerialException):pass
        self.serial_port=None;self.protocol_ready=False;self.latest=None;self.close_logs();self.update_enabled()
        self.tx_remaining=b''
        self.statusBar().showMessage(f'Connection/log failure: {error}. Firmware link watchdog stops output with a 2 s timeout (plus one acquisition scan).')

    def disconnect_port(self):
        self.stop_control('Disconnected');self.log('disconnect',note='Serial closed')
        if self.serial_port:
            try:self.serial_port.close()
            except (OSError,serial.SerialException):pass
        self.serial_port=None;self.protocol_ready=False;self.latest=None;self.close_logs();self.update_enabled()
        self.tx_remaining=b''

    def closeEvent(self,event):
        self.timer.stop();self.disconnect_port();event.accept()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--preview',action='store_true')
    args=parser.parse_args();app=QApplication(sys.argv);window=RodAcquisitionWindow(args.preview);window.show();return app.exec()

if __name__=='__main__':sys.exit(main())
