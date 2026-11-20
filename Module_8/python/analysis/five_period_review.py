"""Reproducible offline review of the five PI records; never opens a device.

Run from the repository: .venv/bin/python Module_8/python/analysis/five_period_review.py
Sources are frozen on first run as complete-line byte prefixes. Reruns reuse those
snapshots, verify original prefixes, and leave all raw data untouched.
"""
import csv
import hashlib
import io
import itertools
import json
import os
from pathlib import Path
import numpy as np
os.environ.setdefault('MPLCONFIGDIR','/tmp/module8_matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from angstrom_fit import (ROOT, MODULE, CHANNELS, fit_trace, analyse_interval,
                          safe, spatial, finite_response, infer)
from initial_tec_reference import initial_tec_reference

OUT=MODULE/'data/processed/five_period_review'
FIG=MODULE/'figures/five_period_review'
SOURCES={100:'m08_pi_p100s_20261116_104519_503645.csv',
         200:'m08_pi_p200s_20261109_095722_597413.csv',
         300:'m08_pi_p300s_20261116_111157_767223.csv',
         400:'m08_pi_p400s_20261118_092100_447310.csv',
         500:'m08_pi_p500s_20261109_104354_009745.csv'}
# Retain the same three near-base rods for every frequency, before fitting.
# These are the existing planning limits, not instructor-prescribed constants.
TOL={'max_mean_change_C':.1,'max_amplitude_change_fraction':.05,'max_phase_change_rad':.1}
RODS=CHANNELS[1:4]
COLORS=['#64748b','#2563eb','#d97706','#059669','#9333ea','#db2777']


def digest(b):return hashlib.sha256(b).hexdigest()


def write_json(path,obj):path.write_text(json.dumps(safe(obj),indent=2,allow_nan=False)+'\n')


def freeze_sources():
    folder=OUT/'snapshots';folder.mkdir(parents=True,exist_ok=True)
    manifest_path=OUT/'m08_pi_five_period_sources.json'
    if manifest_path.exists():manifest=json.loads(manifest_path.read_text())
    else:
        manifest={}
        for period,filename in SOURCES.items():
            raw=MODULE/'data/raw'/filename
            b=raw.read_bytes();b=b[:b.rfind(b'\n')+1]
            dest=folder/raw.name;dest.write_bytes(b)
            plan=raw.with_name(raw.stem+'_plan_01.json')
            plan_dest=folder/plan.name;plan_dest.write_bytes(plan.read_bytes())
            manifest[str(period)]={'raw':str(raw.relative_to(ROOT)),
                'snapshot':str(dest.relative_to(ROOT)),'prefix_bytes':len(b),'sha256':digest(b),
                'plan_snapshot':str(plan_dest.relative_to(ROOT)),'plan_sha256':digest(plan_dest.read_bytes())}
        map_path=MODULE/'config/sensor_map.json'
        (folder/'sensor_map.json').write_bytes(map_path.read_bytes())
        write_json(manifest_path,manifest)
    for entry in manifest.values():
        snap=(ROOT/entry['snapshot']).read_bytes()
        assert digest(snap)==entry['sha256']
        assert digest((ROOT/entry['raw']).read_bytes()[:entry['prefix_bytes']])==entry['sha256']
        assert digest((ROOT/entry['plan_snapshot']).read_bytes())==entry['plan_sha256']
    geometry=json.loads((folder/'sensor_map.json').read_text())
    current=json.loads((MODULE/'config/sensor_map.json').read_text())
    for key in ('x_m','analysis_length_m','diameter_m'):
        if current[key]!=geometry[key]:
            raise ValueError(f'Frozen and current geometry differ for {key}')
    for key in ('ruler_segment_error_bound_m','ruler_error_source','note'):
        geometry[key]=current[key]
    return manifest,geometry


def unpack(entry,period):
    rows=list(csv.DictReader(io.StringIO((ROOT/entry['snapshot']).read_text())))
    active=[r for r in rows if r['event']=='measurement' and r['run_state']=='RUNNING']
    assert active and {r['control_mode'] for r in active}=={'PI'}
    assert {float(r['period_s']) for r in active}=={float(period)}
    assert len({(r['run_id'],r['step'],r['plan_sha256']) for r in active})==1
    events=[r for r in rows if r.get('note','').startswith('#EVENT,STEP,') and r['run_id']==active[0]['run_id']]
    assert len(events)==1
    start=int(events[0]['note'].split(',')[2])/1000
    plan=json.loads((ROOT/entry['plan_snapshot']).read_text())
    duration=float(plan['steps'][0]['duration_s'])
    t=np.array([float(r['time_s']) for r in active]);dt=float(np.median(np.diff(t)))
    # Coverage up to within a report interval of a planned cycle end counts;
    # do not discard the last completed cycle because DONE has no RUNNING sample.
    count=int(np.floor(min(duration,t[-1]-start+dt*1.1)/period+1e-9))
    seq=np.array([int(r['seq']) for r in active])
    audit={'start_device_s':start,'start_host_time':events[0]['host_time'],
        'last_active_host_time':active[-1]['host_time'],'complete_cycles':count,
        'active_samples':len(active),'median_dt_s':dt,'largest_dt_s':float(np.max(np.diff(t))),
        'seq_missing':int(np.maximum(np.diff(seq)-1,0).sum()),
        'duplicate_or_reversed_time':int(np.sum(np.diff(t)<=0)),
        'fault_samples':sum(r['fault_code']!='NONE' or r['safety']!='OK' for r in active),
        'nonfinite_temperature_values':sum(not np.isfinite(float(r[ch])) for r in active for ch in CHANNELS),
        'max_tec_C':max(float(r['tec_C']) for r in active),
        'latest_state':next(r for r in reversed(rows) if r['event']=='measurement')['run_state'],
        'settings':{key:sorted({r[key] for r in active}) for key in
                    ('Ta_C','Tb_C','Kp_pwm_per_C','Ki_pwm_per_C_s','pwm_limit','anti_windup')},
        'ambient_C':None,'room_reference':initial_tec_reference(rows)}
    cycles=[];fits={ch:[] for ch in CHANNELS}
    for i in range(count):
        a=start+i*period;b=a+period
        segment=[r for r in active if a<=float(r['time_s'])<b]
        tt=np.array([float(r['time_s'])-start for r in segment])
        assert len(tt)>8 and tt[0]-i*period<2*dt and b-(tt[-1]+start)<2*dt
        cycles.append({'cycle':i+1,'start_s':a,'end_s':b,'samples':len(segment),
                       'saturation_fraction':np.mean([r['saturated']=='1' for r in segment])})
        for ch in CHANNELS:fits[ch].append(fit_trace(tt,[float(r[ch]) for r in segment],period))
    return active,start,count,audit,cycles,fits


def windows(fits,count):
    result=[]
    for j in range(count-4):
        metrics={}
        for ch in RODS:
            series=fits[ch][j:j+5]
            metrics[ch]={'mean_span_C':np.ptp([f['mean_C'] for f in series]),
                'amplitude_span_fraction':np.ptp([f['amplitude_C'] for f in series])/np.mean([f['amplitude_C'] for f in series]),
                'phase_span_rad':np.ptp(np.unwrap([f['phase_rad'] for f in series]))}
        score=max(max(m['mean_span_C']/.1,m['amplitude_span_fraction']/.05,m['phase_span_rad']/.1) for m in metrics.values())
        result.append({'first_cycle':j+1,'last_cycle':j+5,'metrics':metrics,
                       'max_tolerance_ratio':score,'planning_gate_passed':score<=1})
    return result


def independent_complex_fit(xs,z,length,initial,finite=True):
    """Derivative-free grid refinement, independent of production Gauss-Newton."""
    xs=np.asarray(xs);target=z/z[0]
    def score(q,qp):
        s=q+1j*qp
        # Direct cosh is an independent evaluation of the finite solution.
        pred=np.cosh(s*(length-xs))/np.cosh(s*length) if finite else np.exp(-s*xs)
        return float(np.sum(abs(pred[1:]-target[1:])**2))
    p=np.array(initial,float);step=max(p)*.25
    for _ in range(160):
        candidates=[p+step*np.array(d) for d in itertools.product((-1,0,1),repeat=2)]
        candidates=[v for v in candidates if np.all(v>0)]
        best=min(candidates,key=lambda v:score(*v))
        if np.array_equal(best,p):step/=2
        else:p=best
        if step<1e-7:break
    return p,score(*p)


def supplements(active,start,period,result,geometry):
    a=result['start_s'];b=result['end_s'];rows=[r for r in active if a<=float(r['time_s'])<b]
    t=np.array([float(r['time_s'])-a for r in rows]);w=2*np.pi/period
    xs=np.array(geometry['x_m'][:3]);L=geometry['analysis_length_m']
    f=result['channel_fits'];z=np.array([f[ch]['amplitude_C']*np.exp(1j*f[ch]['phase_rad']) for ch in RODS])
    q=result['finite_periodic_fit']['q_per_m'];qp=result['finite_periodic_fit']['q_prime_per_m']
    independent,ssr=independent_complex_fit(xs,z,L,(q,qp))
    assert np.allclose(independent,[q,qp],rtol=2e-5,atol=2e-5)
    assert np.allclose(finite_response(q,qp,L,xs),np.cosh((q+1j*qp)*(L-xs))/np.cosh((q+1j*qp)*L),atol=1e-12)
    # Normal equations independently verify the harmonic least-squares solution.
    X=np.column_stack([np.ones(len(t)),np.cos(w*t),np.sin(w*t)])
    for ch in CHANNELS:
        coef=np.linalg.solve(X.T@X,X.T@np.array([float(r[ch]) for r in rows]))
        assert np.allclose(coef,f[ch]['coefficients'],atol=1e-9)
    semi,_=independent_complex_fit(xs,z,L,(q,qp),finite=False)
    comparable_semi=infer(*semi,period)
    # Sensitivity only: fit an explicit linear baseline to quantify drift leakage.
    Xtrend=np.column_stack([X,t-t.mean()]);trend_fits=[];slopes={}
    for ch in CHANNELS:
        y=np.array([float(r[ch]) for r in rows]);coef=np.linalg.lstsq(Xtrend,y,rcond=None)[0]
        slopes[ch]=coef[3]
        trend_fits.append({'amplitude_C':np.hypot(coef[1],coef[2]),'phase_rad':np.arctan2(-coef[2],coef[1])})
    trend_z=np.array([v['amplitude_C']*np.exp(1j*v['phase_rad']) for v in trend_fits[1:4]])
    trend_p,_=independent_complex_fit(xs,trend_z,L,(q,qp))
    # Each coordinate and L inherit the errors of the gaps used to build them.
    bound=geometry['ruler_segment_error_bound_m']
    scenarios=[]
    for errors in itertools.product((-bound,bound),repeat=5):
        offsets=np.r_[0.,np.cumsum(errors)]
        p,_=independent_complex_fit(xs+offsets[:3],z,L+offsets[-1],(q,qp))
        scenarios.append({'segment_errors_m':list(errors),**infer(*p,period)})
    response=z/z[0];pred=finite_response(q,qp,L,xs)
    phase_residual=np.angle(response/pred)
    amp_error=abs(response)/abs(pred)-1
    # Simple sensitivity to channel inclusion, never used to select a favorable result.
    subsets={}
    for ids in ((1,2,3,4),(1,2,3,4,5)):
        zz=np.array([f[f'rod{i}_C']['amplitude_C']*np.exp(1j*f[f'rod{i}_C']['phase_rad']) for i in ids])
        pp,_=independent_complex_fit(np.array(geometry['x_m'])[[i-1 for i in ids]],zz,L,(q,qp))
        subsets['T1-T'+str(ids[-1])]=infer(*pp,period)
    return safe({'independent_fit_q_qprime':independent,'independent_fit_ssr':ssr,
        'independent_harmonic_normal_equations_verified':True,
        'matched_objective_semi_infinite_transport':comparable_semi,
        'finite_tip_kappa_shift_fraction':result['transport']['kappa_m2_s']/comparable_semi['kappa_m2_s']-1,
        'linear_baseline_sensitivity':{'baseline_slopes_C_s':slopes,'transport':infer(*trend_p,period),
                                     'interpretation':'Sensitivity only; detrending is not proof of settled cycles.'},
        'geometry_scenario':{'bound_m':bound,'source':geometry['ruler_error_source'],
            'coordinate_correlation':'Five gap-reading errors accumulate from T1 through the rod tip. Ranges summarize the 32 sign combinations.',
            'corners':scenarios,
            'kappa_range_m2_s':[min(v['kappa_m2_s'] for v in scenarios),max(v['kappa_m2_s'] for v in scenarios)],
            'nu_range_per_s':[min(v['nu_per_s'] for v in scenarios),max(v['nu_per_s'] for v in scenarios)]},
        'finite_model_residuals':{'relative_amplitude_error':amp_error,'phase_error_rad':phase_residual},
        'additional_sensors_sensitivity':subsets,
        'relative_scan_phase_sensitivity_at_0_17s_rad':2*np.pi*.17/period,
        'scan_note':'Assumed 0.17 s relative scan-offset scenario; not a measured offset, guaranteed bound, or standard uncertainty.'})


def correlated_noise_check(active,start,period,first_cycle,cf,dt):
    """Circular residual-block bootstrap sensitivity, not an acceptance p-value.

    Blocks of 10 and 30 s preserve some within-cycle residual correlation. Long
    drift/contact/model systematics are not identified by this resampling.
    """
    rng=np.random.default_rng(20261118+period);result={}
    for ch in RODS:
        by_block={}
        for seconds in (10,30):
            errors=[]
            for i in range(first_cycle-1,first_cycle+4):
                a=start+i*period;b=a+period
                rows=[r for r in active if a<=float(r['time_s'])<b]
                t=np.array([float(r['time_s'])-start for r in rows]);w=2*np.pi/period
                X=np.column_stack([np.ones(len(t)),np.cos(w*t),np.sin(w*t)])
                f=cf[ch][i];res=np.array(f['residuals_C']);coef=np.array(f['coefficients'])
                n=len(t);block=max(2,int(round(seconds/dt)));nb=int(np.ceil(n/block))
                indices=(rng.integers(0,n,size=(300,nb,1))+np.arange(block)[None,None,:])%n
                sampled=res[indices.reshape(300,-1)[:,:n]]
                changes=sampled@np.linalg.solve(X.T@X,X.T).T
                c=changes+coef;B=np.hypot(c[:,1],c[:,2]);phi=np.arctan2(-c[:,2],c[:,1])
                errors.append({'mean_se_C':np.std(changes[:,0],ddof=1),
                    'amplitude_se_C':np.std(B,ddof=1),
                    'phase_se_rad':np.std(np.angle(np.exp(1j*(phi-f['phase_rad']))),ddof=1)})
            by_block[str(seconds)]={'per_cycle_standard_errors':errors,
                'largest_standard_errors':{k:max(v[k] for v in errors) for k in errors[0]}}
        result[ch]=by_block
    return safe({'replicates':300,'block_seconds':[10,30],'sensors':result,
        'interpretation':'Within-cycle correlated-residual noise sensitivity only; block lengths are scenarios. No p-value, automatic settling certification, or total uncertainty is claimed.'})


def savefig(fig,name):
    fig.savefig(FIG/(name+'.png'),dpi=180);fig.savefig(FIG/(name+'.pdf'));plt.close(fig)


def figures(runs):
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(5,2,figsize=(13,15),layout='constrained')
    settle,sa=plt.subplots(5,3,figsize=(13,14),layout='constrained')
    space,sp=plt.subplots(2,3,figsize=(14,8),layout='constrained')
    for row,run in enumerate(runs):
        P=run['period_s'];r=run['analysis'];a=r['start_s'];b=r['end_s']
        rows=[v for v in run['_active'] if a<=float(v['time_s'])<b];t=np.array([float(v['time_s'])-a for v in rows])
        w=2*np.pi/P;ax,rx=axes[row]
        for j,ch in enumerate(RODS,1):
            y=np.array([float(v[ch]) for v in rows]);f=r['channel_fits'][ch];c=np.array(f['coefficients'])
            pred=c[0]+c[1]*np.cos(w*t)+c[2]*np.sin(w*t)
            ax.plot(t,y,lw=.5,alpha=.65,color=COLORS[j]);ax.plot(t,pred,lw=1,color=COLORS[j],label='T'+str(j))
            rx.plot(t,y-pred,lw=.6,color=COLORS[j],label='T'+str(j))
            cf=run['_cycle_fits'][ch];cycles=np.arange(1,len(cf)+1)
            # Compare cycle stability on a common spatial phase branch.
            phase=np.unwrap([v['phase_rad'] for v in cf])
            base=np.unwrap([v['phase_rad'] for v in run['_cycle_fits']['rod1_C']])
            phase=np.unwrap(np.angle(np.exp(1j*(phase-base))))
            for col,vals in enumerate(([v['mean_C'] for v in cf],[v['amplitude_C'] for v in cf],phase)):
                sa[row,col].plot(cycles,vals,'o-',ms=3,lw=1,color=COLORS[j],label='T'+str(j))
                sa[row,col].axvspan(run['last_five_first_cycle']-.4,cycles[-1]+.4,color='#e2e8f0',alpha=.5,zorder=-1)
        ax.set(title=f'{P} s | cycles {run["last_five_first_cycle"]}-{run["audit"]["complete_cycles"]} | diagnostic',ylabel='Temperature (°C)')
        rx.set(title=f'{P} s | harmonic residuals',ylabel='Observed − harmonic (°C)');rx.axhline(0,color='#64748b',lw=.6)
        ax.set_xlabel('Time within retained interval (s)');rx.set_xlabel('Time within retained interval (s)')
        if row==0:ax.legend(ncol=3);rx.legend(ncol=3)
        for col in range(3):sa[row,col].set_xlabel('Cycle number');sa[row,col].set_title(f'{P} s | '+['mean (°C)','amplitude (°C)','phase relative to T1 (rad)'][col])
        f=r['channel_fits'];xs=np.array(run['geometry']['x_m']);amp=np.array([f[f'rod{i}_C']['amplitude_C'] for i in range(1,6)])
        phi=np.unwrap([f[f'rod{i}_C']['phase_rad'] for i in range(1,6)]);phi-=phi[0]
        color=plt.cm.viridis(row/4)
        sp[0,0].plot(xs[:3]*100,np.log(amp[:3]/amp[0]),'o-',color=color,label=f'{P} s')
        sp[0,0].plot(xs[3:]*100,np.log(amp[3:]/amp[0]),'x',color=color,alpha=.6)
        sp[0,1].plot(xs[:3]*100,phi[:3],'o-',color=color);sp[0,1].plot(xs[3:]*100,phi[3:],'x',color=color,alpha=.6)
        q=r['finite_periodic_fit']['q_per_m'];qp=r['finite_periodic_fit']['q_prime_per_m']
        grid=np.linspace(0,xs[-1],200);transfer=finite_response(q,qp,run['geometry']['analysis_length_m'],grid)
        sp[0,0].plot(grid*100,np.log(abs(transfer)),lw=.8,ls='--',color=color)
        sp[0,1].plot(grid*100,np.unwrap(np.angle(transfer)),lw=.8,ls='--',color=color)
        residuals=run['supplement']['finite_model_residuals']
        sp[0,2].plot(xs[:3]*100,np.array(residuals['relative_amplitude_error'])*100,'o-',color=color)
        tr=r['transport']
        sp[1,0].errorbar(P,tr['kappa_m2_s']*1e6,yerr=tr['kappa_se_m2_s']*1e6,fmt='o',color=color,capsize=4)
        sp[1,1].errorbar(P,tr['nu_per_s'],yerr=tr['nu_se_per_s'],fmt='o',color=color,capsize=4)
        for j in range(2):
            sp[1,2].plot(P,100/(q if j==0 else qp),'o' if j==0 else '^',color=color)
        if q>qp:sp[1,2].plot(P,100/np.sqrt(q*q-qp*qp),'s',mfc='none',color=color)
    fig.suptitle('Five PI records: fixed last five complete cycles; raw traces and first-harmonic fits\nAll parameters remain diagnostic until settling and spatial validity are supported',fontsize=14)
    settle.suptitle('Cycle repeatability: shaded region is the fixed last five complete cycles\nNo cycle is removed from the source files',fontsize=14)
    for col in range(3):sa[0,col].legend(ncol=3)
    sp[0,0].set(xlabel='Distance from T1 (cm)',ylabel='ln(B / B₁)',title='Amplitude: T1–T3 fit; × = diagnostic T4–T5');sp[0,0].legend(ncol=3)
    sp[0,1].set(xlabel='Distance from T1 (cm)',ylabel='Phase relative to T1 (rad)',title='Downstream lag; dashed = finite model')
    sp[0,2].set(xlabel='Distance from T1 (cm)',ylabel='Amplitude residual (%)',title='Finite model discrepancy at fitted sensors')
    sp[1,0].set(xlabel='Drive period (s)',ylabel='κ (10⁻⁶ m²/s)',title='Conditional cycle-repeat SE only')
    sp[1,1].set(xlabel='Drive period (s)',ylabel='ν (1/s)',title='Negative loss is preserved');sp[1,1].axhline(0,color='grey',lw=.8)
    sp[1,2].set(xlabel='Drive period (s)',ylabel='Length (cm)',title='● 1/q; ▲ 1/q′; open squares: 1/m')
    space.suptitle('Exploratory spatial inference — five-period material estimate is not validated',fontsize=14)
    savefig(fig,'m08_pi_five_period_time_fits')
    savefig(settle,'m08_pi_five_period_cycle_settling')
    savefig(space,'m08_pi_five_period_spatial_and_transport')


def main():
    OUT.mkdir(parents=True,exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
    manifest,geometry=freeze_sources();runs=[];table=[]
    for P,entry in manifest.items():
        P=int(P);active,start,count,audit,cycles,cf=unpack(entry,P)
        tests=windows(cf,count);last=tests[-1];j=last['first_cycle']-1
        plan={'label':f'PI {P}s fixed last five cycles','period_s':P,'start_s':start+j*P,
              'end_s':start+(j+5)*P,'rod_sensors':[1,2,3],'settling':TOL,'minimum_amplitude_snr':5}
        result=analyse_interval(active,geometry,plan)
        # Never use passing stationarity alone to declare spatial/model validity.
        supplement=supplements(active,start,P,result,geometry)
        supplement['correlated_noise_check']=correlated_noise_check(active,start,P,j+1,cf,audit['median_dt_s'])
        run={'period_s':P,'source':entry,'geometry':geometry,'audit':audit,'cycles':cycles,
             'five_cycle_windows':tests,'any_window_passes_planning_gate':any(v['planning_gate_passed'] for v in tests),
             'last_five_first_cycle':j+1,'analysis_plan':plan,'analysis':result,'supplement':supplement,
             'overall_status':'diagnostic_only',
             'cycle_fits':{ch:[{k:f[k] for k in ('mean_C','amplitude_C','phase_rad','amplitude_se_C','phase_se_rad','rms_residual_C')} for f in vals] for ch,vals in cf.items()}}
        write_json(OUT/f'm08_pi_p{P}s_analysis.json',run)
        run.update(_active=active,_cycle_fits=cf);runs.append(run)
        tr=result['transport'];table.append({'period_s':P,'total_complete_cycles':count,'retained_first_cycle':j+1,'retained_last_cycle':j+5,
            'last_five_stationary':result['cycle_stationarity_passed'],'any_five_stationary':run['any_window_passes_planning_gate'],
            'q_per_m':result['finite_periodic_fit']['q_per_m'],'q_prime_per_m':result['finite_periodic_fit']['q_prime_per_m'],
            'kappa_m2_s':tr['kappa_m2_s'],'kappa_conditional_se_m2_s':tr['kappa_se_m2_s'],
            'nu_per_s':tr['nu_per_s'],'nu_conditional_se_per_s':tr['nu_se_per_s'],
            'positive_loss':tr['physical_positive_loss'],'max_mean_span_C':max(v['mean_span_C'] for v in last['metrics'].values()),
            'max_amplitude_span_fraction':max(v['amplitude_span_fraction'] for v in last['metrics'].values()),
            'max_phase_span_rad':max(v['phase_span_rad'] for v in last['metrics'].values()),
            'overall_status':'diagnostic_only'})
        print(P,count,'cycles; any stationary:',run['any_window_passes_planning_gate'],'kappa,nu:',tr['kappa_m2_s'],tr['nu_per_s'],flush=True)
    with (OUT/'m08_pi_five_period_summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
    harmonic_rows=[];cycle_rows=[]
    for run in runs:
        for ch,f in run['analysis']['channel_fits'].items():
            harmonic_rows.append({'period_s':run['period_s'],'channel':ch,**{k:f[k] for k in
                ('mean_C','amplitude_C','phase_rad','amplitude_se_C','phase_se_rad','rms_residual_C','sample_count')}})
        for ch,vals in run['cycle_fits'].items():
            for i,f in enumerate(vals,1):cycle_rows.append({'period_s':run['period_s'],'cycle':i,'channel':ch,**f})
    for filename,rows in (('m08_pi_five_period_harmonic_fits.csv',harmonic_rows),('m08_pi_five_period_cycle_fits.csv',cycle_rows)):
        with (OUT/filename).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    comparisons=[]
    for a,b in itertools.combinations(runs,2):
        x=a['analysis']['transport'];y=b['analysis']['transport']
        comparisons.append({'periods_s':[a['period_s'],b['period_s']],
            'kappa_difference_over_conditional_se':(x['kappa_m2_s']-y['kappa_m2_s'])/np.hypot(x['kappa_se_m2_s'],y['kappa_se_m2_s']),
            'interpretation':'Diagnostic comparison only; drift and shared systematics are not covered by these SEs.'})
    write_json(OUT/'m08_pi_five_period_summary.json',{'kind':'measured_five_period_diagnostic_review','results':table,'frequency_comparisons':comparisons,
        'selection':'Same T1-T3 and fixed last five complete cycles at every period. All contiguous five-cycle windows enumerated independently of physical fit results.',
        'settling_criterion':TOL,'criterion_status':'Existing provisional planning tolerances; not a course-mandated noise-calibrated certification.',
        'geometry_inputs':'Confirmed Module 7 map. Operator-confirmed +/-1 mm per ruler gap is propagated as a bounded scenario. The 0.01 mm caliper specification is not assumed 1-sigma.',
        'ambient':'Initial TEC references are recorded per acquisition. See the transport note for the mean-profile refit. Independent air temperature and drift are unknown.',
        'uncertainty':'Conditional cycle-repeat SE, not a confidence interval or total uncertainty. Drift violates independent identical cycle assumptions. Calibration, contact, scan and geometry covariances unresolved.',
        'material_constants':'No sourced density/cp and their uncertainties supplied; k and h not computed.',
        'production_record_complete':False,'qualified_periods_s':[],
        'raw_prefixes_verified_unchanged':True,
        'analysis_sha256':digest(Path(__file__).read_bytes()),'core_analysis_sha256':digest((Path(__file__).parent/'angstrom_fit.py').read_bytes())})
    figures(runs)
    for entry in manifest.values():assert digest((ROOT/entry['raw']).read_bytes()[:entry['prefix_bytes']])==entry['sha256']
    print('Saved',OUT,'and',FIG,flush=True)


if __name__=='__main__':main()
