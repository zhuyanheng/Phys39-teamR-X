"""Analyze the operator-selected end of the completed Nov 4 constant-setpoint run.

This is a stationary approximation, not certification against the original
0.02 C/min, 0.10 C, 600 s criterion. No acquisition or serial imports are used.
"""
import argparse
import csv
import hashlib
import math
from pathlib import Path
import statistics
import stationary_fin_fit as fin

ROOT=Path(__file__).resolve().parents[3]
DEFAULT=ROOT/'Module_7/data/raw/module_07_rod_20261104_095908_593628.csv'


def analyse_selected(raw, duration=600.0):
    raw=Path(raw); before=hashlib.sha256(raw.read_bytes()).hexdigest()
    records=fin.read_rows(raw)
    if not records or records[-1].get('event')!='disconnect':
        raise ValueError('A completed, disconnected run is required; no active file is analyzed.')
    rows=fin.measurement_rows(records)
    active=[r for r in rows if r.get('control_active')=='1']
    if not active:raise ValueError('No controlled measurements')
    end=float(active[-1]['time_s'])
    start=max(i for i,r in enumerate(active) if float(r['time_s'])<=end-duration)
    selected=active[start:]
    strict=fin.steady_window(selected,.02,600,.1,fin.CHANNELS)
    # The caller/operator fixes this window. Large numerical gate values merely
    # allow the shared fitting routine to average that exact selected window;
    # they are not substituted acceptance thresholds.
    result,profile=fin.analyse(selected,fin.POSITIONS_M,fin.ANALYSIS_LENGTH_M,
        ambient=None,diameter=.01277,limit=1e9,hold=duration-.1,
        drift_budget=1e9,diameter_is_measured=True)
    if result['status']!='fitted':raise ValueError(result)
    result.update(source=fin.portable_path(raw),source_sha256=before,
        interpretation='operator_selected_stationary_approximation',
        operator_selection_date='2026-11-04',
        strict_criterion_passed=strict['start'] is not None,
        strict_window_check=strict,
        ambient_note='No independent thermometer; ambient is jointly fitted with m.',
        diameter_method='vernier caliper',instrument_precision_mm=.01,
        instrument_precision_is_standard_uncertainty=False)
    result['criterion']={'selection':'last 600 s before operator stop',
        'relaxed':True,'original_slope_limit_C_per_min':.02,
        'original_drift_budget_C':.1,'original_hold_s':600}
    result['time_quality']={'largest_gap_s':max(float(b['time_s'])-float(a['time_s']) for a,b in zip(selected,selected[1:])),
        'safety_counts':{s:sum(r.get('safety')==s for r in selected) for s in {r.get('safety') for r in selected}}}
    result['channel_slopes_C_per_min']={}
    for ch in fin.CHANNELS:
        ts=[float(r['time_s']) for r in selected];ys=[float(r[ch]) for r in selected]
        mt=statistics.mean(ts);my=statistics.mean(ys)
        result['channel_slopes_C_per_min'][ch]=60*sum((t-mt)*(y-my) for t,y in zip(ts,ys))/sum((t-mt)**2 for t in ts)
    out=ROOT/'Module_7/data/processed';out.mkdir(exist_ok=True,parents=True)
    stem=raw.stem+'_selected_stationary'
    fin.write_json(out/(stem+'.json'),result)
    fin.write_profile_csv(out/(stem+'_profile.csv'),profile)
    import os
    os.environ.setdefault('MPLCONFIGDIR','/private/tmp/module7-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figures=ROOT/'Module_7/figures/final_selected';figures.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.6),constrained_layout=True)
    xx=[fin.ANALYSIS_LENGTH_M*i/300 for i in range(301)]
    theta0=profile[0]['theta_C'];m=result['finite_model']['m_per_m'];mi=result['semi_infinite_model']['m_per_m']
    axes[0].errorbar([r['x_m'] for r in profile],[r['theta_C'] for r in profile],yerr=[r['std_C'] for r in profile],fmt='ko',capsize=4,label='Selected window mean +/- SD')
    axes[0].plot(xx,[theta0*fin.theta_finite(x,m,fin.ANALYSIS_LENGTH_M) for x in xx],label=f'Finite: m={m:.3f} /m')
    axes[0].plot(xx,[theta0*fin.theta_semi_infinite(x,mi) for x in xx],'--',label=f'Semi-infinite: m={mi:.3f} /m')
    for key,label in [('finite','Finite'),('semi','Semi-infinite')]:
        axes[1].plot([r['x_m'] for r in profile],[r['residual_'+key+'_C'] for r in profile],'o-',label=label)
    axes[1].axhline(0,color='grey',lw=.8)
    for ax in axes:ax.set_xlabel('x from hole 2 (m)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    axes[0].set_ylabel('Excess temperature (C)');axes[1].set_ylabel('Model - measured (C)')
    fig.suptitle('Operator-selected stationary approximation; strict criterion not met\nAmbient jointly fitted, not independently measured',fontsize=11)
    fig.savefig(figures/(stem+'.png'),dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(11.5,6),sharex=True,constrained_layout=True)
    ts=[float(r['time_s'])/60 for r in rows]
    for i,ch in enumerate(fin.CHANNELS):axes[0 if i==0 else 1].plot(ts,[float(r[ch]) for r in rows],lw=1,label=ch)
    for ax in axes:
        ax.axvspan(float(selected[0]['time_s'])/60,end/60,color='#b9d8c0',alpha=.45,label='Operator-selected final 10 min')
        ax.set_ylabel('Temperature (C)');ax.grid(alpha=.2);ax.legend(fontsize=8,ncol=3)
    axes[1].set_xlabel('Arduino time (min)');fig.suptitle('Complete measured approach and selected stationary approximation')
    fig.savefig(figures/(stem+'_history.png'),dpi=160);plt.close(fig)
    assert hashlib.sha256(raw.read_bytes()).hexdigest()==before
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('raw',type=Path,nargs='?',default=DEFAULT)
    r=analyse_selected(p.parse_args().raw)
    print('Strict steady criterion:',r['strict_criterion_passed'])
    print('Finite m:',r['finite_model']['m_per_m'],'/m; fitted ambient:',r['ambient_C'],'C')
    print('Slopes C/min:',r['channel_slopes_C_per_min'])
