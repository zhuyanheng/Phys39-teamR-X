"""Offline Angstrom analysis of explicit settled intervals; never accesses serial.

Run: python angstrom_fit.py --config Module_8/config/analysis_plan.json
Model T=a+C*cos(w*t)+S*sin(w*t); phase=atan2(-S,C). Downstream phase
is increasingly negative. q=-slope(log B), q_prime=-slope(phase).
Cycle-to-cycle covariance supplies conditional fit uncertainty; sensor position,
scan timing, material constants and contact errors remain separate systematics.
"""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
MODULE=ROOT/'Module_8'
CHANNELS=('tec_C','rod1_C','rod2_C','rod3_C','rod4_C','rod5_C')


def number(x):
    try:return float(x)
    except (ValueError,TypeError):return math.nan


def portable(path):
    try:return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:return str(Path(path).resolve())


def safe(value):
    if isinstance(value,dict):return {k:safe(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,np.ndarray)):return [safe(v) for v in value]
    if isinstance(value,(float,np.floating)):return float(value) if np.isfinite(value) else None
    if isinstance(value,np.integer):return int(value)
    if isinstance(value,np.bool_):return bool(value)
    return value


def fit_trace(t,y,period):
    t=np.asarray(t,float);y=np.asarray(y,float)
    good=np.isfinite(t)&np.isfinite(y)
    if good.sum()<8:raise ValueError('At least eight finite samples per fitted trace/cycle are needed')
    t=t[good];y=y[good];w=2*np.pi/period
    X=np.column_stack([np.ones(len(t)),np.cos(w*t),np.sin(w*t)])
    coef,_,rank,_=np.linalg.lstsq(X,y,rcond=None)
    if rank!=3:raise ValueError('Sinusoid fit is rank deficient')
    residual=y-X@coef
    covariance=np.linalg.inv(X.T@X)*(residual@residual)/(len(t)-3)
    a,c,s=coef;B=float(np.hypot(c,s));phi=float(np.arctan2(-s,c))
    if B<=1e-12:raise ValueError('No measurable sinusoidal amplitude')
    j=np.array([0,c/B,s/B]);jphi=np.array([0,s/B**2,-c/B**2])
    return {'mean_C':float(a),'amplitude_C':B,'phase_rad':phi,
            'amplitude_se_C':float(np.sqrt(max(0,j@covariance@j))),
            'phase_se_rad':float(np.sqrt(max(0,jphi@covariance@jphi))),
            'rms_residual_C':float(np.sqrt(np.mean(residual**2))),
            'residuals_C':residual,'coefficients':coef,'sample_count':len(t)}


def spatial(xs,fits):
    xs=np.asarray(xs,float)
    phase=np.unwrap([f['phase_rad'] for f in fits])
    X=np.column_stack([np.ones(len(xs)),xs])
    logamp=np.log([f['amplitude_C'] for f in fits])
    la=np.linalg.lstsq(X,logamp,rcond=None)[0]
    ph=np.linalg.lstsq(X,phase,rcond=None)[0]
    return {'q_per_m':float(-la[1]),'q_prime_per_m':float(-ph[1]),
            'log_amplitude_intercept':float(la[0]),'phase_intercept_rad':float(ph[0]),
            'unwrapped_phases_rad':phase,'log_amplitude_residuals':logamp-X@la,
            'phase_residuals_rad':phase-X@ph}


def infer(q,qp,period,covariance=None):
    if q<=0 or qp<=0:raise ValueError('Amplitude attenuation and downstream phase lag must both be positive')
    w=2*np.pi/period;kappa=w/(2*q*qp);nu=kappa*(q*q-qp*qp)
    result={'kappa_m2_s':kappa,'nu_per_s':nu,'m_squared_per_m2':q*q-qp*qp,
            'physical_positive_loss':bool(q>qp),'kappa_se_m2_s':None,'nu_se_per_s':None}
    if covariance is not None:
        cov=np.asarray(covariance,float)
        jk=np.array([-kappa/q,-kappa/qp])
        jn=np.array([w/2*(1/qp+qp/q**2),-w/2*(q/qp**2+1/q)])
        result.update(kappa_se_m2_s=float(np.sqrt(max(0,jk@cov@jk))),
                      nu_se_per_s=float(np.sqrt(max(0,jn@cov@jn))))
    return result


def finite_error(q,qp,length,x):
    s=complex(q,qp)
    semi=np.exp(-s*x)
    finite=semi*(1+np.exp(-2*s*(length-x)))/(1+np.exp(-2*s*length))
    return float(abs(finite-semi)/abs(finite))


def validate_map(geometry):
    xs=geometry.get('x_m');length=geometry.get('analysis_length_m');d=geometry.get('diameter_m')
    if xs is None or length is None:raise ValueError('Measure/save Module 8 x_m and analysis_length_m before analysis; inherited reference coordinates are not selected automatically')
    xs=np.asarray(xs,float)
    if len(xs)!=5 or not np.isfinite(xs).all() or xs[0]!=0 or np.any(np.diff(xs)<=0):raise ValueError('Need five strictly increasing finite rod coordinates starting at zero')
    if not np.isfinite(length) or length<=xs[-1] or not d or not np.isfinite(d) or d<=0:raise ValueError('Invalid rod length or diameter')
    return xs,float(length),float(d)


def analyse_interval(rows,geometry,plan):
    xs,length,d=validate_map(geometry)
    period=number(plan.get('period_s'));start=number(plan.get('start_s'));end=number(plan.get('end_s'))
    if not all(np.isfinite([period,start,end])) or period<100 or end<=start:raise ValueError('Specify finite start/end and a period >=100 s')
    cycles=int(math.floor((end-start)/period+1e-9))
    if cycles<5:raise ValueError('Retain at least five complete cycles after settling')
    stop=start+cycles*period
    chosen=[r for r in rows if start<=number(r.get('time_s'))<stop]
    t=np.array([number(r.get('time_s')) for r in chosen])
    if len(t)<40 or not np.isfinite(t).all() or np.any(np.diff(t)<=0):raise ValueError('Too few samples, nonfinite time or clock reset/duplicate inside interval')
    dt=float(np.median(np.diff(t)))
    if t[0]-start>2*dt or stop-t[-1]>2*dt or np.max(np.diff(t))>max(3*dt,period/20):raise ValueError('Incomplete cycle coverage or large acquisition gap')
    for key in ('period_s','step','run_id','plan_sha256','control_mode'):
        values={r.get(key) for r in chosen if r.get(key) not in ('',None)}
        if len(values)>1:raise ValueError('Interval crosses a '+key+' change')
    recorded={number(r.get('period_s')) for r in chosen if np.isfinite(number(r.get('period_s')))}
    if recorded and any(abs(p-period)>1e-6 for p in recorded):raise ValueError('Requested analysis period differs from recorded firmware period')
    if any(r.get('safety') not in ('',None,'OK') for r in chosen):raise ValueError('Safety event inside accepted interval')
    if any(r.get('run_state') not in ('',None,'RUNNING') for r in chosen):raise ValueError('Accepted interval includes a stopped or faulted schedule')
    settings=plan.get('settling',{})
    required=('max_mean_change_C','max_amplitude_change_fraction','max_phase_change_rad')
    if any(not np.isfinite(number(settings.get(k))) or number(settings[k])<=0 for k in required):raise ValueError('Provide positive quantitative settling tolerances for mean, amplitude and phase')
    requested=plan.get('rod_sensors',[1,2,3,4,5])
    if not isinstance(requested,list) or len(requested)<3 or len(set(requested))!=len(requested) or 1 not in requested or any(i not in range(1,6) for i in requested):raise ValueError('Select at least three distinct rod sensors including T1')
    requested=sorted(requested)
    fits={};cycle_fits={};warnings=[]
    offsets=geometry.get('sample_time_offsets_s',{})
    t_rel=t-start
    for ch in CHANNELS:
        y=np.array([number(r.get(ch)) for r in chosen])
        if not np.isfinite(y).all():
            if ch in ['rod%d_C'%i for i in requested]:raise ValueError('Missing values in retained '+ch)
            warnings.append(ch+' excluded: missing values');continue
        tt=t_rel+number(offsets.get(ch,0))
        fits[ch]=fit_trace(tt,y,period)
        cycle_fits[ch]=[fit_trace(tt[(t_rel>=i*period)&(t_rel<(i+1)*period)],y[(t_rel>=i*period)&(t_rel<(i+1)*period)],period) for i in range(cycles)]
    selected=['rod%d_C'%i for i in requested]
    settled={};all_settled=True
    for ch in selected:
        cf=cycle_fits[ch]
        means=np.array([f['mean_C'] for f in cf]);amp=np.array([f['amplitude_C'] for f in cf]);phi=np.unwrap([f['phase_rad'] for f in cf])
        changes={'mean_change_C':float(np.max(np.abs(np.diff(means)))),
                 'amplitude_change_fraction':float(np.max(np.abs(np.diff(amp)))/np.mean(amp)),
                 'phase_change_rad':float(np.max(np.abs(np.diff(phi)))),
                 'mean_span_C':float(np.ptp(means)),
                 'amplitude_span_fraction':float(np.ptp(amp)/np.mean(amp)),
                 'phase_span_rad':float(np.ptp(phi))}
        # Adjacent changes alone can conceal a persistent drift across cycles.
        passed=changes['mean_span_C']<=settings['max_mean_change_C'] and changes['amplitude_span_fraction']<=settings['max_amplitude_change_fraction'] and changes['phase_span_rad']<=settings['max_phase_change_rad']
        settled[ch]={**changes,'passes':bool(passed)};all_settled &= passed
        f=fits[ch]
        f['cycle_amplitude_se_C']=float(np.std(amp,ddof=1)/np.sqrt(cycles))
        f['cycle_phase_se_rad']=float(np.std(phi,ddof=1)/np.sqrt(cycles))
        f['cycle_mean_se_C']=float(np.std(means,ddof=1)/np.sqrt(cycles))
        snr=f['amplitude_C']/max(f['amplitude_se_C'],f['cycle_amplitude_se_C'],1e-12)
        f['amplitude_signal_to_fit_error']=snr
        if snr<plan.get('minimum_amplitude_snr',5):raise ValueError(ch+' has inadequate amplitude signal-to-fit-error')
    if not all_settled:warnings.append('Selected interval fails supplied cycle-stationarity tolerances; diagnostic only')
    retained_x=[xs[i-1] for i in requested]
    sf=spatial(retained_x,[fits[ch] for ch in selected])
    repetitions=[spatial(retained_x,[cycle_fits[ch][j] for ch in selected]) for j in range(cycles)]
    params=np.array([[r['q_per_m'],r['q_prime_per_m']] for r in repetitions])
    cov=np.cov(params,rowvar=False,ddof=1)/cycles
    physical=infer(sf['q_per_m'],sf['q_prime_per_m'],period,cov)
    q,qp=sf['q_per_m'],sf['q_prime_per_m']
    eps=[{'sensor':ch,'x_m':float(x),'complex_relative_error':finite_error(q,qp,length,x)} for ch,x in zip(selected,retained_x)]
    tolerance=number(plan.get('finite_error_tolerance',.05))
    if not np.isfinite(tolerance) or tolerance<=0:raise ValueError('Finite error tolerance must be positive')
    if max(e['complex_relative_error'] for e in eps)>tolerance:warnings.append('Semi-infinite approximation exceeds selected complex-response tolerance; finite periodic model needed for inference')
    if not physical['physical_positive_loss']:warnings.append('q <= q_prime: nonpositive inferred lateral loss; investigate uncertainty and model')
    bi=physical['m_squared_per_m2']*(d/4)**2
    if bi>=.1:warnings.append('Transverse Biot is not small: reject 1D interpretation')
    # Full solution reconstructed using measured T1 coefficient and each fitted
    # mean; the mean is measured here, not imposed from a fitted ambient.
    base=fits['rod1_C'];z0=complex(base['coefficients'][1],-base['coefficients'][2])
    recon=[]
    for ch,x in zip(selected,retained_x):
        z=z0*np.exp(-complex(q,qp)*x)
        model=fits[ch]['mean_C']+np.real(z*np.exp(1j*2*np.pi*t_rel/period))
        observed=np.array([number(r[ch]) for r in chosen])
        recon.append({'sensor':ch,'model_rms_C':float(np.sqrt(np.mean((model-observed)**2)))})
    material=plan.get('material',{});rho=number(material.get('density_kg_m3'));c=number(material.get('specific_heat_J_kgK'))
    physical.update(k_W_mK=None,h_W_m2K=None,k_fit_se_W_mK=None,h_fit_se_W_m2K=None)
    if np.isfinite(rho) and np.isfinite(c) and rho>0 and c>0:
        if not material.get('source'):raise ValueError('Record a source for density and specific heat')
        physical.update(k_W_mK=rho*c*physical['kappa_m2_s'],h_W_m2K=rho*c*d/4*physical['nu_per_s'],
            k_fit_se_W_mK=rho*c*physical['kappa_se_m2_s'],h_fit_se_W_m2K=rho*c*d/4*physical['nu_se_per_s'])
    else:warnings.append('Density/specific heat not supplied: k and h remain uncomputed')
    warnings.append('Errors are conditional cycle-repeat fit errors; material/geometry, sensor bias, timing and contact systematic errors are not included')
    warnings.append('Spatial phase uses nearest-branch unwrapping; verify alias choice with geometry, residuals and other periods')
    if not offsets:warnings.append('No channel scan-time correction supplied; consider sequential scan timing in phase uncertainty')
    waveform={}
    for ch in ('tec_C','rod1_C'):
        if ch in fits:waveform[ch]={k:fits[ch][k] for k in ('mean_C','amplitude_C','phase_rad','rms_residual_C')}
    boundary_relative_rms=fits['rod1_C']['rms_residual_C']/fits['rod1_C']['amplitude_C']
    boundary_ok=boundary_relative_rms<=plan.get('max_boundary_relative_rms',.1)
    if not boundary_ok:warnings.append('Measured T1 boundary has excessive first-harmonic residual; inspect waveform distortion')
    requested_values=np.array([number(r.get('setpoint_C')) for r in chosen])
    if np.isfinite(requested_values).all():
        f=fit_trace(t_rel,requested_values,period);waveform['setpoint_C']={k:f[k] for k in ('mean_C','amplitude_C','phase_rad','rms_residual_C')}
    return safe({'label':plan.get('label','interval'),'start_s':start,'end_s':stop,'excluded_requested_tail_s':end-stop,'period_s':period,
        'complete_cycles':cycles,'samples':len(chosen),'largest_gap_s':float(np.max(np.diff(t))),
        'selected_rod_sensors':requested,'positions_m':retained_x,'geometry':geometry,'settling_tolerances':settings,
        'cycle_checks':settled,'cycle_stationarity_passed':bool(all_settled),'channel_fits':fits,
        'spatial_fit':sf,'q_qprime_covariance_of_mean':cov,'transport':physical,'finite_length_errors':eps,
        'finite_error_tolerance':tolerance,'bi_perp':bi,'reconstruction_rms':recon,'boundary_waveforms':waveform,
        'boundary_relative_rms':boundary_relative_rms,
        'material_inputs':material,'warnings':warnings,'status':'candidate' if all_settled and boundary_ok and q>qp and max(e['complex_relative_error'] for e in eps)<=tolerance and bi<.1 else 'diagnostic_only'})


def analyse_plan(plan_path):
    path=Path(plan_path);plan=json.loads(path.read_text())
    raw=ROOT/plan['raw'];map_path=ROOT/plan.get('sensor_map','Module_8/config/sensor_map.json')
    raw_bytes=raw.read_bytes();digest=hashlib.sha256(raw_bytes).hexdigest()
    with raw.open(newline='') as stream:
        reader=csv.DictReader(stream)
        if not {'period_s','control_mode','run_state','seq','phase_rad'}.issubset(set(reader.fieldnames or [])):
            raise ValueError('Module 8 periodic-acquisition schema required; Module 7 constant-setpoint files are not periodic data')
        rows=[r for r in reader if r.get('event')=='measurement']
    geometry=json.loads(map_path.read_text());validate_map(geometry)
    if not plan.get('intervals'):raise ValueError('Select actual settled intervals in the analysis plan')
    results=[analyse_interval(rows,geometry,p) for p in plan['intervals']]
    consistency=[]
    for i,a in enumerate(results):
        for b in results[i+1:]:
            if a['period_s']==b['period_s']:continue
            va,vb=a['transport'],b['transport'];se=math.hypot(va['kappa_se_m2_s'],vb['kappa_se_m2_s'])
            consistency.append({'first':a['label'],'second':b['label'],'kappa_difference_m2_s':va['kappa_m2_s']-vb['kappa_m2_s'],'difference_over_combined_fit_se':(va['kappa_m2_s']-vb['kappa_m2_s'])/se if se else None})
    assert hashlib.sha256(raw.read_bytes()).hexdigest()==digest,'Raw changed during analysis'
    code_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    out=safe({'kind':'measured_periodic_analysis','source':portable(raw),'source_sha256':digest,'raw_unchanged':True,
        'analysis_plan':portable(path),'plan_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'analysis_source_sha256':code_sha,'sensor_map_sha256':hashlib.sha256(map_path.read_bytes()).hexdigest(),
        'intervals':results,'frequency_consistency':consistency,'distinct_candidate_periods':len({r['period_s'] for r in results if r['status']=='candidate'}),
        'production_record_complete':len({r['period_s'] for r in results if r['status']=='candidate'})>=2})
    folder=MODULE/'data/processed';folder.mkdir(parents=True,exist_ok=True)
    target=folder/(path.stem+'_angstrom.json');target.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    return target,out


def make_figure(result,path):
    os.environ.setdefault('MPLCONFIGDIR','/private/tmp/module8-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
    xs=np.array(result['positions_m']);channels=['rod%d_C'%i for i in result['selected_rod_sensors']]
    fits=[result['channel_fits'][ch] for ch in channels];sp=result['spatial_fit']
    logB=np.log([f['amplitude_C'] for f in fits]);phi=sp['unwrapped_phases_rad']
    ax[0,0].plot(xs,logB,'ko');ax[0,0].plot(xs,sp['log_amplitude_intercept']-sp['q_per_m']*xs)
    ax[0,1].plot(xs,phi,'ko');ax[0,1].plot(xs,sp['phase_intercept_rad']-sp['q_prime_per_m']*xs)
    ax[1,0].plot(xs,sp['log_amplitude_residuals'],'o-');ax[1,1].plot(xs,sp['phase_residuals_rad'],'o-')
    for axes,label in zip(ax.flat,['ln amplitude (C)','Unwrapped phase (rad)','Log-amplitude residual','Phase residual (rad)']):
        axes.set_xlabel('x (m)');axes.set_ylabel(label);axes.grid(alpha=.2)
    fig.suptitle(f"{result['label']}: period {result['period_s']:g} s | {result['status']}")
    Path(path).parent.mkdir(parents=True,exist_ok=True);fig.savefig(path,dpi=160);plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True)
    args=p.parse_args()
    try:
        target,result=analyse_plan(args.config)
        for i,r in enumerate(result['intervals']):make_figure(r,MODULE/'figures'/(args.config.stem+f'_interval_{i+1}.png'))
        print(target)
        print('Candidate distinct periods:',result['distinct_candidate_periods'])
        return 0
    except (ValueError,KeyError,OSError) as exc:
        print('Analysis not completed:',exc);return 2

if __name__=='__main__':raise SystemExit(main())
