"""Stage 2 measured raw-PWM figures and six-row S18.3 SIMULATION table.

Run: .venv/bin/python Module_8/python/analysis/stage2_raw_pwm.py
Never connects to hardware or edits raw files. Teaching inputs are not measured
ambient conditions. The short 300 s record is shown with explicit limitations.
"""
import csv
from dataclasses import asdict
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import numpy as np
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'m08_stage2_matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from angstrom_fit import ROOT,MODULE,CHANNELS,fit_trace,safe
from initial_tec_reference import initial_tec_reference
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'simulation'))
from periodic_model import Simulation,load_setup,equal_chi_solution,SOURCE

FIG=MODULE/'figures/stage2'
OUT=MODULE/'data/processed/stage2'
SIM=MODULE/'data/simulation/s18_3'
RAW={300:'m08_raw_zero_p300s_ua0_ub50_20261111_113001_400415.csv',
     200:'m08_raw_zero_p200s_ua0_ub50_20261116_093755_907199.csv',
     100:'m08_raw_zero_p100s_ua0_ub50_20261116_100248_724317.csv',
     'positive':'m08_raw_pos_p100s_ua32_ub5_20261116_102227_751202.csv'}
COLORS=['#111827','#2563eb','#d97706','#059669','#9333ea','#db2777']


def sha(b):return hashlib.sha256(b).hexdigest()


def write_json(p,v):p.write_text(json.dumps(safe(v),indent=2,allow_nan=False)+'\n')


def save(fig,stem):
    for ext in ('png','pdf'):fig.savefig(FIG/(stem+'.'+ext),dpi=180)
    plt.close(fig)


def measured(filename):
    path=MODULE/'data/raw'/filename;content=path.read_bytes()
    rows=list(csv.DictReader(io.StringIO(content.decode())))
    active=[r for r in rows if r['event']=='measurement' and r['run_state']=='RUNNING']
    assert len({(r['run_id'],r['step'],r['control_mode'],r['period_s']) for r in active})==1
    event=next(r for r in rows if r.get('note','').startswith('#EVENT,STEP,') and r['run_id']==active[0]['run_id'])
    start=int(event['note'].split(',')[2])/1000;P=float(active[0]['period_s'])
    t=np.array([float(r['time_s'])-start for r in active]);dt=float(np.median(np.diff(t)))
    assert np.all(np.diff(t)>0) and np.max(np.diff(t))<1.5
    complete=int((t[-1]+1.1*dt)//P);retained=min(3,complete);a=(complete-retained)*P;b=complete*P
    keep=(t>=a)&(t<b);T=np.array([[float(r[ch]) for r in active] for ch in CHANNELS]);u=np.array([float(r['signed_pwm']) for r in active])
    assert np.isfinite(T).all() and np.isfinite(u).all()
    assert all(r['fault_code']=='NONE' and r['safety']=='OK' for r in active)
    seq=np.array([int(r['seq']) for r in active]);miss=int(np.maximum(np.diff(seq)-1,0).sum())
    fits={ch:fit_trace(t[keep],T[i,keep],P) for i,ch in enumerate(CHANNELS)}
    f=fits['tec_C'];fu=fit_trace(t[keep],u[keep],P)
    room=initial_tec_reference(rows)
    lag=np.degrees((fu['phase_rad']-f['phase_rad']+np.pi)%(2*np.pi)-np.pi)
    cycles=[fit_trace(t[(t>=a+j*P)&(t<a+(j+1)*P)],T[0,(t>=a+j*P)&(t<a+(j+1)*P)],P) for j in range(retained)]
    info={'kind':'measured_raw_pwm_diagnostic','source':str(path.relative_to(ROOT)),'source_sha256':sha(content),
        'period_s':P,'mode':active[0]['control_mode'],'ua_pwm':float(active[0]['Ua_pwm']),'ub_pwm':float(active[0]['Ub_pwm']),
        'active_samples':len(active),'duration_covered_s':float(t[-1]+dt),'complete_cycles':complete,
        'selected_complete_cycles':list(range(complete-retained+1,complete+1)),
        'selected_start_s':a,'selected_end_s':b,'missing_sequence_samples':miss,
        'mean_tec_C':f['mean_C'],'fundamental_amplitude_C':f['amplitude_C'],
        'phase_lag_vs_applied_pwm_deg':float(lag),'sinusoidal_residual_rms_C':f['rms_residual_C'],
        'residual_rms_over_amplitude':f['rms_residual_C']/f['amplitude_C'],
        'selected_cycle_mean_span_C':float(np.ptp([v['mean_C'] for v in cycles])),
        'selected_cycle_amplitude_span_fraction':float(np.ptp([v['amplitude_C'] for v in cycles])/np.mean([v['amplitude_C'] for v in cycles])),
        'selected_cycle_phase_span_rad':float(np.ptp(np.unwrap([v['phase_rad'] for v in cycles]))),
        'selected_saturated_samples':sum(r['saturated']=='1' for i,r in enumerate(active) if keep[i]),
        'ambient_C':None,**room,'mean_minus_room_reference_C':f['mean_C']-room['room_reference_C'],
        'qualification':'Descriptive final complete-cycle fits; not automatic settling certification.',
        'short_run_warning':'Only two complete cycles at 300 s; selected interval includes startup and is diagnostic.' if complete<3 else None}
    assert sha(path.read_bytes())==info['source_sha256']
    return {'info':info,'path':path,'t':t,'T':T,'u':u,'keep':keep,'fits':fits}


def measured_figures(runs):
    fig,axs=plt.subplots(3,2,figsize=(13,11),layout='constrained',gridspec_kw={'width_ratios':[1.6,1]})
    for row,P in enumerate((300,200,100)):
        r=runs[P];info=r['info'];t=r['t'];left,right=axs[row]
        for j,ch in enumerate(CHANNELS):left.plot(t,r['T'][j],lw=1 if j==0 else .7,color=COLORS[j],label='TEC' if j==0 else f'T{j}')
        right.plot(t,r['u'],color='#111827',lw=.8)
        for ax in (left,right):ax.set_xlim(0,t[-1]);ax.set_xlabel('Time from STEP (s)');ax.axvspan(info['selected_start_s'],info['selected_end_s'],color='#64748b',alpha=.10);ax.grid(alpha=.2)
        left.set(ylabel='Measured temperature (°C)',title=f'{P} s | '+('short record: 2 full cycles + partial tail' if P==300 else f'{info["complete_cycles"]} full cycles'))
        right.set(ylabel='Applied signed PWM',title=f'Ua=0, Ub=50 PWM | {P} s');right.axhline(0,color='grey',lw=.6)
        if row==0:left.legend(ncol=6,fontsize=8,loc='upper right')
    fig.suptitle('Module 8 Stage 2 / S18.3 — measured zero-centered raw PWM\nUnmodified six-channel histories; shaded = descriptive fit window',fontsize=15)
    save(fig,'m08_stage2_s18_3_measured_zero_pwm')
    fig,axs=plt.subplots(3,2,figsize=(12,9),layout='constrained')
    for col,key in enumerate((100,'positive')):
        r=runs[key];info=r['info'];m=r['keep'];t=r['t'][m]-info['selected_start_s'];f=r['fits']['tec_C'];c=f['coefficients'];w=2*np.pi/100
        absolute=r['t'][m];pred=c[0]+c[1]*np.cos(w*absolute)+c[2]*np.sin(w*absolute)
        axs[0,col].plot(t,r['T'][0,m],lw=1,color='#2563eb',label='Measured TEC');axs[0,col].plot(t,pred,'--',lw=1,color='#d97706',label='First-harmonic fit')
        axs[0,col].set(title=('Zero-centered' if key==100 else 'Positive-only')+f' | Ua={info["ua_pwm"]:g}, Ub={info["ub_pwm"]:g} PWM',ylabel='Temperature (°C)');axs[0,col].legend(fontsize=8)
        axs[1,col].plot(t,r['u'][m],color='#111827',lw=.9);axs[1,col].set(ylabel='Applied PWM');axs[1,col].axhline(0,color='grey',lw=.5)
        axs[2,col].plot(t,r['T'][0,m]-pred,lw=.8,color='#059669');axs[2,col].set(ylabel='Fit residual (°C)',xlabel='Time within final three complete cycles (s)',title=f'RMS={info["sinusoidal_residual_rms_C"]:.3f} °C; RMS/B={info["residual_rms_over_amplitude"]:.1%}')
        for ax in axs[:,col]:ax.set_xlim(0,300);ax.grid(alpha=.2)
    fig.suptitle('Module 8 Stage 2 / S18.4 — measured 100 s comparison\nUb differs by 10× for safety; mean temperature also differs. Polarity alone is not isolated.',fontsize=14)
    save(fig,'m08_stage2_s18_4_measured_100s_comparison')


def simulation_table():
    sims=[];rows=[]
    for path in sorted((MODULE/'config/simulation').glob('s18_3_*.json')):
        setup=load_setup(path);run=Simulation(setup);run.advance(run.step_count);m=run.metrics();assert run.finished
        t,T,u=run.arrays();w=2*np.pi/setup.period_s;chi_avg=(setup.chi_h_C_per_pwm+setup.chi_c_C_per_pwm)/2
        theory={'mean_minus_room_C':setup.ub_pwm*(setup.chi_h_C_per_pwm-setup.chi_c_C_per_pwm)/np.pi,
            'fundamental_amplitude_C':chi_avg*setup.ub_pwm/np.hypot(1,w*setup.thermal_time_constant_s),
            'phase_lag_deg':np.degrees(np.arctan(w*setup.thermal_time_constant_s))}
        assert abs(m['mean_minus_room_C']-theory['mean_minus_room_C'])<.004
        assert abs(m['fundamental_amplitude_C']-theory['fundamental_amplitude_C'])<.006
        assert abs(m['phase_lag_deg']-theory['phase_lag_deg'])<.1
        stem='m08_sim_'+setup.case_id;csv_path=SIM/(stem+'.csv')
        with csv_path.open('w',newline='') as f:
            writer=csv.writer(f);writer.writerow(['time_s','simulated_tec_C','input_pwm','previous_step_applied_pwm','previous_step_saturated']);writer.writerows(run.rows)
        exact=equal_chi_solution(setup,t);error=None if exact is None else float(np.max(abs(T-exact)))
        if error is not None:assert error<.01
        write_json(SIM/(stem+'.json'),{'kind':'mathematical_simulation_not_measurement','setup':asdict(setup),'setup_file':str(path.relative_to(ROOT)),
            'setup_sha256':sha(path.read_bytes()),'copied_module6_solver_sha256':sha(SOURCE.read_bytes()),
            'adapter_sha256':sha((SOURCE.parent/'periodic_model.py').read_bytes()),'csv':str(csv_path.relative_to(ROOT)),
            'csv_sha256':sha(csv_path.read_bytes()),'metrics':m,'independent_fourier_prediction':theory,
            'maximum_equal_chi_time_solution_error_C':error,
            'normalization':'H=1 W/K is arbitrary. C=H*tau and P_u=H*chi preserve the measured-form one-lump ODE; these are not separately measured heat-loss/capacitance values.'})
        rows.append({'case':setup.case_id,'period_s':setup.period_s,'chi_c_C_per_pwm':setup.chi_c_C_per_pwm,
            **{k:m[k] for k in ('mean_minus_room_C','fundamental_amplitude_C','phase_lag_deg','sinusoidal_residual_rms_C','cycle_mean_span_C','cycle_amplitude_span_fraction','cycle_phase_span_rad')},
            'duration_s':setup.duration_s,'dt_s':setup.dt_s,'retained_cycles':5})
        sims.append((setup,run));print('Simulated',setup.case_id,flush=True)
    with (OUT/'m08_stage2_s18_3_simulation_table.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    # Match the five columns in the course worksheet; retain full precision in
    # the companion diagnostics table above.
    with (OUT/'m08_stage2_s18_3_filled_table.csv').open('w',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['Period (s)','chi_c (C/PWM)','Mean minus room (C)','Fundamental amplitude (C)','Phase lag (deg)'])
        for r in rows:writer.writerow([r['period_s'],r['chi_c_C_per_pwm'],r['mean_minus_room_C'],r['fundamental_amplitude_C'],r['phase_lag_deg']])
    fig,axs=plt.subplots(3,2,figsize=(12,10),layout='constrained')
    for row,P in enumerate((100,200,300)):
        for setup,run in sims:
            if setup.period_s!=P:continue
            t,T,u=run.arrays();first=t<=2*P;last=(t>=8*P)&(t<=10*P)
            color='#2563eb' if setup.chi_c_C_per_pwm==.23 else '#d97706';label=f'χc={setup.chi_c_C_per_pwm:.2f}'
            axs[row,0].plot(t[first],T[first],lw=1,color=color,label=label)
            axs[row,1].plot(t[last]-8*P,T[last],lw=1,color=color,label=label)
            exact=equal_chi_solution(setup,t)
            if exact is not None:
                axs[row,0].plot(t[first],exact[first],'--',lw=.7,color='black',label='Equal-χ analytical')
                axs[row,1].plot(t[last]-8*P,exact[last],'--',lw=.7,color='black')
        for col in range(2):axs[row,col].set(ylabel='Simulated TEC (°C)',xlabel='Model time (s)' if col==0 else 'Time within cycles 9–10 (s)',title=f'{P} s | '+('startup' if col==0 else 'late response'));axs[row,col].grid(alpha=.2)
        axs[row,0].legend(fontsize=8,ncol=3)
    fig.suptitle('Module 8 Stage 2 / S18.3 — six one-lump SIMULATIONS\nRoom = initial = 22°C; τth=80 s; χh=0.46 °C/PWM; Ua=0, Ub=50 PWM',fontsize=14)
    save(fig,'m08_stage2_s18_3_six_simulations')
    setup,run=sims[-1];t,T,u=run.arrays();exact=equal_chi_solution(setup,t)
    fig,axs=plt.subplots(2,2,figsize=(11,7),layout='constrained')
    for col,keep in enumerate((t<=600,t>=2700)):
        axs[0,col].plot(t[keep],T[keep],label='Forward Euler',lw=1.4)
        axs[0,col].plot(t[keep],exact[keep],'--',label='Complete analytical solution',lw=1.1)
        axs[1,col].plot(t[keep],T[keep]-exact[keep],lw=1);axs[1,col].set(ylabel='Numerical − analytical (°C)',xlabel='Model time (s)')
        axs[0,col].set(title='Startup' if col==0 else 'Final complete cycle',ylabel='Temperature (°C)');axs[0,col].legend(fontsize=8)
        for ax in axs[:,col]:ax.grid(alpha=.2)
    fig.suptitle('S18.3 derivation check — equal χ, period 300 s\nComplete transient solution; dt=0.05 s; initial T=22°C',fontsize=14)
    save(fig,'m08_stage2_s18_3_analytical_check')
    return rows


def documentation(simrows,runs):
    lines=['# Module 8 Stage 2 — setups, completed simulation table and measured plots','',
        'The six-row table below contains mathematical simulations, not laboratory measurements. The Module 6 solver was copied without changes; the Module 8 adapter supplies sinusoidal raw PWM. Run the GUI with `../run_simulation.command`.','',
        'Common simulation setup: one-lump process, raw open-loop sine, room = initial = 22 °C, thermal time constant = 80 s, χh = 0.46 °C/PWM, Ua = 0, Ub = 50 PWM, dt = 0.05 s and PWM limit = 255. There is no feedback or cooling compensation. Kp/Ki and anti-windup are inactive in this raw mode. The limit is a simulation setting, not a proposed hardware limit. H = 1 is an arbitrary normalization, with C = Hτ and P_u = Hχ.','',
        '## Completed S18.3 simulation table','',
        '| Case | Period (s) | χc (°C/PWM) | Mean − room (°C) | Fundamental amplitude (°C) | Phase lag vs PWM (°) | Simulated duration (s) |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for i,r in enumerate(simrows,1):lines.append(f'| {i} | {r["period_s"]:g} | {r["chi_c_C_per_pwm"]:.2f} | {r["mean_minus_room_C"]:.3f} | {r["fundamental_amplitude_C"]:.3f} | {r["phase_lag_deg"]:.2f} | {r["duration_s"]:g} |')
    lines+=['', 'Values are numerical first-harmonic fits to the final five complete simulated cycles of each ten-cycle run. The CSV also retains residual RMS and per-cycle spans. Duration is a budget, not a settling definition. Independent Fourier predictions agree within 0.004 °C in mean, 0.006 °C in amplitude and 0.1° in phase; the small remaining differences include forward-Euler error and finite startup decay.','',
        'At fixed PWM amplitude, a longer period increases temperature amplitude and reduces phase lag. Unequal heating/cooling susceptibility raises the mean above room temperature and adds waveform distortion. The exact steady fundamental uses χavg=(χh+χc)/2: B=χavg·Ub/sqrt(1+(ωτ)²), lag=atan(ωτ), and mean−room=Ub(χh−χc)/π for Ua=0. These are checks on this piecewise-linear model, not measured material parameters.','',
        '## Analytical startup check','',
        'For χh=χc=χ and Ua=0, let a=χUb/[1+(ωτ)²], b=−aωτ. Then T(t)=Troom+a sin(ωt)+b cos(ωt)+C exp(−t/τ), with C=Tinitial−Troom−b. At t=0 this gives Tinitial. Substitution yields τ d(T−Troom)/dt+(T−Troom)=χUb sin(ωt): the homogeneous term cancels and the sine/cosine coefficients satisfy a−ωτb=χUb and b+ωτa=0. The dashed overlay retains this startup term.','',
        '## Measured Stage 2 records','',
        '| Mode | Period (s) | Ua / Ub (PWM) | Fit cycles | Initial TEC reference (°C) | TEC mean (°C) | Mean − reference (°C) | Fundamental amplitude (°C) | Lag vs applied PWM (°) | Fit RMS (°C) |',
        '|---|---:|---|---|---:|---:|---:|---:|---:|---:|']
    for key in (300,200,100,'positive'):
        r=runs[key]['info'];cs=r['selected_complete_cycles'];lines.append(f'| {r["mode"]} | {r["period_s"]:g} | {r["ua_pwm"]:g} / {r["ub_pwm"]:g} | {cs[0]}–{cs[-1]} | {r["room_reference_C"]:.3f} | {r["mean_tec_C"]:.3f} | {r["mean_minus_room_reference_C"]:.3f} | {r["fundamental_amplitude_C"]:.3f} | {r["phase_lag_vs_applied_pwm_deg"]:.2f} | {r["sinusoidal_residual_rms_C"]:.3f} |')
    lines+=['',
        'Measured plots retain the RUNNING history including startup; only time origins are shifted to each STEP event. Shading identifies descriptive fitting intervals. The 300 s record contains only two complete cycles plus a partial tail; its fit includes startup and is diagnostic. The other records use their final three complete cycles, with per-cycle spans saved for review. These figures do not certify settling.','',
        'The 100 s positive-only trial uses Ua=32, Ub=5 PWM, whereas its zero-centered baseline uses Ua=0, Ub=50 PWM. The amplitude was reduced for safety and the mean operating temperature changed. Absolute residual reductions therefore cannot isolate polarity reversal. Inspect RMS/B as well as absolute residuals; do not equate a smaller absolute residual with a uniquely identified mechanism. The positive-only measured mean is reported as measured, not relabelled 40 °C.','',
        'The measured table uses each acquisition’s first finite TEC reading as the room reference. Independent air temperature and drift are unknown. The six teaching simulations use the course-prescribed 22 °C.','',
        '## Files','',
        '- [Completed five-column worksheet (CSV)](../data/processed/stage2/m08_stage2_s18_3_filled_table.csv)',
        '- [Simulation fit diagnostics (CSV)](../data/processed/stage2/m08_stage2_s18_3_simulation_table.csv)',
        '- [Measured metrics (CSV)](../data/processed/stage2/m08_stage2_measured_metrics.csv)',
        '- [Zero-centered measured curves](../figures/stage2/m08_stage2_s18_3_measured_zero_pwm.png)',
        '- [100 s measured zero/positive comparison](../figures/stage2/m08_stage2_s18_4_measured_100s_comparison.png)',
        '- [Six simulation curves](../figures/stage2/m08_stage2_s18_3_six_simulations.png)',
        '- [Analytical/numerical comparison](../figures/stage2/m08_stage2_s18_3_analytical_check.png)','',
        'Each figure has a PDF counterpart. Full simulated startup histories and setup/hash receipts are in `../data/simulation/s18_3/`. Original measured CSVs are unchanged.','',
        'Reproduce all plots and tables: `.venv/bin/python Module_8/python/analysis/stage2_raw_pwm.py` from the repository root.','',
        '[Course Stage 2 instructions](https://sethfraden.github.io/Phys39F26-course/labs/lab-09/#stage-2-explore-uncompensated-sinusoidal-pwm). The focused Stage 3 P/PI comparison uses a separate six-sensor rod simulator; the copied one-lump simulator is not a substitute for it. Codex generated the working figures and calculations; review the evidence and explain the model in your own account.','']
    (MODULE/'docs/stage2_results.md').write_text('\n'.join(lines))


def main():
    for folder in (FIG,OUT,SIM):folder.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    runs={key:measured(name) for key,name in RAW.items()};measured_figures(runs)
    write_json(OUT/'m08_stage2_measured_sources.json',{'records':[r['info'] for r in runs.values()],
        'analysis_sha256':sha(Path(__file__).read_bytes()),'raw_files_unchanged':True})
    metrics=[{k:v for k,v in r['info'].items() if k not in ('selected_complete_cycles',)} for r in runs.values()]
    with (OUT/'m08_stage2_measured_metrics.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(metrics[0]));writer.writeheader();writer.writerows(metrics)
    simrows=simulation_table();documentation(simrows,runs)
    for r in runs.values():assert sha(r['path'].read_bytes())==r['info']['source_sha256']
    print('Saved Stage 2 figures, simulation table and working notes.',flush=True)


if __name__=='__main__':main()
