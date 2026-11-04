"""Offline Module 8 analysis/configuration viewer. No serial imports or hardware actions."""
from pathlib import Path
import argparse
import csv
import json
import math
import sys
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
    QPushButton,QSplitter,QPlainTextEdit,QTextBrowser,QFileDialog,QComboBox,QLabel,QMessageBox)
import pyqtgraph as pg
sys.path.insert(0,str(Path(__file__).parent/'analysis'))
import angstrom_fit as fit
ROOT=Path(__file__).resolve().parents[2]


class AnalysisWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('Module 8 - Offline Angstrom analysis');self.resize(1360,900)
        self.config_path=ROOT/'Module_8/config/analysis_plan.json';self.result=None
        body=QWidget();outer=QVBoxLayout(body);self.setCentralWidget(body)
        banner=QLabel('OFFLINE ANALYSIS | Load measured periodic data and geometry; this window never connects to Arduino.')
        banner.setWordWrap(True);outer.addWidget(banner)
        split=QSplitter(Qt.Horizontal);outer.addWidget(split,1)
        left=QWidget();controls=QVBoxLayout(left);split.addWidget(left)
        for title,callback in [('Open analysis plan',self.load_plan),('Choose measured CSV',self.choose_raw),('Choose measured sensor map',self.choose_map),('Save plan as...',self.save_plan),('Fit saved plan',self.analyse),('Open existing result',self.open_result)]:
            button=QPushButton(title);button.clicked.connect(callback);controls.addWidget(button)
        self.editor=QPlainTextEdit();controls.addWidget(self.editor,1)
        if self.config_path.exists():self.editor.setPlainText(self.config_path.read_text())
        right=QWidget();view=QVBoxLayout(right);split.addWidget(right);split.setSizes([430,900])
        self.selector=QComboBox();self.selector.currentIndexChanged.connect(self.show_interval);view.addWidget(self.selector)
        self.summary=QTextBrowser();self.summary.setMaximumHeight(220);view.addWidget(self.summary)
        self.history=pg.PlotWidget(title='Measured traces and selected interval');self.history.setBackground('w');self.history.addLegend();self.history.setLabel('left','Temperature',units='C');self.history.setLabel('bottom','Arduino time',units='s');view.addWidget(self.history,2)
        row=QHBoxLayout();view.addLayout(row,1)
        self.amplitude=pg.PlotWidget(title='Log amplitude and spatial fit');self.phase=pg.PlotWidget(title='Unwrapped phase and spatial fit')
        for plot in (self.amplitude,self.phase):plot.setBackground('w');plot.setLabel('bottom','x',units='m');row.addWidget(plot)
        self.trace_selector=QComboBox();self.trace_selector.addItems(fit.CHANNELS);view.addWidget(self.trace_selector)
        self.residual=pg.PlotWidget(title='Selected sensor: time residuals');self.residual.setBackground('w');self.residual.addLegend();self.residual.setLabel('bottom','Arduino time',units='s');self.residual.setLabel('left','Measured - model',units='C');view.addWidget(self.residual,1)
        self.trace_selector.currentIndexChanged.connect(self.show_trace_residual)
        self.summary.setPlainText('No measured Module 8 result loaded. The template does not certify any dataset.\nComplete measured x_m/L and select at least five settled cycles at each retained period.\nMaterial inputs remain unknown until supplied; k and h are then left uncomputed.')

    def error(self,exc):QMessageBox.warning(self,'Analysis not completed',str(exc))
    def load_plan(self):
        path,_=QFileDialog.getOpenFileName(self,'Analysis plan',str(ROOT/'Module_8/config'),'JSON (*.json)')
        if path:self.config_path=Path(path);self.editor.setPlainText(self.config_path.read_text())
    def choose(self,key,title):
        path,_=QFileDialog.getOpenFileName(self,title,str(ROOT/'Module_8'))
        if not path:return
        try:
            config=json.loads(self.editor.toPlainText());config[key]=fit.portable(Path(path));self.editor.setPlainText(json.dumps(config,indent=2))
        except (ValueError,OSError) as exc:self.error(exc)
    def choose_raw(self):self.choose('raw','Measured periodic CSV')
    def choose_map(self):self.choose('sensor_map','Measured oscillatory geometry JSON')
    def save_plan(self):
        try:
            config=json.loads(self.editor.toPlainText())
            path,_=QFileDialog.getSaveFileName(self,'Save analysis plan',str(self.config_path),'JSON (*.json)')
            if path:self.config_path=Path(path);self.config_path.write_text(json.dumps(config,indent=2)+'\n')
        except (ValueError,OSError) as exc:self.error(exc)
    def analyse(self):
        try:
            if json.loads(self.editor.toPlainText())!=json.loads(self.config_path.read_text()):raise ValueError('Save the edited plan before fitting, so the output identifies its exact inputs.')
            target,result=fit.analyse_plan(self.config_path)
            for i,r in enumerate(result['intervals']):fit.make_figure(r,ROOT/'Module_8/figures'/(self.config_path.stem+f'_interval_{i+1}.png'))
            self.load_result(result);self.statusBar().showMessage('Saved '+str(target))
        except (ValueError,KeyError,OSError) as exc:self.error(exc)
    def open_result(self):
        path,_=QFileDialog.getOpenFileName(self,'Analysis result',str(ROOT/'Module_8/data/processed'),'JSON (*.json)')
        if path:
            try:self.load_result(json.loads(Path(path).read_text()))
            except (ValueError,KeyError,OSError) as exc:self.error(exc)
    def load_result(self,result):
        if result.get('kind')!='measured_periodic_analysis':raise ValueError('Choose an Angstrom analysis result')
        self.result=result;self.selector.blockSignals(True);self.selector.clear()
        for r in result['intervals']:self.selector.addItem(f"{r['label']} | {r['period_s']:g} s | {r['status']}")
        self.selector.blockSignals(False);self.show_interval(0)
    def show_interval(self,index):
        if self.result is None or index<0:return
        r=self.result['intervals'][index];t=r['transport'];s=r['spatial_fit']
        def value(x):return 'not supplied' if x is None else f'{x:.6g}'
        lines=[f"{r['status']} | {r['complete_cycles']} complete cycles | {r['samples']} samples",
            f"q = {s['q_per_m']:.6g} /m; q' = {s['q_prime_per_m']:.6g} /m",
            f"kappa = {value(t['kappa_m2_s'])} m2/s; nu = {value(t['nu_per_s'])} /s",
            f"k = {value(t['k_W_mK'])} W/(m K); h = {value(t['h_W_m2K'])} W/(m2 K)",
            f"Bi_perp = {r['bi_perp']:.4g}; repeat-fit errors exclude systematic errors"]+r['warnings']
        self.summary.setPlainText('\n'.join(lines));self.amplitude.clear();self.phase.clear();self.history.clear()
        xs=np.array(r['positions_m']);fs=[r['channel_fits'][f'rod{i}_C'] for i in r['selected_rod_sensors']]
        self.amplitude.plot(xs,np.log([f['amplitude_C'] for f in fs]),pen=None,symbol='o',symbolBrush='#245a81')
        self.amplitude.plot(xs,s['log_amplitude_intercept']-s['q_per_m']*xs,pen='#245a81')
        self.phase.plot(xs,s['unwrapped_phases_rad'],pen=None,symbol='o',symbolBrush='#b45b22')
        self.phase.plot(xs,s['phase_intercept_rad']-s['q_prime_per_m']*xs,pen='#b45b22')
        self.amplitude.setLabel('left','ln B');self.phase.setLabel('left','Phase',units='rad')
        raw=ROOT/self.result['source']
        if raw.exists():
            with raw.open(newline='') as stream:rows=[z for z in csv.DictReader(stream) if z.get('event')=='measurement']
            ts=[fit.number(z.get('time_s')) for z in rows]
            for ch,color in zip(fit.CHANNELS,['#111111','#245a81','#2f7d4f','#927919','#b45b22','#693f85']):self.history.plot(ts,[fit.number(z.get(ch)) for z in rows],pen=color,name=ch)
            region=pg.LinearRegionItem((r['start_s'],r['end_s']),movable=False);self.history.addItem(region)
        else:self.statusBar().showMessage('Source CSV missing: fits are visible, raw time history unavailable')
        self.show_trace_residual()

    def show_trace_residual(self,*_):
        self.residual.clear()
        if self.result is None:return
        index=self.selector.currentIndex()
        if index<0:return
        r=self.result['intervals'][index];raw=ROOT/self.result['source'];ch=self.trace_selector.currentText()
        if not raw.exists() or ch not in r['channel_fits']:return
        with raw.open(newline='') as stream:
            rows=[z for z in csv.DictReader(stream) if z.get('event')=='measurement' and r['start_s']<=fit.number(z.get('time_s'))<r['end_s']]
        t=np.array([fit.number(z['time_s']) for z in rows]);y=np.array([fit.number(z.get(ch)) for z in rows]);tr=t-r['start_s']
        a,c,s=r['channel_fits'][ch]['coefficients'];w=2*np.pi/r['period_s']
        offset=fit.number(r['geometry'].get('sample_time_offsets_s',{}).get(ch,0))
        fitted=a+c*np.cos(w*(tr+offset))+s*np.sin(w*(tr+offset))
        self.residual.plot(t,y-fitted,pen='#245a81',name='Individual sinusoid residual')
        if ch.startswith('rod'):
            i=int(ch[3:-2])-1;x=r['geometry']['x_m'][i];base=r['channel_fits']['rod1_C'];z0=complex(base['coefficients'][1],-base['coefficients'][2])
            sp=r['spatial_fit'];z=z0*np.exp(-complex(sp['q_per_m'],sp['q_prime_per_m'])*x)
            model=a+np.real(z*np.exp(1j*w*(tr+offset)))
            self.residual.plot(t,y-model,pen='#b45b22',name='Spatial semi-infinite model residual')


def main():
    app=QApplication(sys.argv);w=AnalysisWindow();w.show();return app.exec()
if __name__=='__main__':raise SystemExit(main())
