"""S18.3 raw-sine adapter for the unchanged Module 6 one-lump solver.

No serial or hardware access. H=1 is an arbitrary normalization: C=H*tau,
P_u,c=H*chi_c, r=chi_h/chi_c. Equal susceptibilities need no TEC inversion.
"""
from dataclasses import asdict, dataclass
from datetime import datetime
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import numpy as np

MODULE=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).with_name('tec_model_v3.py')
spec=importlib.util.spec_from_file_location('m08_copied_tec_model',SOURCE)
model=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=model
spec.loader.exec_module(model)


@dataclass(frozen=True)
class Setup:
    case_id:str='custom'
    period_s:float=100.
    chi_c_C_per_pwm:float=.23
    chi_h_C_per_pwm:float=.46
    ambient_C:float=22.
    initial_C:float=22.
    thermal_time_constant_s:float=80.
    ua_pwm:float=0.
    ub_pwm:float=50.
    pwm_limit:float=255.
    dt_s:float=.05
    duration_s:float=1000.
    normalization_H_W_per_K:float=1.

    def validate(self):
        values=asdict(self)
        if any(not math.isfinite(v) for k,v in values.items() if k!='case_id'):
            raise ValueError('All numeric inputs must be finite.')
        if self.period_s<100:raise ValueError('Use a period of at least 100 s.')
        for key in ('chi_c_C_per_pwm','chi_h_C_per_pwm','thermal_time_constant_s','dt_s','duration_s','normalization_H_W_per_K'):
            if values[key]<=0:raise ValueError(key+' must be positive.')
        if self.ub_pwm<=0 or not 0<self.pwm_limit<=255:
            raise ValueError('Amplitude must be positive; PWM limit must be in (0, 255].')
        if abs(self.ua_pwm)+self.ub_pwm>self.pwm_limit:
            raise ValueError('The sine exceeds the chosen PWM limit. Lower Ua/Ub or raise the simulation limit.')
        if self.dt_s>min(self.period_s,self.thermal_time_constant_s)/100:
            raise ValueError('Use dt <= min(period, thermal time constant)/100.')
        if not math.isclose(self.duration_s/self.dt_s,round(self.duration_s/self.dt_s),abs_tol=1e-7):
            raise ValueError('Duration must be an integer multiple of dt.')
        return self

    def to_model_config(self):
        self.validate();H=self.normalization_H_W_per_K
        return model.ModelConfig(ambient_c=self.ambient_C,initial_c=self.initial_C,
            setpoint_c=self.ambient_C,total_capacitance_j_per_c=H*self.thermal_time_constant_s,
            heat_loss_w_per_c=H,tec_power_w_per_pwm=H*self.chi_c_C_per_pwm,
            heating_to_cooling_ratio=self.chi_h_C_per_pwm/self.chi_c_C_per_pwm,
            measured_cooling_chi_c_per_pwm=self.chi_c_C_per_pwm,
            measured_heating_chi_c_per_pwm=self.chi_h_C_per_pwm,
            measured_tau_s=self.thermal_time_constant_s,pwm_limit=self.pwm_limit,
            dt_s=self.dt_s,kp_pwm_per_c=0.,ki_pwm_per_c_s=0.)


def load_setup(path):
    data=json.loads(Path(path).read_text())
    return Setup(**{k:v for k,v in data.items() if k in Setup.__dataclass_fields__}).validate()


def input_pwm(setup,t):
    return setup.ua_pwm+setup.ub_pwm*math.sin(2*math.pi*t/setup.period_s)


def equal_chi_solution(setup,t):
    """Complete continuous solution, including initial transient; equal chi only."""
    if not math.isclose(setup.chi_h_C_per_pwm,setup.chi_c_C_per_pwm):return None
    t=np.asarray(t,float);chi=setup.chi_h_C_per_pwm;tau=setup.thermal_time_constant_s
    wt=2*np.pi*tau/setup.period_s
    a=chi*setup.ub_pwm/(1+wt*wt);b=-a*wt
    mean=setup.ambient_C+chi*setup.ua_pwm
    transient=setup.initial_C-mean-b
    return mean+a*np.sin(2*np.pi*t/setup.period_s)+b*np.cos(2*np.pi*t/setup.period_s)+transient*np.exp(-t/tau)


class Simulation:
    def __init__(self,setup):
        self.setup=setup.validate();self.base=setup.to_model_config()
        self.state=model.ModelState(0.,setup.initial_C,setup.initial_C)
        self.steps=0;self.step_count=round(setup.duration_s/setup.dt_s)
        # Last column is applied on the previous Euler interval; input_pwm is
        # the instantaneous scheduled input at this row's timestamp.
        self.rows=[[0.,setup.initial_C,input_pwm(setup,0.),None,False]]

    @property
    def finished(self):return self.steps>=self.step_count

    def advance(self,count=1):
        from dataclasses import replace
        for _ in range(min(count,self.step_count-self.steps)):
            self.state.time_s=self.steps*self.setup.dt_s
            command=input_pwm(self.setup,self.state.time_s)
            config=replace(self.base,open_loop_pwm=command)
            result=model.advance_model(self.state,config,'one_lump','open_loop')
            self.steps+=1;self.state.time_s=self.steps*self.setup.dt_s
            self.rows.append([self.state.time_s,result.tec_temperature_c,
                input_pwm(self.setup,self.state.time_s),result.applied_pwm,result.saturated])

    def arrays(self):return np.array([r[:3] for r in self.rows],float).T

    def metrics(self):
        t,T,u=self.arrays();P=self.setup.period_s
        complete=int((t[-1]+1e-8)//P)
        if complete<5:return None
        end=complete*P;start=end-5*P;keep=(t>=start-1e-8)&(t<end-1e-8)
        def fit(mask):
            tt=t[mask];y=T[mask];X=np.column_stack([np.ones(len(tt)),np.cos(2*np.pi*tt/P),np.sin(2*np.pi*tt/P)])
            c=np.linalg.lstsq(X,y,rcond=None)[0];B=float(np.hypot(c[1],c[2]));phi=math.atan2(-c[2],c[1]);res=y-X@c
            return c,B,phi,res
        c,B,phi,res=fit(keep);cycles=[fit((t>=a-1e-8)&(t<a+P-1e-8)) for a in np.arange(start,end,P)]
        phase=np.unwrap([f[2] for f in cycles]);amps=np.array([f[1] for f in cycles])
        return {'mean_C':float(c[0]),'mean_minus_room_C':float(c[0]-self.setup.ambient_C),
            'fundamental_amplitude_C':B,'phase_lag_deg':float(np.degrees((-np.pi/2-phi+np.pi)%(2*np.pi)-np.pi)),
            'sinusoidal_residual_rms_C':float(np.sqrt(np.mean(res*res))),
            'retained_start_s':start,'retained_end_s':end,'retained_cycles':5,
            'cycle_mean_span_C':float(np.ptp([f[0][0] for f in cycles])),
            'cycle_amplitude_span_fraction':float(np.ptp(amps)/np.mean(amps)),
            'cycle_phase_span_rad':float(np.ptp(phase)),
            'selected_saturated_samples':sum(bool(self.rows[i][4]) for i in np.flatnonzero(keep)),
            'interpretation':'Last five complete simulated cycles; inspect repeatability and residuals. Run duration alone does not establish settling.'}

    def export(self,output=None,figure_output=None):
        output=Path(output) if output else MODULE/'data/simulation/s18_3'
        figure_output=Path(figure_output) if figure_output else MODULE/'figures/simulation/s18_3'
        output.mkdir(parents=True,exist_ok=True);figure_output.mkdir(parents=True,exist_ok=True)
        stem=f'm08_sim_{self.setup.case_id}_{datetime.now():%Y%m%d_%H%M%S_%f}'
        csv_path=output/(stem+'.csv');info_path=output/(stem+'.json')
        with csv_path.open('x',newline='') as f:
            writer=csv.writer(f);writer.writerow(['time_s','simulated_tec_C','input_pwm','previous_step_applied_pwm','previous_step_saturated']);writer.writerows(self.rows)
        provenance={'kind':'mathematical_simulation_not_measurement','setup':asdict(self.setup),
            'model':'Copied Module 6 one-lump forward Euler; no cooling compensation or feedback in raw mode',
            'arbitrary_normalization':'H=normalization_H_W_per_K, C=H*tau, P_u,c=H*chi_c; not separately measured physical constants.',
            'csv':str(csv_path),'csv_sha256':hashlib.sha256(csv_path.read_bytes()).hexdigest(),
            'copied_solver_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'completed':self.finished,'metrics':self.metrics(),
            'ambient_note':'22 C in course presets is a prescribed simulation value, not measured laboratory ambient.'}
        info_path.write_text(json.dumps(provenance,indent=2,allow_nan=False)+'\n')
        os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'m08_sim_matplotlib'))
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        fig=Figure(figsize=(11,9),layout='constrained');FigureCanvasAgg(fig)
        axes=fig.subplots(3,1);t,T,u=self.arrays()
        axes[0].plot(t,T,lw=1,label='Numerical TEC');analytic=equal_chi_solution(self.setup,t)
        if analytic is not None:axes[0].plot(t,analytic,'--',lw=1,label='Equal-χ analytical solution')
        axes[0].set(ylabel='Temperature (°C)',title='Full simulated history, including startup');axes[0].legend()
        axes[1].plot(t,u,lw=.8,color='black');axes[1].set(ylabel='Raw input (PWM)',xlabel='Model time (s)')
        metrics=self.metrics()
        if metrics:
            keep=(t>=metrics['retained_start_s']-1e-8)&(t<metrics['retained_end_s']-1e-8)
            tt=t[keep];X=np.column_stack([np.ones(len(tt)),np.cos(2*np.pi*tt/self.setup.period_s),np.sin(2*np.pi*tt/self.setup.period_s)])
            pred=X@np.linalg.lstsq(X,T[keep],rcond=None)[0]
            axes[0].axvspan(metrics['retained_start_s'],metrics['retained_end_s'],alpha=.12,color='grey')
            axes[2].plot(tt,T[keep]-pred,lw=.8);axes[2].set(ylabel='Harmonic residual (°C)',xlabel='Model time (s)',title='Last five complete cycles; residual includes waveform distortion')
        else:axes[2].text(.5,.5,'Fewer than five complete cycles: no settled-response readout',ha='center',transform=axes[2].transAxes)
        for ax in axes:ax.grid(alpha=.2)
        fig.suptitle('SIMULATION — '+self.setup.case_id)
        for ext in ('png','pdf'):fig.savefig(figure_output/(stem+'.'+ext),dpi=160)
        return csv_path,info_path,figure_output/(stem+'.png')
