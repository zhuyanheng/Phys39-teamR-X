"""Check per-cycle repeatability in a saved or growing single-step pilot CSV.

The snapshot prefix length/hash makes a live-file assessment reproducible.
This is a repeatability check, not a full Angstrom/model validity assessment.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import io
import json
import math
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from angstrom_fit import fit_trace,safe

MODULE=Path(__file__).resolve().parents[2]


def inspect(path,prefix_bytes=None):
    path=Path(path);content=path.read_bytes()
    if prefix_bytes is not None:content=content[:prefix_bytes]
    prefix=content[:content.rfind(b'\n')+1]
    rows=list(csv.DictReader(io.StringIO(prefix.decode('utf-8-sig'))))
    measurements=[r for r in rows if r['event']=='measurement']
    active=[r for r in measurements if r['run_state']=='RUNNING']
    latest=active[-1]
    keys=('run_id','step','control_mode','period_s','plan_sha256')
    active=[r for r in active if all(r[k]==latest[k] for k in keys)]
    if latest['step']!='0':raise ValueError('This pilot checker supports the initial single-step segment only')
    events=[r for r in rows if r.get('note','').startswith('#EVENT,STEP,') and r['run_id']==latest['run_id'] and r['note'].endswith(',0')]
    start=int(events[-1]['note'].split(',')[2])/1000
    period=float(latest['period_s']);elapsed=float(latest['time_s'])-start
    complete=int(elapsed//period)
    channels=('tec_C','rod1_C','rod2_C','rod3_C','rod4_C','rod5_C')
    fits={k:[] for k in channels};cycles=[]
    for i in range(complete):
        a=start+i*period;b=a+period
        segment=[r for r in active if a<=float(r['time_s'])<b]
        t=np.array([float(r['time_s'])-start for r in segment])
        if len(t)<8 or max(np.diff(t))>1.5:raise ValueError('Insufficient samples or acquisition gap in a cycle')
        cycles.append({'cycle':i+1,'start_s':a,'end_s':b,'samples':len(segment),
                       'saturated_fraction':sum(r['saturated']=='1' for r in segment)/len(segment)})
        for k in channels:
            f=fit_trace(t,[float(r[k]) for r in segment],period)
            fits[k].append({name:f[name] for name in ('mean_C','amplitude_C','phase_rad','rms_residual_C')})
    changes={}
    for k,series in fits.items():
        changes[k]=[]
        for i,(a,b) in enumerate(zip(series,series[1:]),2):
            mean=abs(b['mean_C']-a['mean_C'])
            amp=abs(b['amplitude_C']-a['amplitude_C'])/((a['amplitude_C']+b['amplitude_C'])/2)
            phase=abs((b['phase_rad']-a['phase_rad']+math.pi)%(2*math.pi)-math.pi)
            changes[k].append({'ending_cycle':i,'mean_change_C':mean,'amplitude_change_fraction':amp,
                               'phase_change_rad':phase,'passes_planning_tolerances':mean<=.1 and amp<=.05 and phase<=.1})
    selected=('rod1_C','rod2_C','rod3_C')
    five=complete>=5 and all(all(v['passes_planning_tolerances'] for v in changes[k][-4:]) for k in selected)
    return safe({'source':str(path.resolve().relative_to(MODULE.parent)),
        'snapshot_prefix_bytes':len(prefix),'snapshot_prefix_sha256':hashlib.sha256(prefix).hexdigest(),
        'as_of_host_time':measurements[-1]['host_time'],'run_id':latest['run_id'],
        'period_s':period,'elapsed_running_s':elapsed,'complete_cycles':complete,
        'first_segment_start_s':start,'cycles':cycles,'cycle_fits':fits,'cycle_to_cycle_changes':changes,
        'planning_tolerances':{'mean_change_C':.1,'amplitude_change_fraction':.05,'phase_change_rad':.1},
        'minimum_retained_rods_for_this_check':selected,'last_five_cycles_repeatability_gate':five,
        'scope':'Planning tolerances require justification against measured noise. Passing this gate alone does not certify boundary quality, spatial model, geometry or a full production dataset.'})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw',type=Path);parser.add_argument('--prefix-bytes',type=int)
    args=parser.parse_args();result=inspect(args.raw,args.prefix_bytes)
    directory=MODULE/'data/processed/pilot_checks';directory.mkdir(parents=True,exist_ok=True)
    output=directory/(args.raw.stem+'_cycle_settling.json')
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('as of',result['as_of_host_time'],'elapsed',result['elapsed_running_s'],'complete cycles',result['complete_cycles'])
    for k in ('tec_C','rod1_C','rod2_C','rod3_C'):
        print(k, result['cycle_to_cycle_changes'][k][-1:] or 'need two complete cycles')
    print('last five repeatability gate',result['last_five_cycles_repeatability_gate']);print(output)

if __name__=='__main__':main()
