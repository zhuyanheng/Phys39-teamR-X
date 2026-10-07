"""Reproduce Module 6 analysis from unchanged Module 4/5 CSVs and official v3.

Run from the repository root: .venv/bin/python python/analysis/module_06_analysis.py
This program has no serial or hardware connection.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, replace
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/module_06"
FIG = ROOT / "docs/figures/module_06"
V3_PATH = ROOT / "python/Lab_6_7_modeling_tec_v3.py"
spec = importlib.util.spec_from_file_location("official_tec_v3", V3_PATH)
v3 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v3
spec.loader.exec_module(v3)

HEAT, COOL, INK, GOLD = "#b45b22", "#245a81", "#333333", "#927919"
plt.rcParams.update({"figure.figsize": (10, 5.6), "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": .18,
                     "savefig.bbox": "tight"})


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def save_csv(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def validate_trace(rows, label):
    t = np.array([float(r["time_s"]) for r in rows])
    T = np.array([float(r["temperature_C"]) for r in rows])
    if len(t) < 2 or not np.all(np.diff(t) > 0):
        raise ValueError(f"{label}: time is not strictly increasing")
    if not np.all(np.isfinite(T)) or any(r["safety"] != "OK" for r in rows):
        raise ValueError(f"{label}: invalid temperature or recorded safety fault")
    for r in rows:
        pwm, direction = int(r["pwm"]), int(r["heat_cool"])
        expected = (pwm, 0) if direction else (0, pwm)
        if (int(r["heat_pwm_firmware"]), int(r["cool_pwm_firmware"])) != expected:
            raise ValueError(f"{label}: firmware PWM fields disagree")
    return t, T


def save_figure(name):
    plt.savefig(FIG / f"{name}.png", dpi=170)
    plt.savefig(FIG / f"{name}.svg")
    plt.close()


def crossing(t, temperature, target, direction):
    hits = np.flatnonzero(direction * (temperature - target) >= 0)
    if not len(hits):
        return None
    i = int(hits[0])
    if i == 0:
        return float(t[0])
    fraction = (target - temperature[i-1]) / (temperature[i] - temperature[i-1])
    return float(t[i-1] + fraction * (t[i] - t[i-1]))


def step_estimate(summary):
    rows = read_csv(ROOT / summary["source_csv"])
    time, temperature = validate_trace(rows, summary["run_id"])
    # Trace the final contiguous command segment backwards from its selected window.
    final_index = np.flatnonzero(time <= float(summary["steady_end_s"]) + 1e-6)[-1]
    start = int(final_index)
    pwm, direction = int(summary["pwm"]), int(summary["direction"] == "HEAT")
    while start > 0 and (int(rows[start-1]["pwm"]), int(rows[start-1]["heat_cool"])) == (pwm, direction):
        start -= 1
    seg = rows[start:final_index+1]
    t = time[start:final_index+1] - time[start]
    T = temperature[start:final_index+1]
    tail = T[-40:]
    initial, final = float(T[0]), float(np.mean(tail))
    change = final - initial
    target = initial + (1-math.exp(-1)) * change
    sign = 1 if change > 0 else -1
    tau = crossing(t, T, target, sign)
    # Sensitivity to the minimum/maximum in the chosen endpoint window;
    # these are not a confidence interval and omit systematic uncertainty.
    sensitivity = sorted(crossing(t, T, initial+(1-math.exp(-1))*(f-initial), sign)
                         for f in (float(min(tail)), float(max(tail))))
    record = dict(run_id=summary["run_id"], source_csv=summary["source_csv"],
                  signed_pwm=pwm if direction else -pwm,
                  segment_start_arduino_s=float(time[start]), duration_s=float(t[-1]),
                  initial_C=initial, final_20s_mean_C=final, target_63_2_C=target,
                  tau_interpolated_s=tau,
                  endpoint_sensitivity_min_s=sensitivity[0],
                  endpoint_sensitivity_max_s=sensitivity[1],
                  final_20s_min_C=float(min(tail)), final_20s_max_C=float(max(tail)),
                  median_sample_interval_s=float(np.median(np.diff(t))),
                  has_3tau_plus_60s_duration=bool(t[-1] >= 3*tau+60))
    return record, t, T


def simulate(config, mode, duration=1800):
    results = v3.simulate(config, "one_lump", mode, duration)
    return results


def arrays(results):
    return np.array([r.time_s for r in results]), np.array([r.measured_temperature_c for r in results])


def transient_metrics(config, results, mode):
    t, T = arrays(results)
    offset = config.setpoint_c-config.initial_c
    t10 = crossing(t, T, config.initial_c+.1*offset, 1 if offset>0 else -1)
    t90 = crossing(t, T, config.initial_c+.9*offset, 1 if offset>0 else -1)
    band = .02*abs(offset)
    outside = np.flatnonzero(np.abs(T-config.setpoint_c) > band)
    settling = float(t[outside[-1]+1]) if len(outside) and outside[-1]+1 < len(t) else (0.0 if not len(outside) else None)
    return dict(controller=mode, Kp=config.kp_pwm_per_c, Ki=config.ki_pwm_per_c_s,
                zeta=v3.one_lump_pi_damping_ratio(config) if mode=="pi" else None,
                final_droop_C=config.setpoint_c-float(T[-1]),
                rise_10_to_90_s=t90-t10 if t10 is not None and t90 is not None else None,
                settling_2pct_of_initial_offset_s=settling,
                overshoot_C=max(0., float(np.max((T-config.setpoint_c)*(1 if offset>0 else -1)))),
                saturation_duration_s=sum(r.saturated for r in results)*config.dt_s,
                anti_windup=config.anti_windup, duration_s=float(t[-1]))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    summary = read_csv(ROOT / "data/module_04/steady_state.csv")
    slopes = {}
    slope_rows = []
    fig, ax = plt.subplots()
    for direction, color, marker in [("HEAT", HEAT, "o"), ("COOL", COOL, "s")]:
        group = [r for r in summary if r["direction"] == direction]
        x = np.array([int(r["pwm"])*(1 if direction=="HEAT" else -1) for r in group])
        y = np.array([float(r["steady_temperature_C"]) for r in group])
        for r in group:
            raw = read_csv(ROOT/r["source_csv"])
            validate_trace(raw, r["run_id"])
            selected = [z for z in raw if float(r["steady_start_s"]) <= float(z["time_s"]) <= float(r["steady_end_s"])]
            mean = np.mean([float(z["temperature_C"]) for z in selected])
            assert len(selected)==40 and abs(mean-float(r["steady_temperature_C"]))<=.02
        slope, intercept = np.polyfit(x, y, 1)
        slopes[direction] = float(slope)
        # Show endpoint dependence without calling it a statistical uncertainty.
        no_max = np.abs(x) < max(abs(x))
        without_max = float(np.polyfit(x[no_max], y[no_max], 1)[0])
        slope_rows.append(dict(direction=direction, chi_C_per_PWM=float(slope),
                               fit_intercept_C=float(intercept), n_points=len(x),
                               chi_excluding_max_endpoint_C_per_PWM=without_max,
                               status="provisional endpoint-window calibration"))
        ax.scatter(x, y, color=color, marker=marker, label=f"{direction}: selected windows")
        xx = np.linspace(min(x), max(x), 100)
        ax.plot(xx, intercept+slope*xx, color=color, linestyle="--", label=f"Fit: chi = {slope:.4f} C/PWM")
        for row, a, b in zip(group, x, y): ax.annotate(row["run_id"], (a,b), xytext=(4,5), textcoords="offset points", fontsize=9)
    ax.set(xlabel="Signed PWM (counts; positive heats)", ylabel="Selected-window mean temperature (C)",
           title="Module 4 susceptibility estimates | provisional steady-state windows")
    ax.legend(fontsize=9)
    save_figure("01_susceptibility")
    save_csv(OUT/"susceptibility.csv", slope_rows)

    steps = {}
    tau_rows = []
    for row in summary:
        if row["run_id"] in {"H1","H2","H3","C1","C2","C3"}:
            record, t, T = step_estimate(row)
            tau_rows.append(record)
            steps[row["run_id"]] = (record,t,T)
    save_csv(OUT/"time_constants.csv", tau_rows)
    reference, t, T = steps["H3"]
    tau = reference["tau_interpolated_s"]
    fig, axs = plt.subplots(1,2,figsize=(11,4.8))
    for ax, run, color in zip(axs,["H3","C1"],[HEAT,COOL]):
        r,t,T = steps[run]
        ax.plot(t,T,color=color,label=f"Measured {run}")
        fitted = r["final_20s_mean_C"]+(r["initial_C"]-r["final_20s_mean_C"])*np.exp(-t/r["tau_interpolated_s"])
        ax.plot(t,fitted,"--",color=INK,label="Exponential from endpoint + 63.2% time")
        ax.axhline(r["target_63_2_C"],color=GOLD,linestyle=":")
        ax.axvline(r["tau_interpolated_s"],color=GOLD,linestyle=":",label=f"tau = {r['tau_interpolated_s']:.1f} s")
        ax.set(xlabel="Time from first confirmed command sample (s)",ylabel="Temperature (C)",title=f"{run}: PWM {r['signed_pwm']:+g}")
        ax.legend(fontsize=8)
    fig.suptitle("Thermal time constant from measured steps | endpoint-sensitive estimates")
    save_figure("02_time_constants")

    droop_source = read_csv(ROOT/"Module_5/data/part_04_droop_comparison.csv")
    first_rows = read_csv(ROOT/"Module_5/data"/droop_source[0]["source_csv"])
    baseline = []
    for r in first_rows:
        if r["p_active"]=="1": break
        if r["pwm"]=="0" and r["safety"]=="OK": baseline.append(float(r["temperature_C"]))
    ambient = float(np.mean(baseline))
    chi_h,chi_c = slopes["HEAT"],slopes["COOL"]
    # H is a freely chosen scale. Only C/H and P_u/H were measured.
    base = v3.ModelConfig(ambient_c=ambient, initial_c=ambient, setpoint_c=30.,
        total_capacitance_j_per_c=tau, heat_loss_w_per_c=1.,
        tec_power_w_per_pwm=chi_c, heating_to_cooling_ratio=chi_h/chi_c,
        measured_cooling_chi_c_per_pwm=chi_c, measured_heating_chi_c_per_pwm=chi_h,
        measured_tau_s=tau, kp_pwm_per_c=2., ki_pwm_per_c_s=.01,
        pwm_limit=255., dt_s=.1, anti_windup=True)
    checks=[]
    open_rows=[]
    fig,axs=plt.subplots(1,2,figsize=(11,4.8))
    for ax,run,color in zip(axs,["H3","C1"],[HEAT,COOL]):
        r,t,T=steps[run]
        cfg=replace(base, ambient_c=23.44, initial_c=r["initial_C"], open_loop_pwm=r["signed_pwm"])
        results=simulate(cfg,"open_loop",float(t[-1]))
        ts,simT=arrays(results)
        # v3.open_loop_susceptibility selects by SETPOINT; open-loop inputs
        # must instead select by the actual command sign.
        chi_command=v3.active_tec_coefficient(cfg,cfg.open_loop_pwm)/cfg.heat_loss_w_per_c
        prediction=cfg.ambient_c+chi_command*cfg.open_loop_pwm
        interpolated=np.interp(t,np.r_[0,ts],np.r_[cfg.initial_c,simT])
        open_rows.append(dict(run_id=run, source_csv=r["source_csv"], ambient_C=23.44,
            signed_pwm=r["signed_pwm"], predicted_final_C=prediction,
            measured_final_20s_C=r["final_20s_mean_C"],
            measured_minus_predicted_C=r["final_20s_mean_C"]-prediction,
            trace_RMSE_C=float(np.sqrt(np.mean((interpolated-T)**2)))))
        ax.plot(t,T,color=color,label="Measured")
        ax.plot(ts,simT,"--",color=INK,label="Official v3: measured chi, common tau")
        ax.axhline(prediction,linestyle=":",color=GOLD,label=f"Predicted final {prediction:.2f} C")
        ax.set(xlabel="Time from first confirmed command sample (s)",ylabel="Temperature (C)",title=f"{run}: signed PWM {r['signed_pwm']:+g}")
        ax.legend(fontsize=8)
        half=simulate(replace(cfg,dt_s=.05),"open_loop",float(t[-1]))
        th,Th=arrays(half)
        analytic=prediction+(cfg.initial_c-prediction)*np.exp(-ts/tau)
        assert max(abs(simT-analytic)) < .01
        checks.append(dict(case=f"open_loop_{run}", max_error_to_analytic_C=float(max(abs(simT-analytic))),
            max_dt_halving_difference_C=float(max(abs(simT-np.interp(ts,th,Th))))))
    fig.suptitle("Open-loop validation | shared tau, separate heat/cool susceptibility")
    save_figure("03_open_loop_comparison")
    save_csv(OUT/"open_loop_comparison.csv",open_rows)

    p_rows=[]
    for summary_row in droop_source:
        raw=read_csv(ROOT/"Module_5/data"/summary_row["source_csv"])
        validate_trace(raw,summary_row["source_csv"])
        active=[r for r in raw if r["p_active"]=="1"]
        kp=float(summary_row["kp_pwm_per_C"])
        assert all(float(r["Kp_pwm_per_C"])==kp and float(r["setpoint_C"])==30. for r in active)
        end=float(active[-1]["time_s"])
        tail=[r for r in active if float(r["time_s"])>=end-20]
        measured=30-float(np.mean([float(r["temperature_C"]) for r in tail]))
        assert abs(measured-float(summary_row["measured_droop_C"]))<.0001
        cfg=replace(base,kp_pwm_per_c=kp,ki_pwm_per_c_s=0)
        results=simulate(cfg,"p",900)
        prediction=v3.predicted_p_droop(cfg)
        final=30-results[-1].measured_temperature_c
        assert abs(final-prediction)<1e-4
        L=chi_h*kp
        p_rows.append(dict(source_csv="Module_5/data/"+summary_row["source_csv"],Kp=kp,
            ambient_C=ambient, chi_heat_C_per_PWM=chi_h, loop_gain=L,
            measured_droop_C=measured,predicted_droop_C=prediction,simulated_final_droop_C=final,
            measured_minus_predicted_C=measured-prediction,
            measured_fractional_droop=measured/(30-ambient),predicted_fractional_droop=1/(1+L),
            closed_loop_tau_s=v3.predicted_p_time_constant(cfg)))
        ts,temp=arrays(results)
        ss=30-prediction
        analytic=ss+(ambient-ss)*np.exp(-ts/v3.predicted_p_time_constant(cfg))
        half=simulate(replace(cfg,dt_s=.05),"p",900)
        th,Th=arrays(half)
        checks.append(dict(case=f"P_Kp_{kp}",max_error_to_analytic_C=float(max(abs(temp-analytic))),
            max_dt_halving_difference_C=float(max(abs(temp-np.interp(ts,th,Th))))))
    save_csv(OUT/"p_droop_comparison.csv",p_rows)
    fig,ax=plt.subplots()
    kpgrid=np.linspace(0,4,200)
    ax.plot(kpgrid,(30-ambient)/(1+chi_h*kpgrid),color=INK,label="One-lump analytical droop")
    ax.scatter([r['Kp'] for r in p_rows],[r['simulated_final_droop_C'] for r in p_rows],facecolors="none",edgecolors=COOL,s=90,label="Official v3 (900 s)")
    ax.scatter([r['Kp'] for r in p_rows],[r['measured_droop_C'] for r in p_rows],color=HEAT,marker="x",s=65,label="Module 5 final-20-s mean")
    ax.set(xlabel="Kp (PWM counts/C)",ylabel="Signed steady-state error (C)",title="P-control droop | 30 C setpoint, 23.1885 C ambient reference")
    ax.legend()
    save_figure("04_p_droop")

    fig,axs=plt.subplots(2,1,figsize=(10,7),sharex=True)
    p_source=p_rows[3]["source_csv"]
    raw=[r for r in read_csv(ROOT/p_source) if r["p_active"]=="1"]
    times=np.array([float(r["time_s"]) for r in raw]);times-=times[0]
    temperatures=np.array([float(r["temperature_C"]) for r in raw])
    cfg=replace(base,initial_c=float(temperatures[0]))
    p_results=simulate(cfg,"p",float(times[-1]))
    ts,temp=arrays(p_results)
    axs[0].plot(times,temperatures,color=HEAT,label="Module 5 measured, Kp=2")
    axs[0].plot(ts,temp,"--",color=INK,label="v3, common H3 tau")
    axs[0].axhline(30,color=GOLD,linestyle=":",label="Setpoint")
    axs[0].set(ylabel="Temperature (C)",title="P-only transient comparison | Kp=2 PWM/C")
    axs[0].legend(fontsize=9)
    signed=[int(r["pwm"])*(1 if int(r["heat_cool"]) else -1) for r in raw]
    axs[1].step(times,signed,where="post",color=HEAT,label="Firmware-reported integer PWM")
    axs[1].plot(ts,[r.applied_pwm for r in p_results],"--",color=INK,label="v3 continuous PWM")
    axs[1].set(xlabel="Time from first P-active sample (s)",ylabel="Signed PWM (counts)")
    axs[1].legend(fontsize=9)
    save_figure("05_p_transient")

    configs={"P":replace(base,ki_pwm_per_c_s=0), "PI_overdamped":base,
             "PI_underdamped":replace(base,ki_pwm_per_c_s=.08)}
    metrics=[]
    fig,axs=plt.subplots(2,1,figsize=(10,7),sharex=True)
    for name,color,style in [("P",INK,"--"),("PI_overdamped",COOL,"-"),("PI_underdamped",HEAT,"-.")]:
        cfg=configs[name]; mode="p" if name=="P" else "pi"
        results=simulate(cfg,mode)
        ts,temp=arrays(results)
        metric=transient_metrics(cfg,results,mode);metric["case"]=name
        metrics.append(metric)
        axlabel=f"{name}, Ki={cfg.ki_pwm_per_c_s:g}"
        axs[0].plot(ts,temp,color=color,linestyle=style,label=axlabel)
        axs[1].plot(ts,[r.applied_pwm for r in results],color=color,linestyle=style,label=axlabel)
        # Save model data at 0.5 s cadence; the official solver still uses dt=0.1 s.
        save_csv(OUT/f"simulation_{name}.csv",[asdict(r) for r in results[::5]])
        half=simulate(replace(cfg,dt_s=.05),mode)
        th,Th=arrays(half)
        checks.append(dict(case=name,max_error_to_analytic_C=None,
            max_dt_halving_difference_C=float(max(abs(temp-np.interp(ts,th,Th))))))
    axs[0].axhline(30,color=GOLD,linestyle=":",label="Setpoint")
    axs[0].set(ylabel="Temperature (C)",title="Simulated P/PI comparison | identical initial conditions, Kp=2")
    axs[0].legend(fontsize=9)
    axs[1].set(xlabel="Simulation time (s)",ylabel="Applied signed PWM (counts)")
    axs[1].legend(fontsize=9)
    save_figure("06_p_pi_simulation")
    save_csv(OUT/"simulation_metrics.csv",metrics)
    save_csv(OUT/"numerical_checks.csv",checks)

    # Demonstrate windup in a deliberately unreachable, simulation-only setpoint.
    fig,axs=plt.subplots(2,1,figsize=(10,7),sharex=True)
    windup=[]
    for aw,color,style in [(True,COOL,"-"),(False,HEAT,"--")]:
        cfg=replace(base,setpoint_c=60,ki_pwm_per_c_s=.08,pwm_limit=15,anti_windup=aw)
        state=v3.ModelState(0,ambient,ambient)
        results=[]
        for i in range(14000):
            live=replace(cfg,setpoint_c=30) if i>=4000 else cfg
            results.append(v3.advance_model(state,live,"one_lump","pi"))
        ts,temp=arrays(results)
        post=temp[ts>400]
        windup.append(dict(anti_windup=aw,integral_PWM_at_switch=results[3999].i_pwm,
            peak_temperature_after_switch_C=float(max(post)),final_temperature_C=float(temp[-1])))
        axs[0].plot(ts,temp,color=color,linestyle=style,label=f"Anti-windup {'ON' if aw else 'OFF'}")
        axs[1].plot(ts,[r.i_pwm for r in results],color=color,linestyle=style)
    axs[0].axhline(30,color=INK,linestyle=":")
    for ax in axs:ax.axvline(400,color=GOLD,linestyle=":")
    axs[0].set(ylabel="Temperature (C)",title="Windup demonstration | simulation only, PWM limit=15")
    axs[0].legend();axs[1].set(xlabel="Time (s); setpoint 60 C to 30 C at 400 s",ylabel="Integral contribution (PWM counts)")
    save_figure("07_windup_simulation")
    save_csv(OUT/"windup_comparison.csv",windup)
    result={"source_status":"provisional Module 4 endpoint calibration; no physical PI data",
            "v3_source_url":"https://sethfraden.github.io/Phys39F26-course/downloads/Lab_6_7_modeling_tec_v3.py",
            "v3_sha256":hashlib.sha256(V3_PATH.read_bytes()).hexdigest(),
            "chi_heat_C_per_PWM":chi_h,"chi_cool_C_per_PWM":chi_c,"heating_cooling_ratio":chi_h/chi_c,
            "reference_tau_run":"H3","tau_s":tau,"tau_run_range_s":[min(r['tau_interpolated_s'] for r in tau_rows),max(r['tau_interpolated_s'] for r in tau_rows)],
            "H_is_arbitrary_normalization_not_measured":True,
            "base_config":asdict(base),"simulation_configs":{k:asdict(c) for k,c in configs.items()},
            "slopes":slope_rows,"steps":tau_rows,"open_loop":open_rows,"p_comparison":p_rows,
            "simulation_metrics":metrics,"numerical_checks":checks,"windup":windup,
            "source_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [ROOT/'data/module_04/steady_state.csv',ROOT/'Module_5/data/part_04_droop_comparison.csv']+
                [ROOT/r['source_csv'] for r in summary]+[ROOT/'Module_5/data'/r['source_csv'] for r in droop_source]}}
    (OUT/"analysis_results.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:result[k] for k in ['chi_heat_C_per_PWM','chi_cool_C_per_PWM','tau_s','tau_run_range_s','simulation_metrics','numerical_checks']},indent=2))
    return result


if __name__ == "__main__":
    main()
