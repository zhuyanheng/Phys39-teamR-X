"""Module 8 raw-sine simulation GUI using the copied Module 6 solver. No device access."""
import argparse
from dataclasses import asdict
import json
import math
from pathlib import Path
import sys
import numpy as np
from PySide6 import QtCore, QtWidgets
import pyqtgraph as pg

sys.path.insert(0,str(Path(__file__).resolve().parent/'simulation'))
from periodic_model import MODULE, Setup, Simulation, load_setup, equal_chi_solution

FIELDS=(('period_s','Drive period (s)',100,1000,0),
    ('chi_c_C_per_pwm','Cooling χc (°C/PWM)',.001,2,4),
    ('chi_h_C_per_pwm','Heating χh (°C/PWM)',.001,2,4),
    ('ambient_C','Room temperature (°C)',-50,100,2),
    ('initial_C','Initial temperature (°C)',-50,100,2),
    ('thermal_time_constant_s','Thermal time constant (s)',1,10000,2),
    ('ua_pwm','PWM mean Ua',-255,255,2),('ub_pwm','PWM amplitude Ub',.01,255,2),
    ('pwm_limit','PWM limit',1,255,0),('dt_s','Euler time step (s)',.001,1,3),
    ('duration_s','Stop at model time (s)',1,100000,2))


class Simulator(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('Module 8 — one-lump sinusoidal PWM simulation');self.resize(1440,880)
        self.timer=QtCore.QTimer(self);self.timer.setInterval(30);self.timer.timeout.connect(self.tick)
        self.presets=sorted((MODULE/'config/simulation').glob('s18_3_*.json'))
        central=QtWidgets.QWidget();self.setCentralWidget(central);layout=QtWidgets.QHBoxLayout(central)
        panel=QtWidgets.QVBoxLayout();layout.addLayout(panel,1);plots=QtWidgets.QVBoxLayout();layout.addLayout(plots,3)
        title=QtWidgets.QLabel('S18.3: six simulated raw-PWM runs');title.setStyleSheet('font-weight: bold; font-size: 17px;');panel.addWidget(title)
        note=QtWidgets.QLabel('One-lump model · raw sinusoidal PWM\nChoose a preset, then Run. No TEC connection.');note.setWordWrap(True);panel.addWidget(note)
        self.combo=QtWidgets.QComboBox()
        for p in self.presets:self.combo.addItem(p.stem)
        panel.addWidget(self.combo);self.combo.currentIndexChanged.connect(self.load_preset)
        form=QtWidgets.QFormLayout();panel.addLayout(form);self.inputs={}
        for key,label,lo,hi,digits in FIELDS:
            box=QtWidgets.QDoubleSpinBox();box.setRange(lo,hi);box.setDecimals(digits);box.setSingleStep(.01 if digits>=3 else 1)
            self.inputs[key]=box;form.addRow(label,box);box.valueChanged.connect(self.edited)
        self.speed=QtWidgets.QDoubleSpinBox();self.speed.setRange(1,500);self.speed.setValue(50);self.speed.setSuffix(' ×');form.addRow('Playback speed',self.speed)
        row=QtWidgets.QHBoxLayout();panel.addLayout(row)
        self.run_button=QtWidgets.QPushButton('Run');self.run_button.clicked.connect(self.toggle);row.addWidget(self.run_button)
        reset=QtWidgets.QPushButton('Apply / Reset');reset.clicked.connect(self.apply);row.addWidget(reset)
        save=QtWidgets.QPushButton('Save CSV + results + figures');save.clicked.connect(self.save);panel.addWidget(save)
        self.status=QtWidgets.QLabel();self.status.setWordWrap(True);panel.addWidget(self.status)
        self.readout=QtWidgets.QLabel();self.readout.setWordWrap(True);self.readout.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse);panel.addWidget(self.readout)
        footer=QtWidgets.QLabel('Output: Module_8/data/simulation/s18_3\nFigures: Module_8/figures/simulation/s18_3\n22°C is the teaching scenario, not measured room temperature.');footer.setWordWrap(True);panel.addWidget(footer);panel.addStretch()
        pg.setConfigOptions(antialias=True,background='w',foreground='k')
        self.temperature=pg.PlotWidget(title='Simulated TEC temperature');self.temperature.setLabel('left','Temperature',units='°C');self.temperature.setLabel('bottom','Model time',units='s');self.temperature.addLegend()
        self.temperature.getAxis('bottom').enableAutoSIPrefix(False)
        self.curve=self.temperature.plot(pen=pg.mkPen('#2563eb',width=2),name='Numerical TEC')
        self.analytic=self.temperature.plot(pen=pg.mkPen('#d97706',width=1.4,style=QtCore.Qt.DashLine),name='Equal-χ analytical')
        plots.addWidget(self.temperature,3)
        self.pwm=pg.PlotWidget(title='Uncompensated raw PWM input');self.pwm.setLabel('left','Signed PWM');self.pwm.setLabel('bottom','Model time',units='s')
        self.pwm.getAxis('bottom').enableAutoSIPrefix(False)
        self.pwm_curve=self.pwm.plot(pen=pg.mkPen('#111827',width=1.3));plots.addWidget(self.pwm,2);self.pwm.setXLink(self.temperature)
        self.loading=False;self.dirty=False;self.load_preset(0)

    def load_preset(self,index):
        self.timer.stop();self.run_button.setText('Run');self.loading=True
        s=load_setup(self.presets[index]);self.case_id=s.case_id
        for key,box in self.inputs.items():box.setValue(getattr(s,key))
        self.loading=False;self.dirty=False;self.apply()

    def edited(self,*args):
        if self.loading:return
        self.timer.stop();self.run_button.setText('Run');self.dirty=True
        self.status.setText('Settings changed. Apply / Reset starts a fresh run. Save still exports the previous active settings.')

    def setup(self):
        return Setup(case_id='custom' if self.dirty else self.case_id,**{key:box.value() for key,box in self.inputs.items()}).validate()

    def apply(self):
        try:s=self.setup()
        except ValueError as e:QtWidgets.QMessageBox.warning(self,'Check settings',str(e));return False
        self.timer.stop();self.run_button.setText('Run');self.sim=Simulation(s);self.dirty=False;self.case_id=s.case_id;self.draw();return True

    def toggle(self):
        if self.timer.isActive():self.timer.stop();self.run_button.setText('Run');return
        if self.dirty and not self.apply():return
        if self.sim.finished:return
        self.timer.start();self.run_button.setText('Pause')

    def tick(self):
        count=max(1,round(self.speed.value()*self.timer.interval()/1000/self.sim.setup.dt_s))
        self.sim.advance(count)
        if self.sim.finished:self.timer.stop();self.run_button.setText('Run')
        self.draw()

    def draw(self):
        t,T,u=self.sim.arrays();stride=max(1,len(t)//10000)
        self.curve.setData(t[::stride],T[::stride]);self.pwm_curve.setData(t[::stride],u[::stride])
        exact=equal_chi_solution(self.sim.setup,t[::stride])
        self.analytic.setData(t[::stride],exact) if exact is not None else self.analytic.setData([],[])
        for item,label in self.temperature.plotItem.legend.items:
            if item.item is self.analytic:
                item.setVisible(exact is not None);label.setVisible(exact is not None)
        state='Completed' if self.sim.finished else 'Paused' if not self.timer.isActive() else 'Running'
        self.status.setText(f'{state}: {t[-1]:.1f} / {self.sim.setup.duration_s:g} simulated seconds\nAll startup samples are retained in memory.')
        m=self.sim.metrics()
        if m:
            self.readout.setText(f'Last five complete cycles ({m["retained_start_s"]:g}–{m["retained_end_s"]:g} s)\nMean − room: {m["mean_minus_room_C"]:.5f} °C\nAmplitude: {m["fundamental_amplitude_C"]:.5f} °C\nPhase lag vs PWM: {m["phase_lag_deg"]:.4f}°\nHarmonic residual RMS: {m["sinusoidal_residual_rms_C"]:.5f} °C\nFive-cycle spans: mean {m["cycle_mean_span_C"]:.5g} °C; amplitude {m["cycle_amplitude_span_fraction"]:.3%}; phase {m["cycle_phase_span_rad"]:.5g} rad\nInspect repeatability before calling it settled.')
        else:self.readout.setText('Response readout appears after five complete simulated cycles. Run to the preset endpoint, then inspect the cycle spans.')

    def save(self):
        if len(self.sim.rows)<2:QtWidgets.QMessageBox.information(self,'No samples','Run the simulation first.');return
        self.timer.stop();self.run_button.setText('Run')
        try:paths=self.sim.export()
        except Exception as e:QtWidgets.QMessageBox.warning(self,'Export failed',str(e));return
        self.status.setText('Saved full simulated history and analysis:\n'+str(paths[0]));self.statusBar().showMessage(str(paths[0]))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    app=QtWidgets.QApplication.instance() or QtWidgets.QApplication([]);window=Simulator()
    if args.check:
        for i in range(len(window.presets)):window.load_preset(i);assert window.sim.setup.period_s>=100
        print('Loaded all six presets; simulation GUI initialized without device access.');window.close();return
    window.show();app.exec()


if __name__=='__main__':main()
