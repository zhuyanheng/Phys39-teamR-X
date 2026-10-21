"""Analyze retained Module 5 P and Oct 19 PI records; never connects to hardware.

Run with repository .venv/bin/python. All source CSVs remain unchanged.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
from file_naming import experiment_stem

os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/phys39_analysis_mpl')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

M = Path(__file__).resolve().parents[2]
ROOT = M.parent
OUT = M / 'data/experiment_analysis'
FIG = M / 'figures/experiment_analysis'
DOC = M / 'docs/experiment_analysis_2026-10-19.md'
PFILES = {
    .25: '20260930_110723_droop_kp0p25.csv',
    .5: '20260930_111214_droop_kp0p5.csv',
    1: '20260930_112131_droop_kp1.csv',
    2: '20260930_112429_droop_kp2.csv',
    4: '20260930_112955_droop_kp4.csv',
    250: '20261007_105005_kp250_20to30c_oscillation.csv',
}
PIFILES = {
    .1: ('pi_kp_20_ki_0p1_20261019_093424_268559.csv', '3'),
    .2: ('pi_kp_20_ki_0p2_20261019_095648_364327.csv', '2'),
    .5: ('pi_kp_20_ki_0p5_20261019_101544_769937.csv', '3'),
}
COLORS = ['#2166ac', '#d17a15', '#a5243d']
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': .18})


def read(path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def arrays(rows):
    t = np.array([float(r['time_s']) for r in rows])
    T = np.array([float(r['temperature_C']) for r in rows])
    if len(t) < 2 or not np.all(np.diff(t) > 0) or not np.isfinite(T).all():
        raise ValueError('Invalid or nonmonotonic trace')
    if any(r['safety'] != 'OK' for r in rows):
        raise ValueError('Safety fault in retained measurements')
    for r in rows:
        u = int(r['pwm'])
        heat, cool = (u, 0) if r['heat_cool'] == '1' else (0, u)
        if (int(r['heat_pwm_firmware']), int(r['cool_pwm_firmware'])) != (heat, cool):
            raise ValueError('Firmware PWM fields disagree')
    return t-t[0], T


def metrics(rows, label, source, direction):
    t, T = arrays(rows)
    target = float(rows[0]['setpoint_C'])
    initial = float(T[0]); delta = target-initial
    sign = 1 if delta > 0 else -1
    progress = sign*(T-initial)
    def crossing(level):
        ix = np.flatnonzero(progress >= level)
        if len(ix) == 0:
            return None
        i = int(ix[0])
        if i == 0:
            return float(t[0])
        return float(t[i-1]+(level-progress[i-1])/(progress[i]-progress[i-1])*(t[i]-t[i-1]))
    c10, c90 = crossing(.1*abs(delta)), crossing(.9*abs(delta))
    inside = abs(T-target) <= .2+1e-9
    suffix_inside = np.logical_and.accumulate(inside[::-1])[::-1]
    valid = np.flatnonzero(suffix_inside & (t[-1]-t >= 60))
    tail60 = T[t >= t[-1]-60]
    tail20 = T[t >= t[-1]-20]
    excursion = max(0., float(np.max(sign*(T-target))))
    u = np.array([float(r['pwm'])*(1 if r['heat_cool']=='1' else -1) for r in rows])
    return dict(label=label, source=str(source.relative_to(ROOT)), direction=direction,
                Kp=float(rows[0]['Kp_pwm_per_C']),
                Ki=float(rows[0].get('Ki_pwm_per_C_s') or 0), samples=len(rows),
                duration_s=float(t[-1]), initial_C=initial, target_C=target,
                min_C=float(T.min()), max_C=float(T.max()),
                overshoot_C=excursion, overshoot_pct=100*excursion/abs(delta),
                target_rise_10_90_s=None if c10 is None or c90 is None else c90-c10,
                settle_pm0p2_C_s=None if len(valid)==0 else float(t[valid[0]]),
                tail60_mean_C=float(tail60.mean()), tail60_error_C=float(target-tail60.mean()),
                tail20_mean_C=float(tail20.mean()), tail20_error_C=float(target-tail20.mean()),
                median_sample_s=float(np.median(np.diff(t))),
                applied_fullscale_samples=int(np.count_nonzero(abs(u)==255)),
                computed_saturated_samples=sum(r.get('saturated')=='1' for r in rows),
                tail60_peak_to_peak_C=float(np.ptp(tail60)))


def savefig(fig, name):
    fig.savefig(FIG / (name+'.png'), dpi=170)
    fig.savefig(FIG / (name+'.svg'))
    plt.close(fig)


def fmt(x, digits=2):
    return '未达到/未确认' if x is None else f'{x:.{digits}f}'


def main():
    OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    manifest = {}; result = []; ps = {}; pis = {}
    for kp, name in PFILES.items():
        path = ROOT/'Module_5/data'/name
        manifest[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        rows = [r for r in read(path) if r['p_active']=='1']
        if {(float(r['setpoint_C']), float(r['Kp_pwm_per_C'])) for r in rows} != {(30., kp)}:
            raise ValueError('Unexpected P settings')
        result.append(metrics(rows, f'P Kp={kp:g}', path, 'up'))
        ps[kp] = rows
    for ki, (name, run) in PIFILES.items():
        path = M/'data/physical'/name
        manifest[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        rows = [r for r in read(path) if r['event']=='measurement' and
                r['control_active']=='1' and r['run_id']==run]
        if {(r['mode'], float(r['Kp_pwm_per_C']), float(r['Ki_pwm_per_C_s']),
             int(r['pwm_limit']),r['anti_windup']) for r in rows} != {('PI',20.,ki,255,'1')}:
            raise ValueError('Unexpected PI settings')
        groups = []
        for r in rows:
            if not groups or groups[-1][0] != r['setpoint_C']:
                groups.append((r['setpoint_C'], []))
            groups[-1][1].append(r)
        if [float(g[0]) for g in groups] != [20.,30.,20.]:
            raise ValueError('Missing matched PI up/down steps')
        for direction, (_, segment) in zip(['up','down'], groups[1:]):
            result.append(metrics(segment, f'PI Ki={ki:g}', path, direction))
        pis[ki] = rows

    # Three illustrative P gains. Kp=4 is an observed stable historical example,
    # not an established optimum or a matched counterpart of PI Kp=20.
    for kp in [.25,4,250]:
        rows = ps[kp]; t,T = arrays(rows)
        u = [int(r['pwm'])*(1 if r['heat_cool']=='1' else -1) for r in rows]
        fig, ax = plt.subplots(2,1,sharex=True,figsize=(10,5.6),layout='constrained')
        fig.suptitle(f'Historical P experiment | Kp={kp:g} PWM/°C | heating only')
        ax[0].plot(t,T,label='Measured',color=COLORS[0]); ax[0].axhline(30,ls='--',color='black',label='Target')
        ax[0].set_ylabel('Temperature (°C)'); ax[0].legend(loc='best')
        ax[1].step(t,u,where='pre',color=COLORS[1]); ax[1].set_ylabel('Reported signed PWM')
        ax[1].set_xlabel('Time from first active measurement (s)')
        savefig(fig, experiment_stem(kp))
    for ki,rows in pis.items():
        t,T=arrays(rows); target=np.array([float(r['setpoint_C']) for r in rows])
        fig,ax=plt.subplots(4,1,sharex=True,figsize=(11,9),layout='constrained')
        fig.suptitle(f'Physical PI | Kp=20, Ki={ki:g} | PWM limit=255, anti-windup ON')
        ax[0].plot(t,T,label='Measured',color=COLORS[0]);ax[0].step(t,target,where='post',ls='--',color='black',label='Target')
        ax[0].set_ylabel('Temperature (°C)');ax[0].legend(loc='best',ncol=2)
        for a, keys, labels in [(ax[1],['reported_signed_pwm','sent_signed_pwm'],['Firmware reported','Next sent']),
                               (ax[2],['p_term_pwm','i_term_pwm'],['P term','I term'])]:
            for key,label,color in zip(keys,labels,COLORS):
                a.plot(t,[float(r[key]) for r in rows],label=label,color=color)
            a.set_ylabel('PWM');a.legend(loc='best',ncol=2)
        ax[3].plot(t,target-T,color=COLORS[0]);ax[3].axhspan(-.2,.2,color='green',alpha=.12)
        ax[3].set_ylabel('Target − T (°C)');ax[3].set_xlabel('Time from initial 20°C conditioning (s)')
        savefig(fig, experiment_stem(20, ki))
    fig,ax=plt.subplots(2,2,figsize=(12,7),layout='constrained')
    fig.suptitle('PI comparison | Kp=20, PWM limit=255 | steps aligned separately')
    for ki,color in zip(PIFILES,COLORS):
        rows=pis[ki]; groups=[]
        for r in rows:
            if not groups or groups[-1][0]!=r['setpoint_C']:groups.append((r['setpoint_C'],[]))
            groups[-1][1].append(r)
        for col,(_,rr) in enumerate(groups[1:]):
            t,T=arrays(rr);ax[0,col].plot(t,T,label=f'Ki={ki:g}',color=color)
            ax[1,col].plot(t,T,label=f'Ki={ki:g}',color=color)
    for col,target in enumerate([30,20]):
        ax[0,col].set_title('Heating 20→30°C' if col==0 else 'Cooling 30→20°C')
        for row in range(2):
            ax[row,col].axhline(target,color='black',ls='--');ax[row,col].axhspan(target-.2,target+.2,color='green',alpha=.12)
            ax[row,col].set_ylabel('Temperature (°C)');ax[row,col].legend()
        ax[1,col].set_ylim(target-1.25,target+1.05);ax[1,col].set_xlabel('Time after step (s)')
    savefig(fig,'pi_aligned_comparison')

    # Historical high-gain period: same explicit late-time peak criterion used
    # by Module 5 analysis, with Arduino t>=90 s and peak >30.5°C.
    high=ps[250]; peaks=[]
    for a,b,c in zip(high,high[1:],high[2:]):
        if float(b['time_s'])>=90 and float(a['temperature_C'])<float(b['temperature_C'])>=float(c['temperature_C']) and float(b['temperature_C'])>30.5:
            peaks.append(float(b['time_s']))
    period=float(np.mean(np.diff(peaks))) if len(peaks)>=2 else None
    with (OUT/'step_metrics.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    payload=dict(input_sha256=manifest,metrics=result,exp_p_kp_250_late_peak_times_arduino_s=peaks,
                 exp_p_kp_250_late_period_s=period,
                 settling_definition='Within target ±0.2 C through record end, >=60 s observed after settling',
                 rise_definition='First 10%-to-90% crossings of target minus first post-step measured T; interpolated',
                 tail_definition='Final 60 s; historical P droop comparison also includes final 20 s')
    (OUT/'analysis_results.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
    lines=['# P / PI 实验分析（2026-10-19）','',
           '按用户决定，使用 Module 5 的历史 P 数据和 10月19日三组 PI 数据。旧 P 数据明确保留；此前作废的 Module 6 记录不参与。原始 CSV 未修改。','',
           '## 结论','',
           '- P 增益从0.25提高至4时，30°C目标下末段误差明显缩小，但仍有 droop；Kp=250 的记录出现超调和持续振荡。',
           '- PI 三组均完成20→30→20°C，固定 Kp=20，Ki=0.1、0.2、0.5；PWM上限255，anti-windup开启。',
           '- Ki增加使升温最终修正更快，同时增大超调。降温稳定时间不是单调变化，不能声称所有方向均更快。',
           '- 本组 Ki=0.2 可作为低超调与速度间的折中；Ki=0.5 升温最快，但约有0.82°C升温超调和1.08°C降温过冲。这不是全局最优参数的证明。','',
           '## PI 定量结果','',
           '| Ki | 方向 | 10–90%响应时间/s | 超调/°C | 超调/% | 稳定时间/s | 最后60秒误差/°C |',
           '|---:|---|---:|---:|---:|---:|---:|']
    for m in result:
        if m['label'].startswith('PI'):
            lines.append(f"| {m['Ki']:g} | {'升温' if m['direction']=='up' else '降温'} | {fmt(m['target_rise_10_90_s'])} | {fmt(m['overshoot_C'])} | {fmt(m['overshoot_pct'])} | {fmt(m['settle_pm0p2_C_s'])} | {fmt(m['tail60_error_C'],4)} |")
    lines += ['','## 历史 P 结果','',
              '| Kp | 最后20秒平均温度/°C | 最后20秒误差/°C | 超调/°C | 目标±0.2°C稳定时间/s |',
              '|---:|---:|---:|---:|---:|']
    for m in result:
        if m['label'].startswith('P '):
            lines.append(f"| {m['Kp']:g} | {fmt(m['tail20_mean_C'])} | {fmt(m['tail20_error_C'])} | {fmt(m['overshoot_C'])} | {fmt(m['settle_pm0p2_C_s'])} |")
    lines += ['',f'Kp=250 后期振荡周期约 {fmt(period)} 秒。全幅输出样本数为 {result[5]["applied_fullscale_samples"]}/{result[5]["samples"]}；振荡曲线末段平均值不是稳定平衡温度。','',
              '## 机制与证据边界','',
              '误差 e=Tset−T，积分 q=∫e dt，控制输出 u=Kp e+Ki q。达到目标时 P项可接近零，但I项仍保留先前误差的记忆；继续输出与热惯性共同造成越过目标后回归。Ki=0.5降温首次经过20°C附近时，19.97°C样本的P项为+0.60而I项约−62.78 PWM，仍有显著制冷请求。',
              '三组 PI 保留段 computed_saturated 均为0，因此没有证据把本次超调归因于饱和造成的积分windup。步幅均约10°C，不能据此单独验证“步幅越大超调越大”；该点保留为现场观察及待验证假设。未对PI报告单一振荡周期：过冲回归不等于存在足够多稳定周期。','',
              '## 方法与限制','',
              '- 时间从各阶跃后第一个有效测量点起算，约有一个采样间隔的不确定性；指标描述这次记录，不提供重复实验置信区间。',
              '- 10–90%按实际初始温度到目标温度的步幅定义，线性插值首次交叉。P低增益若到不了90%目标步幅，结果为缺失，不替换成相对最终温度的响应时间。',
              '- 稳定判据：误差始终在±0.2°C内直到该段结束，且有至少60秒后续观察；不是无限时间稳定性证明。最后60秒误差不是严格无限时间稳态误差。',
              '- P droop表用最后20秒，以衔接Module 5既有表；机器可读指标另含最后60秒。接近0.01°C量级的峰值不应解释为显著超调。',
              '- 历史P记录不是三组完整的20↔30°C双向配对：低增益记录缺少降温，高增益记录从约20.95°C开始升温。不能补造缺失方向的指标，也不能宣称满足课程六组完全匹配的实验协议。',
              '- 历史P程序输出钳位为255，但旧CSV没有独立pwm_limit字段；60°C的limit_C是温度保护阈值，不是PWM上限。不同日期的环境温度、初始条件和硬件状态可能不同。',
              '- 为图示选择P Kp=0.25、4、250作为低、稳定示例、高增益；Kp=4不是已验证的最佳中增益，PI Kp=20也不满足“略低于4”的匹配关系。按用户决定复用数据，但这一课程协议差异必须保留。',
              '- P与PI的Kp不同，不能把跨组的全部速度差异单独归因于积分项。三组PI内部只改变Ki，比较依据更充分。','',
              '## 产物与下一步','',
              '- data/experiment_analysis/step_metrics.csv：12段记录的指标；analysis_results.json：定义、来源SHA256和计算结果。',
              '- figures/experiment_analysis/：三张历史P、三张PI完整轨迹，以及一张PI对齐比较图；均有PNG与SVG。',
              '- 下一步是六组对应的two-lump模拟与实验比较，再将理论、图表、参数选择和协议限制整理进A3。本脚本没有运行新的模拟。','']
    DOC.write_text('\n'.join(lines))
    print(DOC)
    for m in result:
        print(m['label'],m['direction'],'rise',fmt(m['target_rise_10_90_s']),'overshoot',fmt(m['overshoot_C']),'settle',fmt(m['settle_pm0p2_C_s']),'tailerror',fmt(m['tail60_error_C'],4))
    print('high P period',period)


if __name__=='__main__':
    main()
