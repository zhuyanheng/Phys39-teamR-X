"""Audit recorded hardware rehearsals, without certifying periodic control quality.

One measurement row is one Arduino scan; CSV events are kept separate.
Checks the original byte stream, sequence, channels, outputs and planned phase.
Run from any directory; output defaults inside Module_8/data/processed/.
"""
from pathlib import Path
import argparse
import collections
import csv
import hashlib
import json
import math
import re
import sys

MODULE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(MODULE/'python'))
from rod_protocol import parse_data_line,ROD_CHANNELS


def sha(raw):return hashlib.sha256(raw).hexdigest()


def audit(path):
    path=Path(path)
    original=path.read_bytes()
    rows=list(csv.DictReader(original.decode('utf-8-sig').splitlines()))
    samples=[r for r in rows if r['event']=='measurement']
    serial_path=path.with_suffix('.serial.log')
    serial_bytes=serial_path.read_bytes()
    serial_lines=serial_bytes.decode('utf-8',errors='replace').splitlines()
    data_lines=[s for s in serial_lines if s.startswith('DATA,')]
    parsed=[parse_data_line(s) for s in data_lines]
    plans={}
    for p in sorted(path.parent.glob(path.stem+'_plan_*.json')):
        doc=json.loads(p.read_text())
        plans[doc['plan_sha256']]=doc
    starts={}
    for r in rows:
        match=re.fullmatch(r'#EVENT,STEP,(\d+),0',r.get('note',''))
        if match:starts[r['run_id']]=int(match[1])
    times=[float(r['time_s']) for r in samples]
    seq=[int(r['seq']) for r in samples]
    channels=['tec_C']+[f'{c}_C' for c in ROD_CHANNELS]
    ranges={k:{'invalid_count':sum(not math.isfinite(float(r[k])) for r in samples),
               'min_C':min(float(r[k]) for r in samples),'max_C':max(float(r[k]) for r in samples)} for k in channels}
    runs=[]
    for run_id in sorted({r['run_id'] for r in samples if r['run_state']=='RUNNING'},key=int):
        active=[r for r in samples if r['run_id']==run_id and r['run_state']=='RUNNING']
        plan=plans[active[0]['plan_sha256']]
        errors=[];wave_errors=[]
        for r in active:
            elapsed=(int(r['time_ms'])-starts[run_id])/1000
            phase=0;offset=0
            for step in plan['steps']:
                used=max(0,min(elapsed-offset,step['duration_s']))
                phase+=2*math.pi*used/step['period_s'];offset+=step['duration_s']
            errors.append(abs((float(r['phase_rad'])-phase+math.pi)%(2*math.pi)-math.pi))
            s=plan['steps'][int(r['step'])]
            wave_errors.append(abs(float(r['setpoint_C'])-(s['Ta_C']+s['Tb_C']*math.sin(phase))))
        done=[r for r in samples if r['run_id']==run_id and r['run_state']=='DONE']
        runs.append({'run_id':run_id,'active_samples':len(active),'steps':plan['steps'],
            'saturated_samples':sum(r['saturated']=='1' for r in active),
            'saturated_fraction':sum(r['saturated']=='1' for r in active)/len(active),
            'max_phase_generation_error_rad':max(errors),'max_setpoint_generation_error_C':max(wave_errors),
            'done_samples':len(done),'all_done_outputs_zero':bool(done) and all(int(r['signed_pwm'])==0 and int(r['heat_pwm'])==0 and int(r['cool_pwm'])==0 for r in done),
            'mean_changed_between_steps':len({s['Ta_C'] for s in plan['steps']})>1,
            'maximum_possible_cycles_per_step':[s['duration_s']/s['period_s'] for s in plan['steps']]})
    assert path.read_bytes()==original,'Raw CSV changed during check; rerun on a stable snapshot'
    assert serial_path.read_bytes()==serial_bytes,'Serial log changed during check'
    return {'source':str(path.resolve().relative_to(MODULE.parent)),'sha256':sha(original),
        'serial_sha256':sha(serial_bytes),'raw_unchanged':True,
        'first_host_time':samples[0]['host_time'],'last_host_time':samples[-1]['host_time'],
        'measurement_rows':len(samples),'serial_data_lines':len(data_lines),
        'malformed_serial_data_lines':sum(s is None for s in parsed),
        'csv_serial_sequence_match':[s.values['seq'] for s in parsed if s] == seq,
        'missing_sequence_records':sum(max(0,b-a-1) for a,b in zip(seq,seq[1:])),
        'nonadvancing_sequence':sum(b<=a for a,b in zip(seq,seq[1:])),
        'sample_interval_min_s':min(b-a for a,b in zip(times,times[1:])),
        'sample_interval_max_s':max(b-a for a,b in zip(times,times[1:])),
        'channel_ranges':ranges,'max_heartbeat_age_ms':max(int(r['heartbeat_age_ms']) for r in samples),
        'fault_counts':dict(collections.Counter(r['fault_code'] for r in samples)),
        'firmware_errors':[s for s in serial_lines if s.startswith('#ERR,')],
        'events':[s for s in serial_lines if s.startswith('#EVENT,')],
        'runs':runs,'limitation':'Rehearsal validates acquisition, timing and output-off sequence; it does not establish settled sinusoidal tracking or a production dataset.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw',nargs='+',type=Path)
    parser.add_argument('--out',type=Path,default=MODULE/'data/processed/rehearsal_checks/rehearsal_check_20261109.json')
    args=parser.parse_args()
    result={'date':'2026-11-09','checks':[audit(p) for p in args.raw]}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    for entry in result['checks']:
        print(Path(entry['source']).name,entry['measurement_rows'],'rows, missing',entry['missing_sequence_records'],'faults',entry['fault_counts'])
        for run in entry['runs']:print(' run',run['run_id'],'phase error',run['max_phase_generation_error_rad'],'setpoint error',run['max_setpoint_generation_error_C'],'done zero',run['all_done_outputs_zero'])
    print(args.out)

if __name__=='__main__':main()
