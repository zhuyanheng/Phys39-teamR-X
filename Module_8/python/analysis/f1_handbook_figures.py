"""Generate the explanatory figures used by Module_8/docs/f1_study_guide.html.

Numbers come from Module_8/data/processed/*.json plus one raw CSV window.
No hardware and no re-fitting: this only draws what the analysis already produced.
"""
import csv
import json
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/module8-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[3]
M = ROOT / "Module_8"
PROC = M / "data/processed"
RAW = M / "data/raw"
OUT = M / "figures/f1_handbook"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 8.5, "axes.titlesize": 9.5, "axes.labelsize": 8.5,
    "axes.grid": True, "grid.alpha": .25, "grid.linewidth": .6,
    "legend.fontsize": 7.3, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 170, "savefig.bbox": "tight", "savefig.pad_inches": .02,
})
C = dict(blue="#1f4e79", orange="#c55a11", green="#2e7d32", grey="#666666",
         red="#b03a2e", teal="#0f6e6e", purple="#6a3d9a")

TRANSPORT = json.loads((PROC / "transport_note/m08_transport_parameters.json").read_text())
SUMMARY = json.loads((PROC / "five_period_review/m08_pi_five_period_summary.json").read_text())
PERIODS = [r["period_s"] for r in SUMMARY["results"]]
X = [0.0, 0.0385, 0.0895, 0.1405, 0.1915]
L, D = 0.2715, 0.01277
RHO, CP = 2700.0, 896.0


def analysis(period):
    p = PROC / f"five_period_review/m08_pi_p{int(period)}s_analysis.json"
    return json.loads(p.read_text())


def save(fig, name):
    fig.savefig(OUT / name)
    plt.close(fig)
    print("wrote", name)


def fig01():
    fig, ax = plt.subplots(figsize=(6.6, 2.0))
    ax.set_axis_off(); ax.set_xlim(0, 10); ax.set_ylim(0, 3)
    boxes = [
        (0.10, "Sensors\nA0 = TEC, A1-A5 = rod\nT -> R -> Steinhart"),
        (2.60, "Firmware (Arduino)\ntime, phase, T_set\nOPEN / P / PI, PWM\nsafety, 500 ms DATA"),
        (5.10, "Python GUI\nplan upload, START\n6 live traces\nCSV + serial log"),
        (7.60, "Offline analysis\nsinusoid fits -> q, q'\n-> kappa, nu, k, h"),
    ]
    for x0, label in boxes:
        ax.add_patch(FancyBboxPatch((x0, 0.95), 2.15, 1.45, boxstyle="round,pad=0.06",
                                    fc="#f3f7fa", ec=C["blue"], lw=1.0))
        ax.text(x0 + 1.07, 1.68, label, ha="center", va="center", fontsize=7.0,
                color="#12324d", linespacing=1.5)
    for x0 in (2.24, 4.74, 7.24):
        ax.add_patch(FancyArrowPatch((x0, 1.45), (x0 + 0.34, 1.45), arrowstyle="-|>",
                                     mutation_scale=11, lw=1.1, color=C["grey"]))
    ax.text(5.0, 2.78, "one time base:  time_s = millis()/1000  ->  phase and samples share one clock",
            ha="center", fontsize=7.3, color=C["red"])
    ax.text(5.0, 2.46, "the GUI never closes the control loop; if heartbeats stop, the firmware switches the outputs off",
            ha="center", fontsize=7.3, color=C["grey"])
    save(fig, "fig01_pipeline.png")


def read_window(period, use_all=False):
    a = analysis(period)
    t0, t1 = a["analysis"]["start_s"], a["analysis"]["end_s"]
    src = RAW / Path(a["source"]["raw"]).name
    rows = []
    with src.open(newline="") as fh:
        for r in csv.DictReader(fh):
            if not use_all and r.get("run_state") != "RUNNING":
                continue
            try:
                t = float(r["time_s"])
            except (TypeError, ValueError):
                continue
            if t0 <= t <= t1:
                rows.append(r)
    t = np.array([float(r["time_s"]) for r in rows]) - t0
    keys = ("tec_C", "setpoint_C", "rod1_C", "rod2_C", "rod3_C", "rod4_C", "rod5_C")
    cols = {k: np.array([float(r[k]) if r[k] not in ("", "nan") else np.nan for r in rows])
            for k in keys}
    return t, cols, a


def fig02():
    t, c, a = read_window(200)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.6, 3.9), sharex=True,
                                   gridspec_kw={"height_ratios": [1, 1.3]})
    ax1.plot(t, c["setpoint_C"], color=C["red"], lw=1.0, ls="--", label="requested $T_{set}$")
    ax1.plot(t, c["tec_C"], color=C["blue"], lw=1.1, label="measured A0 (TEC)")
    ax1.set_ylabel("$T$ (°C)")
    ax1.set_ylim(29.2, 43.8)
    ax1.legend(loc="upper center", ncol=2)
    ax1.set_title("A real record: 200 s period, the last five complete cycles (10 min)\n"
                  f"A0 amplitude {a['analysis']['channel_fits']['tec_C']['amplitude_C']:.2f} °C about "
                  "35.00 °C: request and measurement overlap", fontsize=8.6)
    for i, key in enumerate(("rod1_C", "rod2_C", "rod3_C", "rod4_C", "rod5_C")):
        fit = a["analysis"]["channel_fits"][key]
        ax2.plot(t, c[key], lw=.9, color=plt.cm.viridis(i / 4.6),
                 label=f"T{i+1} x={X[i]*100:.2f} cm  B={fit['amplitude_C']:.2f} °C")
    ax2.set_xlabel("time inside the selected window (s)")
    ax2.set_ylabel("rod $T$ (°C)")
    ax2.set_ylim(25.0, 34.7)
    leg = ax2.legend(loc="lower right", ncol=2, fontsize=6.6)
    leg.get_frame().set_facecolor("white"); leg.get_frame().set_edgecolor("none")
    leg.get_frame().set_alpha(.92)
    ax2.set_title("the same five cycles seen down the rod: amplitude shrinks, peaks arrive later", fontsize=8.6)
    save(fig, "fig02_waveforms_200s.png")


def fig03():
    t, c, a = read_window(200)
    P = 200.0
    m = t <= P
    tt, yy = t[m], c["rod1_C"][m]
    fit = a["analysis"]["channel_fits"]["rod1_C"]
    mu, B, ph = fit["mean_C"], fit["amplitude_C"], fit["phase_rad"]
    w = 2 * math.pi / P
    model = mu + B * np.cos(w * tt + ph)
    fig, ax = plt.subplots(figsize=(6.6, 2.6))
    ax.plot(tt, yy, ".", ms=1.7, color="#9db4c8", label="measured T1")
    ax.plot(tt, model, color=C["orange"], lw=1.3, label="fit  $a + B\\cos(\\omega t+\\varphi)$")
    ax.axhline(mu, color=C["grey"], lw=.9, ls=":")
    ax.axhline(mu + B, color="#bbbbbb", lw=.7, ls=":")
    ax.axhline(mu - B, color="#bbbbbb", lw=.7, ls=":")
    ax.annotate("", xy=(238, mu + B), xytext=(238, mu - B),
                arrowprops=dict(arrowstyle="<->", color=C["red"], lw=1.1))
    ax.text(243, mu, "$2B$", color=C["red"], va="center", fontsize=8.5)
    ax.text(2, mu + .10, f"mean $a$ = {mu:.2f} °C", color=C["grey"], fontsize=7.4)
    imax = int(np.nanargmax(model))
    ax.axvline(tt[imax], color=C["green"], lw=.9, ls="--")
    ax.annotate(f"peak -> phase $\\varphi$ = {ph:+.2f} rad\n(T1 lags A0 by {abs(ph) - 1.6658:.2f} rad)",
                xy=(tt[imax], mu + B), xytext=(112, 33.45), color=C["green"], fontsize=7.2,
                arrowprops=dict(arrowstyle="-", color=C["green"], lw=.7))
    ax.set_xlim(-8, 266); ax.set_ylim(30.4, 34.15)
    ax.set_xlabel("time (s)"); ax.set_ylabel("T1 (°C)")
    ax.set_title("One cycle gives exactly three numbers per sensor: mean $a$, amplitude $B$, phase $\\varphi$",
                 fontsize=8.8)
    ax.legend(loc="lower left", ncol=1, fontsize=6.8)
    save(fig, "fig03_definition_one_cycle.png")


def fig04():
    fig, axes = plt.subplots(2, 2, figsize=(6.6, 4.3), sharex="col")
    for col, P in enumerate((200, 500)):
        a = analysis(P)
        ch = [f"rod{i}_C" for i in range(1, 6)]
        B = np.array([a["analysis"]["channel_fits"][c]["amplitude_C"] for c in ch])
        ph = np.unwrap([a["analysis"]["channel_fits"][c]["phase_rad"] for c in ch])
        sf = a["analysis"]["spatial_fit"]
        q, qp = sf["q_per_m"], sf["q_prime_per_m"]
        xs = np.linspace(0, .20, 60)
        ax = axes[0][col]
        ax.semilogy(np.array(X) * 100, B, "o", ms=3.6, color=C["blue"], label="all five sensors")
        ax.semilogy(np.array(X)[:3] * 100, B[:3], "s", ms=4.4, mfc="none", color=C["orange"],
                    label="used in the fit (T1-T3)")
        ax.semilogy(xs * 100, B[0] * np.exp(-q * xs), color=C["orange"], lw=1.0, ls="--")
        ax.set_ylabel(r"amplitude $B_i$ (°C)")
        ax.set_title(f"{int(P)} s:   $-\\mathrm{{slope}}(\\ln B)=q={-q:.2f}$ m$^{{-1}}$", fontsize=8.6)
        ax.legend(loc="lower left")
        ax = axes[1][col]
        ax.plot(np.array(X) * 100, ph, "o-", ms=3.6, lw=.8, color=C["teal"], label="unwrapped $\\varphi_i$")
        ax.plot(np.array(X)[:3] * 100, ph[:3], "s", ms=4.4, mfc="none", color=C["purple"],
                label="used in the fit")
        ax.plot(xs * 100, ph[0] - qp * xs, color=C["purple"], lw=1.0, ls="--")
        ax.set_xlabel("distance from T1 (cm)")
        ax.set_ylabel(r"phase $\varphi$ (rad)")
        ax.set_title(f"{int(P)} s:   $-\\mathrm{{slope}}(\\varphi)=q'={-qp:.2f}$ m$^{{-1}}$", fontsize=8.6)
        ax.legend(loc="upper right", fontsize=6.8)
    fig.suptitle("Where q and q' come from: two straight lines through the sensor amplitudes and phases",
                 fontsize=9.2, y=1.005)
    fig.tight_layout()
    save(fig, "fig04_spatial_fit.png")


def fig05():
    a = analysis(200)
    ch = [f"rod{i}_C" for i in range(1, 6)]
    raw = np.array([a["analysis"]["channel_fits"][c]["phase_rad"] for c in ch])
    wrapped = (raw + np.pi) % (2 * np.pi) - np.pi
    unwrapped = np.unwrap(raw)
    fig, ax = plt.subplots(figsize=(6.6, 2.4))
    ax.plot(np.array(X) * 100, wrapped, "o", ms=5, color=C["red"],
            label=r"what atan2 returns ($-\pi,\pi]$)")
    ax.plot(np.array(X) * 100, unwrapped, "s-", ms=4.5, color=C["teal"], lw=1.0, label="after unwrapping")
    for i in range(1, len(X)):
        ax.annotate("", xy=(X[i] * 100, unwrapped[i]), xytext=(X[i] * 100, wrapped[i]),
                    arrowprops=dict(arrowstyle="-", color="#bbbbbb", lw=.9, ls=":"))
    ax.axhline(-np.pi, color=C["grey"], lw=.8, ls="--")
    ax.text(.3, -np.pi + .1, r"$-\pi$", color=C["grey"], fontsize=7.5)
    ax.set_xlabel("distance from T1 (cm)"); ax.set_ylabel(r"$\varphi$ (rad)")
    ax.set_title("Why unwrapping is required: T3 falls below $-\\pi$, so its raw atan2 value jumps to +2.5")
    ax.legend(loc="lower left", ncol=2)
    save(fig, "fig05_unwrap.png")


def records():
    return {int(r["period_s"]): r for r in TRANSPORT["records"]}


def fig06():
    r = records()[500]
    a = analysis(500)["analysis"]["channel_fits"]
    q, qp = r["q_per_m"], r["q_prime_per_m"]
    mfit = r["mean_profile_fit"]["m_per_m"]
    a0, Tinf = a["rod1_C"]["mean_C"], r["mean_profile_fit"]["room_reference_C"]
    xs = np.linspace(0, L, 160)
    ts = np.linspace(0, 500, 240)
    amean = Tinf + (a0 - Tinf) * np.cosh(mfit * (L - xs)) / np.cosh(mfit * L)
    B0 = a["rod1_C"]["amplitude_C"]
    field = amean[None, :] + (B0 * np.exp(-q * xs))[None, :] * np.cos(
        2 * np.pi * ts[:, None] / 500 - qp * xs[None, :] + a["rod1_C"]["phase_rad"])
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.6, 4.4),
                                   gridspec_kw={"height_ratios": [2.1, 1]})
    im = ax1.pcolormesh(xs * 100, ts, field, cmap="RdYlBu_r", shading="auto")
    cb = fig.colorbar(im, ax=ax1, pad=.015); cb.set_label("$T$ (°C)", fontsize=8)
    for x in X:
        ax1.axvline(x * 100, color="k", lw=.6, alpha=.5)
    ax1.set_ylabel("time (s)"); ax1.set_xlabel("distance from T1 (cm)")
    ax1.set_title("The measured temperature field, reconstructed: 500 s period, one full cycle")
    ax1.grid(False)
    ax2.plot(xs * 100, amean - Tinf, color=C["grey"], lw=1.2, label="mean profile (finite cosh, m=5.97)")
    ax2.plot(xs * 100, B0 * np.exp(-q * xs), color=C["orange"], lw=1.2, label="amplitude envelope $B_0e^{-qx}$")
    ax2.set_xlabel("distance from T1 (cm)"); ax2.set_ylabel("excess $T$ (K)")
    ax2.legend(loc="upper right")
    ax2.set_title("Two envelopes: the mean decays on 1/m scale, the oscillation on 1/q scale", fontsize=8.6)
    fig.tight_layout()
    save(fig, "fig06_wavefield.png")


def fig07():
    rec = records()
    P = sorted(rec)
    q = [rec[p]["q_per_m"] for p in P]
    qp = [rec[p]["q_prime_per_m"] for p in P]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.6))
    ax1.plot(P, q, "o-", color=C["blue"], ms=5, label="$q$ (amplitude decay)")
    ax1.plot(P, qp, "s--", color=C["teal"], ms=4.5, label="$q'$ (phase lag)")
    ax1.set_xlabel("forcing period (s)"); ax1.set_ylabel("slope (m$^{-1}$)")
    ax1.legend(); ax1.set_title("both slopes fall as the period grows", fontsize=8.6)
    ax2.plot(P, [100 / v for v in q], "o-", color=C["blue"], ms=5, label="$1/q$")
    ax2.plot(P, [100 / v for v in qp], "s--", color=C["teal"], ms=4.5, label="$1/q'$")
    ax2.plot(P, [100 / rec[p]["mean_profile_fit"]["m_per_m"] for p in P], "^:",
             color=C["grey"], ms=4.5, label="$1/m$ (mean field)")
    for x in X:
        ax2.axhline(x * 100, color="#d9d9d9", lw=.8, zorder=0)
    ax2.set_xlabel("forcing period (s)"); ax2.set_ylabel("length scale (cm)")
    ax2.legend(); ax2.set_title("three length scales; grey lines = sensor spacing", fontsize=8.6)
    fig.tight_layout(); save(fig, "fig07_q_qprime.png")


def fig08():
    res = {r["period_s"]: r for r in SUMMARY["results"]}
    P = sorted(res)
    kappa = np.array([res[p]["kappa_m2_s"] for p in P]) * 1e5
    se = np.array([res[p]["kappa_conditional_se_m2_s"] for p in P]) * 1e5
    mean = float(np.mean(kappa))
    fig, ax = plt.subplots(figsize=(6.6, 2.7))
    ax.axhspan(6.862, 7.110, color="#cfe3d4", label="6061-T6 handbook implies 6.86-7.11")
    ax.axhline(mean, color=C["blue"], lw=.9, ls=":")
    ax.errorbar(P, kappa, yerr=se, fmt="o", ms=5, color=C["blue"], capsize=3, lw=1.0,
                label=r"$\kappa=\omega/(2qq')$ with conditional fit error")
    for x, y in zip(P, kappa):
        ax.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=7, color=C["blue"])
    ax.set_xlabel("forcing period (s)"); ax.set_ylabel(r"$\kappa$ ($10^{-5}$ m$^2$/s)")
    ax.set_ylim(6.2, 7.5)
    ax.set_title(f"kappa from five independent frequencies: mean {mean:.2f}e-5, span {100*(max(kappa)-min(kappa))/mean:.1f}%")
    ax.legend(loc="lower right")
    save(fig, "fig08_kappa.png")


def fig09():
    rec = records(); P = sorted(rec)
    k = np.array([rec[p]["k_W_mK"] for p in P])
    fig, ax = plt.subplots(figsize=(6.6, 2.5))
    ax.axhspan(166, 172, color="#cfe3d4", label="6061-T6 handbook 166-172 W/(m K)")
    ax.plot(P, k, "o-", ms=5, color=C["blue"], label=r"$k=\kappa\rho c$")
    for x, y in zip(P, k):
        ax.annotate(f"{y:.0f}", (x, y), textcoords="offset points", xytext=(0, 7),
                    ha="center", fontsize=7, color=C["blue"])
    ax.set_xlabel("forcing period (s)"); ax.set_ylabel("$k$ (W/(m K))")
    ax.set_ylim(150, 178)
    ax.set_title("Conductivity: five points straddle the lower edge of the handbook band")
    ax.legend(loc="lower right")
    save(fig, "fig09_k.png")


def fig10():
    res = {r["period_s"]: r for r in SUMMARY["results"]}
    P = sorted(res)
    nu = np.array([res[p]["nu_per_s"] for p in P]) * 1e3
    se = np.array([res[p]["nu_conditional_se_per_s"] for p in P]) * 1e3
    fig, ax = plt.subplots(figsize=(6.6, 2.6))
    ax.axhspan(-3.0, 0.0, color="#f6dcd8", label="nu < 0: side *heating* -> impossible")
    ax.axhline(0, color="#999999", lw=.8)
    ax.errorbar(P, nu, yerr=se, fmt="o", ms=5, color=C["teal"], capsize=3, lw=1.0,
                label=r"$\nu=\kappa(q^2-q'^2)$ with conditional fit error")
    for x, y in zip(P, nu):
        ax.annotate(f"{y:+.2f}", (x, y), textcoords="offset points",
                    xytext=(0, 9 if y > 0 else -14), ha="center", fontsize=7, color=C["teal"])
    ax.set_xlabel("forcing period (s)"); ax.set_ylabel(r"$\nu$ ($10^{-3}$ s$^{-1}$)")
    ax.set_title("Side-loss rate: the 100 s point goes negative, so the method fails there")
    ax.legend(loc="lower right")
    save(fig, "fig10_nu.png")


def fig11():
    rec = records(); P = sorted(rec)
    hh = [(p, rec[p]["h_W_m2K"]) for p in P if rec[p].get("h_W_m2K")]
    nu_se = {r["period_s"]: r["nu_conditional_se_per_s"] for r in SUMMARY["results"]}
    fig, ax = plt.subplots(figsize=(6.6, 2.6))
    for p, v in hh:
        err = nu_se[p] * RHO * CP * D / 4
        ax.errorbar([p], [v], yerr=[err], fmt="o", ms=5, color=C["purple"], capsize=3, lw=1.0)
        ax.annotate(f"{v:.1f} ± {err:.1f}", (p, v), textcoords="offset points",
                    xytext=(0, 9), ha="center", fontsize=7, color=C["purple"])
    ax.axhline(10, color=C["grey"], ls="--", lw=.9, label="course provisional h = 10 W/(m² K)")
    ax.axvline(140, color=C["red"], lw=.8)
    ax.text(150, 4, "100 s: not reported\n(nu < 0)", color=C["red"], fontsize=7.2)
    ax.set_xlim(60, 560); ax.set_ylim(0, 26)
    ax.set_xlabel("forcing period (s)"); ax.set_ylabel("$h$ (W/(m² K))")
    ax.set_title("Side coefficient: same order as natural convection, but a factor of two spread")
    ax.legend(loc="upper left")
    save(fig, "fig11_h.png")


def fig12():
    rec = records(); P = sorted(rec)
    fac = [(p, (rec[p]["q_per_m"] ** 2 + rec[p]["q_prime_per_m"] ** 2) /
            (rec[p]["q_per_m"] ** 2 - rec[p]["q_prime_per_m"] ** 2)) for p in P]
    fig, ax = plt.subplots(figsize=(6.6, 2.5))
    ax.plot([a for a, _ in fac], [abs(b) for _, b in fac], "o-", ms=5, color=C["red"])
    ax.set_yscale("log")
    for p, v in fac:
        ax.annotate(f"{abs(v):.0f}" + (" (sign flip)" if v < 0 else ""),
                    (p, abs(v)), textcoords="offset points", xytext=(0, 8),
                    ha="center", fontsize=7, color=C["red"])
    ax.axhline(1, color="#999999", lw=.8)
    ax.set_xlabel("forcing period (s)")
    ax.set_ylabel("amplification  $(q^2+q'^2)/|q^2-q'^2|$")
    ax.set_title("Why h is fragile: nu is a difference of two nearly equal numbers")
    save(fig, "fig12_conditioning.png")


def fig13():
    rec = records(); P = sorted(rec)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.9))
    p = 200
    a = analysis(p)["analysis"]["channel_fits"]
    means = np.array([a[f"rod{i}_C"]["mean_C"] for i in range(1, 6)])
    mfit = rec[p]["mean_profile_fit"]["m_per_m"]
    Tinf = rec[p]["mean_profile_fit"]["room_reference_C"]
    xs = np.linspace(0, L, 120)
    ax1.plot(np.array(X) * 100, means, "o", ms=5, color=C["blue"], label="measured means $a_i$")
    ax1.plot(xs * 100, Tinf + (means[0] - Tinf) * np.cosh(mfit * (L - xs)) / np.cosh(mfit * L),
             color=C["green"], lw=1.2, label=f"finite cosh, m={mfit:.2f}")
    ax1.plot(xs * 100, Tinf + (means[0] - Tinf) * np.exp(-mfit * xs),
             color=C["orange"], lw=1.0, ls="--", label="semi-infinite $e^{-mx}$")
    ax1.set_xlabel("distance from T1 (cm)"); ax1.set_ylabel("mean $T$ (°C)")
    ax1.set_title("mean profile: models separate towards the tip", fontsize=8.6)
    ax1.legend(loc="lower left", fontsize=6.8)
    for m_, lab in ((5.3565, "m = 5.36 (100 s mean-profile fit)"),
                    (4.33, "m = 4.33 (A4 provisional)")):
        eps = 100 * (1 - (1 + np.exp(-2 * m_ * L)) / (1 + np.exp(-2 * m_ * (L - xs))))
        ax2.plot(xs * 100, eps, lw=1.2, label=lab)
    ax2.axhline(5, color=C["red"], ls="--", lw=.9, label="5% criterion")
    for x in X:
        ax2.axvline(x * 100, color="#d9d9d9", lw=.8, zorder=0)
    ax2.set_xlabel("distance from T1 (cm)"); ax2.set_ylabel(r"$\varepsilon_T$ (%)")
    ax2.set_title("semi-infinite error grows towards the tip", fontsize=8.6)
    ax2.legend(loc="upper left", fontsize=6.8)
    fig.tight_layout(); save(fig, "fig13_mean_profile.png")


def fig14():
    res = {r["period_s"]: r for r in SUMMARY["results"]}
    P = sorted(res)
    data = {
        "mean span / 0.1 °C": [res[p]["max_mean_span_C"] / .1 for p in P],
        "amplitude span / 5%": [res[p]["max_amplitude_span_fraction"] / .05 for p in P],
        "phase span / 0.1 rad": [res[p]["max_phase_span_rad"] / .1 for p in P],
    }
    fig, ax = plt.subplots(figsize=(6.6, 2.7))
    width = .26
    for i, (k, v) in enumerate(data.items()):
        ax.bar(np.arange(len(P)) + (i - 1) * width, v, width, label=k)
    ax.axhline(1, color=C["red"], lw=1.1, ls="--")
    ax.text(.01, 1.03, "pass limit", color=C["red"], fontsize=7.2, ha="left")
    ax.set_xticks(np.arange(len(P))); ax.set_xticklabels([f"{int(p)} s" for p in P])
    ax.set_ylabel("measured span / allowed span")
    ax.set_ylim(0, 6.6)
    ax.set_title("Settling gate: every record fails at least one criterion (bars above 1 fail)")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(.5, 1.0), fontsize=6.8)
    save(fig, "fig14_settling.png")


def fig15():
    hs = np.linspace(0, 60, 200)
    fig, ax = plt.subplots(figsize=(6.6, 2.4))
    for k_, lab in ((161.0, "k = 161"), (169.0, "k = 169")):
        ax.plot(hs, hs * D / (4 * k_), lw=1.2, label=f"$Bi_\\perp=hd/(4k)$, {lab}")
    ax.axhspan(1e-5, 0.1, color="#cfe3d4", label="Bi < 0.1: one temperature per section")
    ax.axvspan(9.3, 18.2, color="#f2e6d8", label="our inferred h range")
    ax.set_yscale("log"); ax.set_ylim(1e-5, 1)
    ax.set_xlabel("$h$ (W/(m² K))"); ax.set_ylabel(r"$Bi_\perp$")
    ax.set_title("Transverse Biot number stays far below 0.1 for any plausible h")
    ax.legend(loc="lower right", fontsize=6.8)
    save(fig, "fig15_biot.png")


def fig16():
    fig, ax = plt.subplots(figsize=(6.6, 2.6))
    ax.set_axis_off(); ax.set_xlim(0, 10); ax.set_ylim(0, 4.6)
    def box(x, y, w, h, text, fc="#f3f7fa", ec=C["blue"], size=6.9):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05", fc=fc, ec=ec, lw=.9))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
                color="#12324d", linespacing=1.45)
    def arrow(x0, y0, x1, y1, color=C["grey"]):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                     mutation_scale=9, lw=.9, color=color))
    box(.2, 3.0, 1.9, 1.1, "schedule\nT, Ta, Tb, mode\nKp, Ki")
    box(2.6, 3.0, 1.8, 1.1, "phase\naccumulator\n$T_{set}=T_a+T_b\\sin\\phi$")
    box(4.9, 3.0, 1.5, 1.1, "error\n$e=T_{set}-T_{A0}$")
    box(6.9, 3.0, 1.6, 1.1, "OPEN lookup\nP: $K_p e$\nPI: $K_p e + K_i\\!\\int\\!e$")
    box(8.9, 3.0, 0.9, 1.1, "x ratio\nif $u<0$")
    box(8.9, 1.5, 0.9, 1.0, "clamp\n$\\pm 96$", fc="#fbeceb", ec=C["red"])
    box(6.9, 1.5, 1.6, 1.0, "H-bridge\nD9 / D10", fc="#fbeceb", ec=C["red"])
    box(4.6, 1.5, 1.7, 1.0, "TEC + rod\n(thermal plant)")
    box(2.4, 1.5, 1.6, 1.0, "thermistors\nA0, T1-T5")
    box(.2, 1.5, 1.6, 1.0, "500 ms record\n+ safety tests", fc="#eef6f1", ec=C["green"])
    # top row, left to right
    arrow(2.10, 3.55, 2.58, 3.55)
    arrow(4.40, 3.55, 4.88, 3.55)
    arrow(6.40, 3.55, 6.88, 3.55)
    arrow(8.50, 3.55, 8.88, 3.55)
    # down to clamp, then left along the bottom row
    arrow(9.35, 3.00, 9.35, 2.52)
    arrow(8.88, 2.00, 8.52, 2.00)
    arrow(6.90, 2.00, 6.32, 2.00)
    arrow(4.60, 2.00, 4.02, 2.00)
    arrow(2.40, 2.00, 1.82, 2.00)
    # feedback up into the schedule
    arrow(1.00, 2.52, 1.00, 2.98, C["blue"])
    ax.text(1.06, 2.72, "A0", fontsize=6.8, color=C["blue"])
    ax.text(5.0, 0.95, "The measurable boundary is T1, but the loop closes on A0. "
            "Everything downstream of the H-bridge is thermal, so it adds lag.",
            ha="center", fontsize=7.2, color=C["grey"])
    ax.text(5.0, 4.35, "control loop implemented in the firmware", ha="center", fontsize=8.6,
            color="#12324d")
    save(fig, "fig16_control_loop.png")


def fig17():
    ks = np.linspace(80, 300, 200)
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    for m_, col, lab in ((5.3565, C["blue"], "m = 5.36 (measured mean profile)"),
                         (4.33, C["orange"], "m = 4.33 (A4: assumed h=10, k=166)")):
        ax.plot(ks, m_ * m_ * ks * D / 4, color=col, lw=1.3,
                label=lab + r"  ->  $h=m^2kd/4$")
    ax.plot([164.5], [15.0], "o", ms=7, color=C["blue"], zorder=5)
    ax.annotate("our best pair\nk=164.5, h=15.0", (164.5, 15.0), textcoords="offset points",
                xytext=(-8, 18), fontsize=7.2, color=C["blue"], ha="center")
    ax.plot([166], [10], "s", ms=6, color=C["orange"], zorder=5)
    ax.annotate("A4 assumption\nk=166, h=10", (166, 10), textcoords="offset points",
                xytext=(22, -16), fontsize=7.2, color=C["orange"])
    for kk in (100, 250):
        hh = 5.3565 ** 2 * kk * D / 4
        ax.plot([kk], [hh], "|", ms=9, color=C["blue"])
        ax.annotate(f"k={kk}, h={hh:.1f}", (kk, hh), textcoords="offset points",
                    xytext=(0, -13), fontsize=6.8, color=C["blue"], ha="center")
    ax.set_xlabel("$k$ (W/(m K))"); ax.set_ylabel("$h$ (W/(m$^2$ K))")
    ax.set_title("Fixing m does NOT fix k and h: it fixes only the ratio $h/k$")
    ax.text(225, 26, "same m = 5.36,\nthree different (k, h)", fontsize=7.4, color=C["blue"],
            ha="center", linespacing=1.4)
    ax.legend(loc="upper left", fontsize=6.8)
    save(fig, "fig17_m_degeneracy.png")


if __name__ == "__main__":
    for fn in (fig01, fig02, fig03, fig04, fig05, fig06, fig07, fig08, fig09, fig10,
               fig11, fig12, fig13, fig14, fig15, fig16, fig17):
        fn()


