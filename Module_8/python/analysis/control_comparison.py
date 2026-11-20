"""Plot recorded OPEN/P/PI at common settings without modifying raw evidence.

Select the last three fully covered, phase-aligned cycles of each initial run.
The selection is descriptive, not an automatic settling certification.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/module8-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from angstrom_fit import fit_trace, safe
from initial_tec_reference import initial_tec_reference

MODULE = Path(__file__).resolve().parents[2]
SOURCES = {
    'OPEN': 'm08_open_p200s_20261111_101207_449492.csv',
    'P': 'm08_p_p200s_20261111_094156_728168.csv',
    'PI': 'm08_pi_p200s_20261109_095722_597413.csv',
}
SOURCES_100 = {
    'Feedforward': 'module_08_rod_20261118_113619_678440.csv',
    'P': 'module_08_rod_20261118_114204_147029.csv',
    'PI': 'm08_pi_p100s_20261116_104519_503645.csv',
}
COLORS = {'Feedforward': '#D55E00', 'OPEN': '#D55E00', 'P': '#0072B2', 'PI': '#009E73'}


def inspect(mode, filename, period=200):
    path = MODULE / 'data/raw' / filename
    original = path.read_bytes()
    prefix = original[:original.rfind(b'\n')+1]
    rows = list(csv.DictReader(io.StringIO(prefix.decode('utf-8-sig'))))
    recorded_mode = 'RAW_POS' if mode == 'Feedforward' else mode
    active = [r for r in rows if r['event'] == 'measurement'
              and r['run_state'] == 'RUNNING' and r['control_mode'] == recorded_mode]
    if not active:
        raise ValueError(f'{mode}: no active samples')
    identity = ('run_id', 'step', 'plan_sha256')
    latest = active[-1]
    active = [r for r in active if all(r[k] == latest[k] for k in identity)]
    if recorded_mode == 'RAW_POS':
        plan = json.loads(path.with_name(path.stem + '_plan_01.json').read_text())
        target = plan['metadata']['requested_comparison_waveform']
        if (target['mean_C'], target['amplitude_C'], target['period_s']) != (35, 5, period):
            raise ValueError('Feedforward plan has a different comparison target')
        if {float(r['period_s']) for r in active} != {period}:
            raise ValueError('Feedforward acquired period differs from the plan')
    elif any((float(r['Ta_C']), float(r['Tb_C']), float(r['period_s'])) != (35, 5, period) for r in active):
        raise ValueError(f'{mode}: comparison requires common 35 +/-5 C, {period} s settings')
    step_event = next(r for r in rows if r['run_id'] == latest['run_id']
                      and r['note'].startswith('#EVENT,STEP,') and r['note'].endswith(',0'))
    origin = int(step_event['note'].split(',')[2])/1000
    dt = float(np.median(np.diff([float(r['time_s']) for r in active])))
    # Endpoint samples are normally one acquisition interval before a boundary.
    complete = int((float(active[-1]['time_s'])-origin+dt)//period)
    if complete < 3:
        raise ValueError(f'{mode}: fewer than three complete covered cycles')
    start, end = origin+(complete-3)*period, origin+complete*period
    selected = [r for r in active if start <= float(r['time_s']) < end]
    t = np.array([float(r['time_s'])-start for r in selected])
    if t[0] > 2*dt or 3*period-t[-1] > 2*dt or np.max(np.diff(t)) > 3*dt+1e-6:
        raise ValueError(f'{mode}: insufficient coverage for the selected window')
    keys = ('tec_C', 'rod1_C', 'setpoint_C', 'signed_pwm')
    data = {k: np.array([float(r[k]) for r in selected]) for k in keys}
    if recorded_mode == 'RAW_POS':
        recorded_phase = np.array([float(r['phase_rad']) for r in selected])
        data['setpoint_C'] = target['mean_C'] + target['amplitude_C'] * np.sin(recorded_phase)
    if not all(np.isfinite(v).all() for v in data.values()):
        raise ValueError(f'{mode}: nonfinite selected values')
    if any(r['safety'] != 'OK' or r['fault_code'] != 'NONE' for r in selected):
        raise ValueError(f'{mode}: safety event in selected interval')
    reference = fit_trace(t, data['setpoint_C'], period)
    metrics = {}
    for key in ('tec_C', 'rod1_C'):
        fit = fit_trace(t, data[key], period)
        cycle_fits = [fit_trace(t[(t >= i*period) & (t < (i+1)*period)],
                               data[key][(t >= i*period) & (t < (i+1)*period)], period) for i in range(3)]
        amplitudes = [f['amplitude_C'] for f in cycle_fits]
        metrics[key] = {
            k: fit[k] for k in ('mean_C', 'amplitude_C', 'rms_residual_C')}
        metrics[key].update(
            phase_lag_vs_TEC_setpoint_deg=math.degrees(
                (reference['phase_rad']-fit['phase_rad']+math.pi) % (2*math.pi)-math.pi),
            cycle_mean_span_C=float(np.ptp([f['mean_C'] for f in cycle_fits])),
            cycle_amplitude_span_fraction=float(np.ptp(amplitudes)/np.mean(amplitudes)),
            cycle_phase_span_rad=float(np.ptp(np.unwrap([f['phase_rad'] for f in cycle_fits]))))
    metrics['tec_C'].update(
        mean_tracking_error_C=float(np.mean(data['tec_C']-data['setpoint_C'])),
        amplitude_ratio=metrics['tec_C']['amplitude_C']/reference['amplitude_C'],
        rms_tracking_error_C=float(np.sqrt(np.mean((data['tec_C']-data['setpoint_C'])**2))))
    seq = np.array([int(r['seq']) for r in selected])
    gaps = np.diff(seq)-1
    info = dict(mode=mode, source=str(path.relative_to(MODULE.parent)),
                source_sha256=hashlib.sha256(original).hexdigest(),
                selected_cycles=list(range(complete-2, complete+1)),
                start_device_s=start, end_device_s=end,
                first_selected_host_time=selected[0]['host_time'],
                last_selected_host_time=selected[-1]['host_time'],
                samples=len(selected), missing_sequence_samples=int(np.sum(gaps[gaps > 0])),
                max_gap_s=float(np.max(np.diff(t))),
                selected_saturated_samples=sum(r['saturated'] == '1' for r in selected),
                Kp=float(latest['Kp_pwm_per_C']), Ki=float(latest['Ki_pwm_per_C_s']),
                ratio=float(latest['heating_to_cooling_ratio']), pwm_limit=int(latest['pwm_limit']),
                metrics=metrics)
    if period == 100:
        info.update(recorded_control_mode=recorded_mode, room_reference=initial_tec_reference(rows),
                    source_prefix_bytes=len(prefix), source_sha256=hashlib.sha256(prefix).hexdigest())
    if recorded_mode == 'RAW_POS':
        info.update(Kp=None, Ki=None, Ua_pwm=float(latest['Ua_pwm']), Ub_pwm=float(latest['Ub_pwm']),
                    setpoint_source='Saved comparison target and recorded phase_rad',
                    feedforward_offset_reference_C=plan['metadata']['calibration_reference_ambient_C'])
    checked = prefix if period == 100 else original
    if path.read_bytes()[:len(checked)] != checked:
        raise ValueError('Source prefix changed during analysis')
    return t, data, info


def gap_line(t, y):
    gaps = np.where(np.diff(t) > .75)[0]+1
    return np.insert(t, gaps, np.nan), np.insert(y, gaps, np.nan)


def main(period=200):
    sources = SOURCES_100 if period == 100 else SOURCES
    runs = {mode: inspect(mode, filename, period) for mode, filename in sources.items()}
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.titlelocation': 'left'})
    fig, axes = plt.subplots(3, 1, figsize=(12.5, 9), sharex=True,
                             gridspec_kw={'height_ratios': [1.25, 1, .85]})
    for mode, (t, data, _) in runs.items():
        for ax, key in zip(axes, ('tec_C', 'rod1_C', 'signed_pwm')):
            ax.plot(*gap_line(t, data[key]), color=COLORS[mode], lw=1.6, label=mode)
    t, data, _ = runs['P']
    axes[0].plot(t, data['setpoint_C'], color='#333333', ls='--', lw=1.25,
                 label='Requested TEC: 35 +/- 5 C')
    for ax in axes:
        ax.grid(alpha=.2); ax.set_xlim(0, 3*period)
        ax.set_xticks(np.linspace(0, 3*period, 7))
    axes[0].set(title='(a) Measured TEC temperature and requested TEC setpoint', ylabel='TEC temperature (C)')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='center', bbox_to_anchor=(.5, .902),
               ncol=4, frameon=False, fontsize=9)
    axes[1].set(title='(b) Measured rod boundary T1', ylabel='T1 temperature (C)')
    axes[2].set(title='(c) Applied signed PWM', ylabel='PWM counts',
                xlabel=f'Time from selected cycle boundary (s), three {period} s cycles')
    axes[2].axhline(0, color='#777777', lw=.7)
    comparison = 'Feedforward / P / PI' if period == 100 else 'OPEN / P / PI'
    fig.suptitle(f'Module 8 Part I: {comparison} comparison', fontsize=16, fontweight='bold', y=.975)
    fig.text(.075, .928, f'Common nominal request: 35 +/- 5 C, {period} s | P: Kp=50, Ki=0 | PI: Kp=50, Ki=0.3', fontsize=10)
    if period == 100:
        fig.text(.075, .043, 'Feedforward and P: cycles 1–3, including startup. PI: cycles 10–12. Metrics describe these windows.', fontsize=9)
        fig.text(.075, .023, 'Feedforward target reconstructed from saved request and phase. Its applied PWM used the historical 23.44 C baseline.', fontsize=9, color='#555555')
    else:
        p_span = runs['P'][2]['metrics']['rod1_C']['cycle_mean_span_C']
        missing = runs['OPEN'][2]['missing_sequence_samples']
        fig.text(.075, .043, f'Whole-cycle time shifts. OPEN: {missing} missing samples. P/T1 mean span: {p_span:.3f} C.', fontsize=9)
        fig.text(.075, .023, 'PI: Nov 9. OPEN/P: Nov 11. Selected windows are descriptive.', fontsize=9, color='#555555')
    fig.subplots_adjust(left=.075, right=.985, top=.855, bottom=.105, hspace=.35)
    stem = 'm08_feedforward_p_pi_p100s_comparison' if period == 100 else 'm08_open_p_pi_p200s_comparison'
    figures = MODULE / 'figures/control_comparison'; figures.mkdir(parents=True, exist_ok=True)
    processed = MODULE / 'data/processed/control_comparison'; processed.mkdir(parents=True, exist_ok=True)
    fig.savefig(figures/(stem+'.png'), dpi=200)
    fig.savefig(figures/(stem+'.pdf'))
    plt.close(fig)
    receipt = {'settings': {'Ta_C': 35, 'Tb_C': 5, 'period_s': period},
               'selection': 'Last three complete covered phase-aligned cycles per run; only whole-cycle time-origin shifts.',
               'processing': 'Unmodified observations; gaps are broken, never filled. No averaging, smoothing, amplitude normalization or fitted phase alignment.',
               'limitations': ['PI and OPEN/P acquired on different days; ambient not recorded.',
                              'P last-three-cycle T1 mean span exceeds provisional 0.1 C tolerance; retained by operator decision, not certified settled.',
                              'Control comparison only; not a transport fit or complete Module 8 qualification.'],
               'runs': [v[2] for v in runs.values()]}
    if period == 100:
        receipt['limitations'] = [
            'Feedforward and P retain the full recorded three-cycle run including startup. PI uses its last three complete cycles.',
            'The methods were acquired on different dates or with different initial TEC temperatures.',
            'Feedforward used the earlier Module 4 temperature baseline to set Ua. The reconstructed nominal request describes the comparison target.',
        ]
    (processed/(stem+'.json')).write_text(json.dumps(safe(receipt), indent=2, allow_nan=False)+'\n')
    with (processed/(stem+'_metrics.csv')).open('w', newline='') as stream:
        fields = ['mode', 'mean_C', 'amplitude_C', 'mean_tracking_error_C', 'amplitude_ratio',
                  'phase_lag_vs_TEC_setpoint_deg', 'rms_tracking_error_C', 'rms_residual_C']
        if period == 100:
            fields += ['Kp', 'Ki', 'Ua_pwm', 'Ub_pwm', 'room_reference_C',
                       'selected_saturated_samples', 'selected_cycles']
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for mode, (_, _, info) in runs.items():
            row = dict(mode=mode, **info['metrics']['tec_C'])
            if period == 100:
                row.update({key: info.get(key) for key in ('Kp', 'Ki', 'Ua_pwm', 'Ub_pwm', 'selected_saturated_samples')})
                row['room_reference_C'] = info['room_reference']['room_reference_C']
                row['selected_cycles'] = f"{info['selected_cycles'][0]}-{info['selected_cycles'][-1]}"
            writer.writerow(row)
    print(json.dumps(safe({'figure': str(figures/(stem+'.png')),
          'runs': [dict(mode=m, **v[2]['metrics']['tec_C'], missing=v[2]['missing_sequence_samples']) for m,v in runs.items()]}), indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--period', type=int, choices=(100, 200), default=200)
    main(parser.parse_args().period)
