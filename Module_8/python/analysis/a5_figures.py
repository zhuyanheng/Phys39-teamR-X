"""Assemble A5 figures and metrics from frozen measurements and course CSV exports."""

import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from angstrom_fit import fit_trace
from control_comparison import inspect

MODULE = Path(__file__).resolve().parents[2]
ROOT = MODULE.parent
PROCESSED = MODULE / "data/processed"
OUTPUT = PROCESSED / "a5"
FIGURES = MODULE / "figures/a5"
SIM = MODULE / "data/simulation/a5"
PERIODS = (100, 200, 300, 400, 500)
RODS = [f"rod{i}_C" for i in range(1, 6)]
COLORS = ["#53808a", "#4275b7", "#135668", "#bc6b29", "#8b4380"]
OBS, THEORY, MODEL = "#254e70", "#cc602b", "#16836b"

plt.rcParams.update({
    "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.18, "legend.frameon": False,
    "axes.labelcolor": "#182a38", "text.color": "#182a38",
})


def read_json(path):
    return json.loads(path.read_text())


def save(fig, name):
    fig.savefig(FIGURES / f"a5_{name}.png", dpi=250)
    plt.close(fig)


def lag(ref, signal):
    return float(np.degrees(np.angle(np.exp(1j * (ref["phase_rad"] - signal["phase_rad"])))))


def rms(y):
    return float(np.sqrt(np.mean(y ** 2)))


def tracking(t, measured, requested, period, saturated):
    f = fit_trace(t, measured, period)
    ref = fit_trace(t, requested, period)
    return {
        "mean_error_C": f["mean_C"] - ref["mean_C"],
        "amplitude": f["amplitude_C"],
        "amplitude_ratio": f["amplitude_C"] / ref["amplitude_C"],
        "lag_deg": lag(ref, f),
        "rms_C": rms(measured - requested),
        "saturated_samples": int(np.count_nonzero(saturated)),
    }


def course_export(mode, period):
    path = SIM / f"m08_course_{mode}_{period}s.csv"
    with path.open() as stream:
        settings = json.loads(stream.readline().removeprefix("# "))
        raw = np.genfromtxt(stream, delimiter=",", names=True)
    drive = settings["drive"]
    assert (drive["Ta"], drive["Tb"], drive["period"], drive["kp"], drive["ki"]) == (
        35, 5, period, 19.5, 0.12 if mode == "pi" else 0)
    assert settings["rod"]["length_m"] == .27
    dt = np.median(np.diff(raw["time_s"]))
    stop = int(round(float(raw["time_s"][-1] + dt), 3) // period) * period
    if period == 100:
        # Common simulated interval for P and PI, independent of export time.
        stop = 1000
    start = stop - 3 * period
    kept = raw[(raw["time_s"] >= start) & (raw["time_s"] < stop)]
    t = kept["time_s"] - start
    assert t[0] <= dt + .011 and t[-1] >= 3 * period - 2 * dt
    # The exported setpoint and timestamps independently verify the phase origin.
    ref = 35 + 5 * np.sin(2 * np.pi * t / period)
    assert max(abs(ref - kept["setpoint_C"])) < .05
    return t, kept, settings, [start, stop]


def control_figures():
    summary = read_json(PROCESSED / "control_comparison/m08_feedforward_p_pi_p100s_comparison.json")
    fig, ax = plt.subplots(2, sharex=True, figsize=(8.2, 3.35), layout="constrained")
    for c, run in zip((THEORY, OBS, MODEL), summary["runs"]):
        t, data, _ = inspect(run["mode"], Path(run["source"]).name, period=100)
        ax[0].plot(t, data["tec_C"], color=c, label=run["mode"], lw=1.2)
        ax[1].plot(t, data["rod1_C"], color=c, lw=1.2)
    ax[0].plot(t, data["setpoint_C"], color="#3b4148", ls=":", label="TEC request")
    ax[0].legend(ncol=4, loc="lower right", fontsize=9)
    ax[0].set_ylabel("TEC (°C)")
    ax[1].set(xlabel="Time since selected cycle boundary (s)", ylabel="Rod T1 (°C)", xlim=(0, 300))
    save(fig, "control_measured")

    fig, ax = plt.subplots(2, sharex=True, figsize=(8.2, 3.15), layout="constrained")
    result = {}
    for mode, c in [("p", OBS), ("pi", MODEL)]:
        t, raw, settings, interval = course_export(mode, 100)
        metric = tracking(t, raw["T0_C"], raw["setpoint_C"], 100, abs(raw["duty_percent"]) >= 99.99)
        cycles = [
            fit_trace(t[(t >= i*100) & (t < (i+1)*100)], raw["T0_C"][(t >= i*100) & (t < (i+1)*100)], 100)
            for i in range(3)
        ]
        metric["cycle_mean_span_C"] = float(np.ptp([f["mean_C"] for f in cycles]))
        amplitudes = [f["amplitude_C"] for f in cycles]
        metric["cycle_amplitude_span_fraction"] = float(np.ptp(amplitudes) / np.mean(amplitudes))
        metric["cycle_phase_span_rad"] = float(np.ptp(np.unwrap([f["phase_rad"] for f in cycles])))
        metric["interval_s"] = interval
        metric["settings"] = settings
        result[mode] = metric
        ax[0].plot(t, raw["T0_C"], color=c, lw=1.35, label=mode.upper())
        ax[1].plot(t, raw["duty_percent"], color=c, lw=1.1)
    ax[0].plot(t, raw["setpoint_C"], color="#3b4148", ls=":", label="Model request")
    ax[0].legend(loc="upper right", ncol=3, fontsize=9)
    ax[0].set_ylabel("Model T0 (°C)")
    ax[1].set(xlabel="Time since selected cycle boundary (s)", ylabel="Signed duty (%)", xlim=(0, 300))
    save(fig, "control_simulation")
    return result


def lengths_and_spatial(reviews, thermal, x, length):
    # The four positive-loss periods define a descriptive common pair. All five
    # period estimates remain in the figure and table.
    valid = [r["analysis"]["transport"] for r in reviews if r["analysis"]["transport"]["nu_per_s"] > 0]
    kappa = float(np.median([r["kappa_m2_s"] for r in valid]))
    nu = float(np.median([r["nu_per_s"] for r in valid]))
    curve_period = np.linspace(100, 500, 401)
    s = np.sqrt((nu + 2j*np.pi/curve_period)/kappa)
    fig, axs = plt.subplots(1, 3, sharex=True, figsize=(8.2, 2.65), layout="constrained")
    curves = [np.full_like(curve_period, 100*math.sqrt(kappa/nu)), 100/s.real, 100/s.imag]
    labels = [r"Mean excess: $1/m$", r"Amplitude: $1/q$", r"Phase: $1/q^\prime$"]
    for ax, curve, label in zip(axs, curves, labels):
        ax.plot(curve_period, curve, color=MODEL, label="Shared model")
        ax.set(title=label, xlabel="Period (s)", xticks=[100, 300, 500])
    axs[0].set_ylabel("Characteristic length (cm)")
    fig2, axs2 = plt.subplots(2, 2, figsize=(8.15, 4.0), layout="constrained")
    mean_ax, amp_ax, phase_ax, loss_ax = axs2.flatten()
    xx = np.linspace(0, x[-1], 150)
    rows = []
    for i, (review, thermal_record) in enumerate(zip(reviews, thermal)):
        p = review["period_s"]
        a = review["analysis"]
        fit = a["channel_fits"]
        q, qp = (a["finite_periodic_fit"][k] for k in ("q_per_m", "q_prime_per_m"))
        dq, dqp = np.sqrt(np.diag(a["finite_q_qprime_covariance_of_mean"]))
        mrec = thermal_record["mean_profile_fit"]
        mean_length = 100 / mrec["m_per_m"]
        # Sensitivity band, not a statistical interval, because ambient was unmeasured.
        ambient_lengths = [100 / z["m_per_m"] for z in thermal_record["mean_fit_ambient_sensitivity"]]
        lo, hi = min(ambient_lengths + [mean_length]), max(ambient_lengths + [mean_length])
        axs[0].errorbar(p, mean_length, [[mean_length-lo], [hi-mean_length]], fmt="o", color=OBS, capsize=2)
        axs[1].errorbar(p, 100/q, 100*dq/q**2, fmt="o", color=OBS, capsize=2)
        axs[2].errorbar(p, 100/qp, 100*dqp/qp**2, fmt="o", color=OBS, capsize=2)
        c = COLORS[i]
        observed = np.array([fit[k]["amplitude_C"]*np.exp(1j*fit[k]["phase_rad"]) for k in RODS])
        ratio = observed / observed[0]
        ss = q+1j*qp
        response = np.cosh(ss*(length-xx))/np.cosh(ss*length)
        for ax, observed_value, prediction in (
            (amp_ax, abs(ratio), abs(response)),
            (phase_ax, -np.unwrap(np.angle(ratio)), -np.unwrap(np.angle(response))),
        ):
            ax.plot(xx*100, prediction, c=c, lw=1.05)
            ax.plot(x[:3]*100, observed_value[:3], "o", c=c, ms=4)
            ax.plot(x[3:]*100, observed_value[3:], "o", c=c, ms=4, mfc="none")
        room = mrec["room_reference_C"]
        mean_ax.plot(x*100, [fit[k]["mean_C"]-room for k in RODS], "o", c=c, ms=3)
        mean_ax.plot(xx*100, (mrec["base_C_fitted"]-room)*np.cosh(mrec["m_per_m"]*(length-xx)) /
                     np.cosh(mrec["m_per_m"]*length), c=c, lw=1.0, label=f"{p} s")
        tr = a["transport"]
        loss_ax.errorbar(p, 1000*tr["nu_per_s"], 1000*tr["nu_se_per_s"], fmt="o", color=c, capsize=3)
        rows.append({"period_s": p, "q": q, "q_prime": qp, "q_se": float(dq),
                     "q_prime_se": float(dqp), "mean_length_cm": mean_length,
                     "mean_length_ambient_scenario_cm": [lo, hi], "transport": tr})
    axs[0].legend(fontsize=8, loc="upper right")
    save(fig, "lengths")
    mean_ax.set(ylabel="Mean excess (°C)", xlabel="Distance from T1 (cm)")
    mean_ax.legend(ncol=2, fontsize=8)
    amp_ax.set(yscale="log", ylabel="Amplitude / T1 amplitude", xlabel="Distance from T1 (cm)")
    phase_ax.set(ylabel="Phase lag from T1 (rad)", xlabel="Distance from T1 (cm)")
    loss_ax.set(ylabel="Loss rate (10⁻³ s⁻¹)", xlabel="Period (s)", xticks=PERIODS)
    loss_ax.axhline(1000*nu, color=MODEL, lw=1, ls="--", label="Shared loss")
    loss_ax.axhline(0, color="#6b757d", lw=.8)
    loss_ax.legend(fontsize=8)
    save(fig2, "spatial")
    return {"shared_kappa": kappa, "shared_nu": nu, "periods": rows}


def matched_figure(review, thermal, x, length):
    period = 300
    a = review["analysis"]
    t_start, t_stop = a["start_s"], a["end_s"]
    with (ROOT / review["source"]["snapshot"]).open() as f:
        raw = [r for r in csv.DictReader(f) if r["event"] == "measurement"
               and r["run_state"] == "RUNNING" and t_start <= float(r["time_s"]) < t_stop]
    t = np.array([float(r["time_s"]) - t_start for r in raw])
    T = np.array([[float(r[k]) for k in RODS] for r in raw])
    sp = np.array([float(r["setpoint_C"]) for r in raw])
    base_fit = a["channel_fits"]["rod1_C"]
    w = 2*np.pi/period
    m, room = (thermal["mean_profile_fit"][k] for k in ("m_per_m", "room_reference_C"))
    means = room+(base_fit["mean_C"]-room)*np.cosh(m*(length-x))/np.cosh(m*length)
    q, qp = (a["finite_periodic_fit"][k] for k in ("q_per_m", "q_prime_per_m"))
    ss = q+1j*qp
    pred = means + np.real(base_fit["amplitude_C"]*np.exp(1j*(w*t[:, None]+base_fit["phase_rad"]))
                           *np.cosh(ss*(length-x))/np.cosh(ss*length))
    ts, sim, settings, sim_interval = course_export("pi", period)
    xp = np.array(settings["rod"]["sensor_fractions"]) * settings["rod"]["length_m"]
    interpolated = np.array([np.interp(x, xp, row) for row in np.column_stack([sim[f"T{i}_C"] for i in range(6)])])
    ref = fit_trace(t, sp, period)
    assert abs(lag(ref, fit_trace(ts, sim["setpoint_C"], period))) < .3
    fig, axes = plt.subplots(3, 2, figsize=(8.2, 4.8), sharex=True, layout="constrained")
    summary = []
    selected = t < 2*period
    model_selected = ts < 2*period
    for i, ax in enumerate(axes.flat[:5]):
        ax.plot(t[selected], T[selected, i], c=OBS, lw=1.1, label="Measured")
        ax.plot(t[selected], pred[selected, i], c=THEORY, ls="--", lw=1.3, label="Analytical")
        ax.plot(ts[model_selected], interpolated[model_selected, i], c=MODEL, ls="-.", lw=1.15, label="Course model")
        ax.set_title(f"T{i+1} · {x[i]*100:.2f} cm", loc="left", fontsize=9)
        fits = [fit_trace(t, T[:, i], period), fit_trace(t, pred[:, i], period),
                fit_trace(ts, interpolated[:, i], period)]
        data = [dict(mean_C=f["mean_C"], amplitude_C=f["amplitude_C"], lag_deg=lag(ref, f)) for f in fits]
        summary.append({"sensor": f"T{i+1}", "measured": data[0], "analytical": data[1],
                        "course_model": data[2], "analytic_rmse_C": rms(T[:, i]-pred[:, i])})
    for ax in axes[:, 0]:
        ax.set_ylabel("Temperature (°C)")
    for ax in (axes[2, 0], axes[1, 1]):
        ax.set_xlabel("Time from setpoint phase zero (s)")
    axes[2, 1].axis("off")
    axes[2, 1].legend(*axes[0, 0].get_legend_handles_labels(), loc="center", fontsize=10)
    save(fig, "matched")
    return {"sensors": summary, "measured_interval_s": [t_start, t_stop],
            "displayed_measured_interval_s": [t_start, t_start+2*period],
            "sim_interval_s": sim_interval, "sim_displayed_interval_s": [sim_interval[0], sim_interval[0]+2*period],
            "sim_settings": settings}


def main():
    FIGURES.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    reviews = [read_json(PROCESSED / f"five_period_review/m08_pi_p{p}s_analysis.json") for p in PERIODS]
    thermal = read_json(PROCESSED / "transport_note/m08_transport_parameters.json")["records"]
    geometry = read_json(MODULE / "config/sensor_map.json")
    x, length = np.array(geometry["x_m"]), geometry["analysis_length_m"]
    control = control_figures()
    spatial = lengths_and_spatial(reviews, thermal, x, length)
    match = matched_figure(reviews[2], thermal[2], x, length)
    pi_tracking = []
    for r in reviews[:3]:
        p = r["period_s"]
        path = Path(r["source"]["raw"])
        t, data, info = inspect("PI", path.name, p)
        metric = tracking(t, data["tec_C"], data["setpoint_C"], p, np.abs(data["signed_pwm"]) >= info["pwm_limit"])
        metric.update(period_s=p, start_s=info["start_device_s"], stop_s=info["end_device_s"],
                      cycles=info["selected_cycles"], kp=info["Kp"], ki=info["Ki"])
        pi_tracking.append(metric)
    (OUTPUT / "a5_metrics.json").write_text(json.dumps({
        "control_model": control, "pi_tracking": pi_tracking, "spatial": spatial, "matched": match,
    }, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
