"""Generate standardized numerical two-lump evidence and report figures.

No serial/hardware access. GUI screenshots and measured CSVs remain unchanged.
"""
import csv
import hashlib
import importlib.util
import json
import math
import os
import sys
from dataclasses import asdict, replace
from pathlib import Path
from file_naming import experiment_stem, simulation_stem

os.environ.setdefault('MPLCONFIGDIR','/private/tmp/phys39_a3_mpl')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

M=Path(__file__).resolve().parents[2]; ROOT=M.parent
OUT=M/'data/a3'; FIG=M/'figures/a3'; EQ=FIG/'equations'
SOURCE=M/'python/Lab_6_7_modeling_tec_v3.py'
spec=importlib.util.spec_from_file_location('a3_official_v3',SOURCE)
v3=importlib.util.module_from_spec(spec);sys.modules[spec.name]=v3;spec.loader.exec_module(v3)
spec2=importlib.util.spec_from_file_location('a3_retained',M/'python/analysis/analyze_retained_experiments.py')
ret=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(ret)
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.16})


def dumpcsv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def simulated(kp,ki,dt):
    d=v3.constants_from_measurements(.14142,.49545,73.03,10,1.5)
    cfg=replace(v3.ModelConfig(),ambient_c=23.19,initial_c=23.,
                total_capacitance_j_per_c=d.total_capacitance_j_per_c,
                heat_loss_w_per_c=d.heat_loss_w_per_c,tec_power_w_per_pwm=d.cooling_power_w_per_pwm,
                heating_to_cooling_ratio=d.heating_to_cooling_ratio,
                measured_cooling_chi_c_per_pwm=.14142,measured_heating_chi_c_per_pwm=.49545,
                measured_tau_s=73.03,kp_pwm_per_c=kp,ki_pwm_per_c_s=ki,dt_s=dt,
                coupling_w_per_c=2.,tec_capacitance_fraction=.35,pwm_limit=255.,anti_windup=True)
    state=v3.ModelState(0.,23.,23.,0.);rows=[];mode='pi' if ki else 'p'
    for i in range(round(1500/dt)):
        now=i*dt;target=20. if now<300 or now>=1000 else 30.
        cfg=replace(cfg,setpoint_c=target)
        ans=v3.advance_model(state,cfg,'two_lump',mode)
        rows.append(dict(time_s=ans.time_s,temperature_C=ans.measured_temperature_c,
                         tec_temperature_C=ans.tec_temperature_c,setpoint_C=target,
                         applied_pwm=ans.applied_pwm,p_term_pwm=ans.p_pwm,i_term_pwm=ans.i_pwm,
                         error_C=ans.error_c,saturated=int(ans.saturated)))
    return cfg,rows


def calcmetrics(rows,label,kp,ki):
    out=[]
    for direction,target,lo,hi in [('up',30.,300.,1000.),('down',20.,1000.,1500.)]:
        r=[x for x in rows if lo < x['time_s'] <= hi+1e-7 and x['setpoint_C']==target]
        t=np.array([x['time_s'] for x in r]);t-=t[0]
        T=np.array([x['temperature_C'] for x in r]);initial=T[0]
        sign=1 if direction=='up' else -1;progress=sign*(T-initial);amplitude=abs(target-initial)
        def cross(p):
            ix=np.flatnonzero(progress>=p*amplitude)
            if len(ix)==0:return None
            j=int(ix[0]);
            if j==0:return 0.
            return float(t[j-1]+(p*amplitude-progress[j-1])/(progress[j]-progress[j-1])*(t[j]-t[j-1]))
        c10,c90=cross(.1),cross(.9)
        inside=abs(T-target)<=.2+1e-9
        valid=np.flatnonzero(np.logical_and.accumulate(inside[::-1])[::-1] & (t[-1]-t>=60))
        over=max(0.,float(np.max(sign*(T-target))))
        out.append(dict(label=label,Kp=kp,Ki=ki,direction=direction,initial_C=float(initial),
                        target_C=target,max_C=float(max(T)),min_C=float(min(T)),
                        overshoot_C=over,overshoot_pct=100*over/amplitude,
                        rise_10_90_s=None if c90 is None or c10 is None else c90-c10,
                        settle_s=None if not len(valid) else float(t[valid[0]]),
                        tail60_error_C=float(target-T[t>=t[-1]-60].mean()),
                        saturated_samples=sum(x['saturated'] for x in r),duration_s=float(t[-1])))
    return out


def figure(rows,title,name,sim=False):
    fig,ax=plt.subplots(2,1,sharex=True,figsize=(10,3.2),layout='constrained',gridspec_kw={'height_ratios':[1.5,1]})
    if sim:
        t=np.array([r['time_s'] for r in rows]);T=[r['temperature_C'] for r in rows]
        target=[r['setpoint_C'] for r in rows];u=[r['applied_pwm'] for r in rows]
        xlabel='Simulation time (s)'
    else:
        t=np.array([float(r['time_s']) for r in rows]);t-=t[0]
        T=[float(r['temperature_C']) for r in rows];target=[float(r['setpoint_C']) for r in rows]
        u=[int(r['pwm'])*(1 if r['heat_cool']=='1' else -1) for r in rows]
        xlabel='Elapsed time from retained control start (s)'
    ax[0].plot(t,T,color='#1b6585',lw=1.6,label='Measured mass Tm' if sim else 'Measured temperature')
    ax[0].step(t,target,where='post',color='#333333',ls='--',lw=1,label='Setpoint')
    ax[0].set_ylabel('Temperature (°C)');ax[0].legend(ncol=2,loc='best',fontsize=9)
    ax[1].step(t,u,where='pre',color='#b05b23',lw=1);ax[1].axhline(0,color='gray',lw=.5)
    ax[1].set_ylabel('Signed PWM');ax[1].set_xlabel(xlabel)
    ax[0].set_title(title,loc='left',fontsize=11)
    fig.savefig(FIG/(name+'.png'),dpi=190);fig.savefig(FIG/(name+'.svg'));plt.close(fig)


def main():
    OUT.mkdir(parents=True,exist_ok=True);EQ.mkdir(parents=True,exist_ok=True)
    cases=[('P025',.25,0.),('P4',4.,0.),('P100',100.,0.),('PI01',20.,.1),('PI02',20.,.2),('PI05',20.,.5)]
    allmetrics=[];checks=[];stability=[];cfg=None
    for label,kp,ki in cases:
        cfg,rows=simulated(kp,ki,.05);_,fine=simulated(kp,ki,.025)
        coarseT=np.array([r['temperature_C'] for r in rows]);fineT=np.array([r['temperature_C'] for r in fine])[1::2]
        checks.append(dict(label=label,max_abs_mass_temp_difference_C=float(np.max(abs(coarseT-fineT)))))
        mm=calcmetrics(rows,label,kp,ki);allmetrics.extend(mm)
        dumpcsv(OUT/(simulation_stem(label)+'.csv'),rows)
        figure(rows,f'Two-lump simulation | Kp={kp:g}, Ki={ki:g}',simulation_stem(label),True)
        for branch,pu in [('heating',v3.heating_tec_coefficient(cfg)),('cooling',v3.cooling_tec_coefficient(cfg))]:
            ct=cfg.tec_capacitance_j_per_c;cm=cfg.measured_capacitance_j_per_c;g=cfg.coupling_w_per_c;h=cfg.heat_loss_w_per_c
            A=ct*cm;B=ct*(g+h)+cm*g;D=g*(h+pu*kp)
            zeta=B/(2*math.sqrt(A*D));kpcrit=(B*B/(4*A*g)-h)/pu
            kicrit=B*(h+pu*kp)/(A*pu)
            roots=np.roots([A,B,D,g*pu*ki] if ki else [A,B,D])
            # Independent state-matrix eigenvalues cross-check the polynomial.
            mat=np.array([[-g/ct,(g-pu*kp)/ct,pu*ki/ct],[g/cm,-(g+h)/cm,0],[0,-1,0]]) if ki else np.array([[-g/ct,(g-pu*kp)/ct],[g/cm,-(g+h)/cm]])
            eig=np.linalg.eigvals(mat)
            assert max(min(abs(x-y) for y in roots) for x in eig)<1e-10
            stability.append(dict(label=label,branch=branch,zeta_2L_P=zeta,Kp_crit=kpcrit,
                                  Ki_crit=kicrit,rho_I=ki/kicrit,
                                  eigenvalues=[{'real':float(x.real),'imag':float(x.imag)} for x in roots]))
    dumpcsv(OUT/'simulation_step_metrics.csv',allmetrics);dumpcsv(OUT/'timestep_checks.csv',checks)
    (OUT/'stability.json').write_text(json.dumps(stability,indent=2))
    (OUT/'shared_model.json').write_text(json.dumps(asdict(cfg),indent=2))
    measured=json.loads((M/'data/experiment_analysis/analysis_results.json').read_text())
    for run in ret.selected_runs():
        kp,ki=run['Kp'],run['Ki']
        figure(run['rows'],f"Experiment: {run['mode']} | Kp={kp:g}, Ki={ki:g}",
               experiment_stem(kp,ki if run['mode']=='PI' else None))
    equations={
        'one_lump':r'C\dot{T}=P_u u-H(T-T_{amb}),\qquad \tau=C/H,\quad \chi=P_u/H',
        'measured':r'\tau\dot{T}=\chi u-(T-T_{amb})',
        'p_results':r'e_{ss}=\frac{T_{set}-T_{amb}}{1+\chi K_p},\quad \tau_{cl}=\frac{\tau}{1+\chi K_p},\quad L=\chi K_p',
        'p_solution':r'T(t)=T_{ss}+(T_0-T_{ss})e^{-t/\tau_{cl}}',
        'twolump1':r'C_T\dot{T}=P_u(u)u-G(T-T_m)',
        'twolump2':r'C_m\dot{T}_m=G(T-T_m)-H(T_m-T_{amb})',
        'coeffs':r'A=C_TC_m,\quad B=C_T(G+H)+C_mG,\quad D=G(H+P_uK_p)',
        'p_second':r'A\ddot{\theta}_m+B\dot{\theta}_m+D\theta_m=0',
        'zeta':r'\omega_n=\sqrt{D/A},\qquad \zeta_{2L,P}=\frac{B}{2\sqrt{AD}}',
        'kpcrit':r'K_{p,crit}=\frac{1}{P_u}\left[\frac{B^2}{4AG}-H\right]',
        'pi_cubic':r'As^3+Bs^2+Ds+GP_uK_i=0',
        'pi_crit':r'BD>AGP_uK_i,\quad K_{i,crit}=\frac{B(H+P_uK_p)}{AP_u},\quad \rho_I=\frac{K_i}{K_{i,crit}}',
        'pi_control':r'\dot{q}=e,\quad u_P=K_pe,\quad u_I=K_iq,\quad u=\operatorname{clip}(u_P+u_I,-255,255)',
        'steady':r'\dot q=0\ \Rightarrow\ e=0\ \Rightarrow\ T_{ss}=T_{set}=55\,^{\circ}\mathrm{C}',
        'hold':r'u_{ss}=\frac{H(T_{set}-T_{amb})}{P_u}=\frac{T_{set}-T_{amb}}{\chi},\quad q_{ss}=u_{ss}/K_i',
        'gap':r'T-T_m=\frac{H}{G}(T_m-T_{amb})',
        'one_pi':r'\zeta_{1L,PI}=\frac{H+P_uK_p}{2\sqrt{CP_uK_i}}',
    }
    for name,eq in equations.items():
        fig=plt.figure(figsize=(9,.7));fig.text(.01,.5,'$'+eq+'$',fontsize=15,va='center');
        fig.savefig(EQ/(name+'.png'),dpi=220,bbox_inches='tight',pad_inches=.04);plt.close(fig)
    sources={str(SOURCE.relative_to(ROOT)):hashlib.sha256(SOURCE.read_bytes()).hexdigest()}
    sources.update(measured['input_sha256'])
    # Only Module 4 contributes calibration evidence; Module 5 P is excluded.
    for p in [ROOT/'Module_4/data/steady_state.csv',
              ROOT/'Module_4/data/module_04_heating_75pct_pwm34_20260928_103941_134734.csv',
              M/'data/model_baseline/susceptibility.csv',M/'data/model_baseline/time_constants.csv',
              M/'data/model_baseline/open_loop_comparison.csv']:
        sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for file in ['gui/two_lump/p_kp_0p25.png','gui/two_lump/p_kp_4.png','gui/two_lump/p_kp_100.png','gui/two_lump/pi_kp_20_ki_0p1.png','gui/two_lump/pi_kp_20_ki_0p2.png','gui/two_lump/pi_kp_20_ki_0p5.png']:
        p=M/'figures'/file;sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT/'provenance.json').write_text(json.dumps(dict(source_sha256=sources,
          timing='initial20:0-300s; target30:300-1000s; target20:1000-1500s; q reset only at t=0',
          origin='New standardized numerical reproductions, not extracted screenshot trajectories'),indent=2))
    print('Prepared A3 evidence. Shared C/H/Puc:',cfg.total_capacitance_j_per_c,cfg.heat_loss_w_per_c,cfg.tec_power_w_per_pwm)
    for s in stability:
        print(s['label'],s['branch'],'zeta',round(s['zeta_2L_P'],4),'kpcrit',round(s['Kp_crit'],4),'kicrit',round(s['Ki_crit'],4),'rho',round(s['rho_I'],4))
    print('dt checks',checks)

if __name__=='__main__':main()
