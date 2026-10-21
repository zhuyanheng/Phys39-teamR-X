"""Analyze the selected Module 6 P/PI measurements; no Module 5 P data or serial IO."""
import csv
import hashlib
import json
import os
from pathlib import Path
from file_naming import experiment_stem

os.environ.setdefault('MPLCONFIGDIR','/private/tmp/phys39_analysis_mpl')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

M=Path(__file__).resolve().parents[2];ROOT=M.parent
OUT=M/'data/experiment_analysis';FIG=M/'figures/experiment_analysis'
DOC=M/'docs/experiment_analysis_2026-10-21.md'
SELECTIONS=[
 ('P',.25,0.,'p_kp_0p25_20261021_103204_751306.csv','1'),
 ('P',4.,0.,'p_kp_4_20261021_103836_296838.csv','1'),
 ('P',100.,0.,'p_kp_100_20261021_105056_326633.csv','1'),
 ('PI',20.,.1,'pi_kp_20_ki_0p1_20261019_093424_268559.csv','3'),
 ('PI',20.,.2,'pi_kp_20_ki_0p2_20261019_095648_364327.csv','2'),
 ('PI',20.,.5,'pi_kp_20_ki_0p5_20261019_101544_769937.csv','3'),
]
COLORS=['#2166ac','#d17a15','#a5243d']
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18})


def read(path):
 with Path(path).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))


def arrays(rows):
 t=np.array([float(r['time_s']) for r in rows]);T=np.array([float(r['temperature_C']) for r in rows])
 if len(t)<2 or not np.all(np.diff(t)>0) or not np.isfinite(T).all():raise ValueError('Invalid time/temperature')
 if any(r['safety']!='OK' for r in rows):raise ValueError('Safety fault in retained run')
 for r in rows:
  pwm=int(r['pwm']);expected=(pwm,0) if r['heat_cool']=='1' else (0,pwm)
  if (int(r['heat_pwm_firmware']),int(r['cool_pwm_firmware']))!=expected:raise ValueError('PWM mismatch')
 return t-t[0],T


def selected_runs():
 runs=[]
 for mode,kp,ki,file,rid in SELECTIONS:
  path=M/'data/physical'/file
  rows=[r for r in read(path) if r['event']=='measurement' and r['control_active']=='1' and r['run_id']==rid]
  arrays(rows)
  if {(r['mode'],float(r['Kp_pwm_per_C']),float(r['Ki_pwm_per_C_s']),int(r['pwm_limit']),r['anti_windup']) for r in rows}!={(mode,kp,ki,255,'1')}:raise ValueError('Unexpected settings: '+file)
  groups=[]
  for r in rows:
   if not groups or groups[-1][0]!=r['setpoint_C']:groups.append((r['setpoint_C'],[]))
   groups[-1][1].append(r)
  if [float(g[0]) for g in groups]!=[20.,30.,20.]:raise ValueError('Incomplete target sequence: '+file)
  runs.append(dict(mode=mode,Kp=kp,Ki=ki,source=path,run_id=rid,rows=rows,groups=groups))
 return runs


def metrics(rows,label,source,direction):
 t,T=arrays(rows);target=float(rows[0]['setpoint_C']);initial=float(T[0]);delta=target-initial
 sign=1 if delta>0 else -1;progress=sign*(T-initial)
 def crossing(level):
  ix=np.flatnonzero(progress>=level)
  if not len(ix):return None
  i=int(ix[0])
  if i==0:return 0.
  return float(t[i-1]+(level-progress[i-1])/(progress[i]-progress[i-1])*(t[i]-t[i-1]))
 c10,c90=crossing(.1*abs(delta)),crossing(.9*abs(delta))
 inside=abs(T-target)<=.2+1e-9
 valid=np.flatnonzero(np.logical_and.accumulate(inside[::-1])[::-1] & (t[-1]-t>=60))
 tail=T[t>=t[-1]-60];tail20=T[t>=t[-1]-20]
 excursion=max(0.,float(np.max(sign*(T-target))))
 u=np.array([float(r['reported_signed_pwm']) for r in rows])
 # Only actual two-sided prominent maxima are eligible. One interval is a rough
 # transient estimate, not a sustained/late-time period or confidence interval.
 peaks=[]
 for i in range(1,len(T)-1):
  if t[i]<3 or T[i]<target+.2 or not T[i-1]<T[i]>=T[i+1]:continue
  left=T[(t>=t[i]-2)&(t<t[i])];right=T[(t>t[i])&(t<=t[i]+2)]
  if not len(left) or not len(right) or min(T[i]-min(left),T[i]-min(right))<.05:continue
  if not peaks or t[i]-peaks[-1]['time_s']>=2:peaks.append(dict(time_s=float(t[i]),temperature_C=float(T[i])))
 period=float(np.mean(np.diff([p['time_s'] for p in peaks]))) if len(peaks)>=2 else None
 return dict(label=label,source=str(source.relative_to(ROOT)),direction=direction,
  Kp=float(rows[0]['Kp_pwm_per_C']),Ki=float(rows[0]['Ki_pwm_per_C_s']),samples=len(rows),
  duration_s=float(t[-1]),initial_C=initial,target_C=target,min_C=float(min(T)),max_C=float(max(T)),
  overshoot_C=excursion,overshoot_pct=100*excursion/abs(delta),
  target_rise_10_90_s=None if c10 is None or c90 is None else c90-c10,
  settle_pm0p2_C_s=None if not len(valid) else float(t[valid[0]]),
  tail60_mean_C=float(tail.mean()) if t[-1]>=60 else None,
  tail60_error_C=float(target-tail.mean()) if t[-1]>=60 else None,
  tail20_mean_C=float(tail20.mean()) if t[-1]>=20 else None,
  tail20_error_C=float(target-tail20.mean()) if t[-1]>=20 else None,
  median_sample_s=float(np.median(np.diff(t))),
  applied_fullscale_samples=int(np.count_nonzero(abs(u)==255)),
  computed_saturated_samples=sum(r['saturated']=='1' for r in rows),
  tail60_peak_to_peak_C=float(np.ptp(tail)) if t[-1]>=60 else None,
  tail60_temperature_change_C=float(tail[-1]-tail[0]) if t[-1]>=60 else None,
  oscillation_period_s=period,oscillation_intervals=max(0,len(peaks)-1))


def savefig(fig,name):
 fig.savefig(FIG/(name+'.png'),dpi=170);fig.savefig(FIG/(name+'.svg'));plt.close(fig)


def fmt(x,d=2):return '未达到/未确认' if x is None else f'{x:.{d}f}'


def main():
 OUT.mkdir(parents=True,exist_ok=True);FIG.mkdir(parents=True,exist_ok=True)
 runs=selected_runs();result=[];manifest={};selection=[]
 for run in runs:
  label=f"P Kp={run['Kp']:g}" if run['mode']=='P' else f"PI Ki={run['Ki']:g}"
  manifest[str(run['source'].relative_to(ROOT))]=hashlib.sha256(run['source'].read_bytes()).hexdigest()
  selection.append({k:(str(v.relative_to(ROOT)) if k=='source' else v) for k,v in run.items() if k not in ['rows','groups']})
  for direction,(_,segment) in zip(['up','down'],run['groups'][1:]):result.append(metrics(segment,label,run['source'],direction))
  t,T=arrays(run['rows']);target=np.array([float(r['setpoint_C']) for r in run['rows']])
  fig,ax=plt.subplots(4,1,sharex=True,figsize=(11,9),layout='constrained')
  fig.suptitle(f"Physical {run['mode']} | Kp={run['Kp']:g}, Ki={run['Ki']:g} | PWM limit=255")
  ax[0].plot(t,T,label='Measured',color=COLORS[0]);ax[0].step(t,target,where='post',ls='--',color='black',label='Target');ax[0].set_ylabel('Temperature (°C)');ax[0].legend(ncol=2)
  for a,keys,labels in [(ax[1],['reported_signed_pwm','sent_signed_pwm'],['Firmware reported','Next sent']),(ax[2],['p_term_pwm','i_term_pwm'],['P term','I term'])]:
   for key,name,color in zip(keys,labels,COLORS):a.plot(t,[float(r[key]) for r in run['rows']],label=name,color=color)
   a.set_ylabel('PWM');a.legend(ncol=2)
  ax[3].plot(t,target-T,color=COLORS[0]);ax[3].axhspan(-.2,.2,color='green',alpha=.12);ax[3].set_ylabel('Target − T (°C)');ax[3].set_xlabel('Elapsed time from retained control start (s)')
  savefig(fig,experiment_stem(run['Kp'],run['Ki'] if run['mode']=='PI' else None))
 for mode in ['P','PI']:
  fig,ax=plt.subplots(2,1,figsize=(10,7),layout='constrained')
  for run,color in zip([x for x in runs if x['mode']==mode],COLORS):
   for a,(_,segment) in zip(ax,run['groups'][1:]):
    t,T=arrays(segment);a.plot(t,T,color=color,label=f"Kp={run['Kp']:g}" if mode=='P' else f"Ki={run['Ki']:g}")
  for a,target,name in zip(ax,[30,20],['Heating','Cooling']):
   a.axhline(target,color='black',ls='--');a.axhspan(target-.2,target+.2,color='green',alpha=.12);a.set_title(name);a.set_xlabel('Time after step (s)');a.set_ylabel('Temperature (°C)');a.legend()
  fig.suptitle('Physical '+mode+' comparison; steps aligned separately');savefig(fig,mode.lower()+'_aligned_comparison')
 with (OUT/'step_metrics.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
 payload=dict(input_sha256=manifest,selected_runs=selection,metrics=result,
  P_data_source='Module 6 measurements collected 2026-10-21; Module 5 P excluded',
  settling_definition='Within target ±0.2 C through record end, >=60 s later observation',
  tail_definition='Final 60 s only when segment duration >=60 s; otherwise null. Finite-record error, not proved steady state.',
  period_definition='Prominent positive peaks above target+0.2 C; >=0.05 C local prominence over ±2s and >=2s spacing. One interval is a rough transient estimate.')
 (OUT/'analysis_results.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
 lines=['# 当前 P / PI 实验分析（2026-10-21）','',
 '使用10月21日新P（Kp=0.25、4、100）与10月19日PI（Kp=20，Ki=0.1、0.2、0.5）。Module 5 P数据不再参与A3。三组新P原始内容不变，保留连接时间戳，文件名按实际模式和增益归档。','',
 '| 模式 | Kp | Ki | 方向 | 记录时长/s | 10–90%/s | 超调/°C | 稳定时间/s | 最后60秒误差/°C | 最后20秒误差/°C |',
 '|---|---:|---:|---|---:|---:|---:|---:|---:|---:|']
 for m in result:lines.append(f"| {'P' if m['Ki']==0 else 'PI'} | {m['Kp']:g} | {m['Ki']:g} | {m['direction']} | {fmt(m['duration_s'])} | {fmt(m['target_rise_10_90_s'])} | {fmt(m['overshoot_C'])} | {fmt(m['settle_pm0p2_C_s'])} | {fmt(m['tail60_error_C'],4)} | {fmt(m['tail20_error_C'],4)} |")
 lines += ['', '## 结论与限制','',
 '- 新P与模拟使用相同增益0.25、4、100，均有目标20→30→20°C，修复了旧P缺少降温及250/100不匹配的问题。',
 '- Kp=100升温最高33.21°C，降温最低19.77°C；两段分别约45与56秒，无法确认持续60秒稳定，最后60秒均值留空而不是用整段均值冒充稳态。',
 '- 高P升温两个明显峰值（33.21、30.58°C）相隔约17.81秒，振荡幅度下降；仅一个峰间间隔，不能当作精确持续振荡周期。降温缺少足够周期，周期留空。',
 '- Kp=0.25初始段约26秒，降温段约75秒且仍漂移，不能声称充分预稳态；所有初始温度和观测时长都明确记录。',
 '- 三组P/PI共同目标和限幅一致，但分两天测量，室温没有独立逐次记录；原模型23.19°C是名义参考，不能声称等于新实验实测室温。',
 '- 新P中增益仍为4，而PI使用20，不满足PI略低于中增益P的严格配对。不能把跨模式速度差异完全归因于积分。',
 '- 当前PI三组结论不变：Ki增大加快最终升温修正并增大超调，降温稳定时间不单调。',
 '- 旧Module 5记录保留；旧报告和退役Kp250图在 archive/2026-10-21_pre_new_p/，不再作为当前证据。',
 '', '## 当前来源','']
 for r in selection:lines.append(f"- {r['mode']} Kp={r['Kp']:g}, Ki={r['Ki']:g}, run_id={r['run_id']}: `{r['source']}`")
 DOC.write_text('\n'.join(lines)+'\n')
 for m in result:print(m['label'],m['direction'],'rise',fmt(m['target_rise_10_90_s']),'over',fmt(m['overshoot_C']),'settle',fmt(m['settle_pm0p2_C_s']),'tail60',fmt(m['tail60_error_C'],4),'period',fmt(m['oscillation_period_s']))
 return payload

if __name__=='__main__':main()
