"""Figures for Module_8/docs/q10_steady_state_derivation.html.

Three pictures, each carrying one sentence of the argument:

  fig01  steady state gives ONE number m, so (k, h) slide along h = (m^2 d/4) k
  fig02  that number m is very sensitive to the assumed room temperature
  fig03  steady state is the omega -> 0 limit: q' -> 0, so the phase speaker goes silent

Nothing is refitted here except the one-parameter mean-profile fit in fig02,
which repeats the same model the analysis uses (fixed room reference, fitted
base and m) so the sensitivity curve can be drawn.
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

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "Module_8"
PROC = M / "data/processed"
OUT = M / "figures/q10"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 8.5, "axes.titlesize": 9.0, "axes.labelsize": 8.4,
    "axes.grid": True, "grid.alpha": .25, "grid.linewidth": .6,
    "legend.fontsize": 7.0, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 170, "savefig.bbox": "tight", "savefig.pad_inches": .02,
})
C = dict(blue="#1f4e79", orange="#c55a11", green="#2e7d32", grey="#666666",
         red="#b03a2e", teal="#0f6e6e", purple="#6a3d9a")

X = np.array([0.0, 0.0385, 0.0895, 0.1405, 0.1915])
L, D = 0.2715, 0.01277
SUMM = list(csv.DictReader(open(PROC / "five_period_review/m08_pi_five_period_summary.csv")))
REC = {int(r["period_s"]): r for r in json.loads(
    (PROC / "transport_note/m08_transport_parameters.json").read_text())["records"]}


def channel_fits(period):
    p = PROC / f"five_period_review/m08_pi_p{int(period)}s_analysis.json"
    return json.loads(p.read_text())["analysis"]["channel_fits"]


def profile_m(means, t_inf):
    """Least-squares (theta0, m) for theta = T - t_inf with an insulated tip.

    Same model as the analysis: the room reference is fixed, the base excess
    temperature and m are fitted.  theta0 is linear, so only m needs a search.
    """
    theta = np.asarray(means, float) - t_inf
    lo, hi = 0.05, 60.0
    for _ in range(160):                       # golden section on m
        m1, m2 = lo + .382 * (hi - lo), lo + .618 * (hi - lo)
        s = []
        for m in (m1, m2):
            f = np.cosh(m * (L - X)) / np.cosh(m * L)
            th0 = float(theta @ f / (f @ f))
            s.append(float(((theta - th0 * f) ** 2).sum()))
        if s[0] < s[1]:
            hi = m2
        else:
            lo = m1
    m = .5 * (lo + hi)
    f = np.cosh(m * (L - X)) / np.cosh(m * L)
    return float(theta @ f / (f @ f)), m


def fig01():
    means = np.array([channel_fits(100)[f"rod{i}_C"]["mean_C"] for i in range(1, 6)])
    t_inf = REC[100]["mean_profile_fit"]["room_reference_C"]
    m = REC[100]["mean_profile_fit"]["m_per_m"]
    ratio = m * m * D / 4.0
    theta = means - t_inf

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.7, 2.7))
    xs = np.linspace(0, L, 200)
    f = np.cosh(m * (L - xs)) / np.cosh(m * L)
    ax1.plot(X * 100, theta, "o", ms=5, mfc="none", mec=C["blue"], mew=1.1,
             label="five measured means  $T_i-T_\\infty$")
    ax1.plot(xs * 100, theta[0] * f, color=C["orange"], lw=1.3,
             label="model, any point on the line")
    ax1.set(xlabel="distance from T1 (cm)", ylabel="$\\theta=T-T_\\infty$   (K)",
            title="one curve, one number:  $m$ = %.2f 1/m" % m)
    ax1.legend(loc="lower left", fontsize=6.8)

    kk = np.linspace(60, 280, 50)
    ax2.plot(kk, ratio * kk, color=C["orange"], lw=1.5, label="$h=(m^2d/4)\\,k$")
    ax2.axvspan(166, 172, color=C["green"], alpha=.16)
    ax2.text(169, 6.0, "aluminium\nhandbook\n166-172", fontsize=6.6, color=C["green"],
             ha="center", va="bottom")
    for k, col, dx, dy in ((100, C["grey"], 7, -13), (166, C["red"], 9, 6), (250, C["grey"], -6, -14)):
        ax2.plot([k], [ratio * k], "o", ms=5.2, color=col)
        ax2.annotate("$k$=%d → $h$=%.1f" % (k, ratio * k), (k, ratio * k), fontsize=6.7,
                     color=col, textcoords="offset points", xytext=(dx, dy),
                     ha="left" if dx > 0 else "right")
    ax2.set(xlabel="assumed $k$   (W m$^{-1}$ K$^{-1}$)",
            ylabel="implied $h$   (W m$^{-2}$ K$^{-1}$)",
            title="every point on this line fits equally well")
    ax2.legend(loc="upper left", fontsize=6.9)
    ax2.set_xlim(60, 300)
    ax2.set_ylim(4, 28)

    fig.tight_layout()
    fig.savefig(OUT / "fig01_degeneracy.png")
    plt.close(fig)
    print("fig01: m = %.4f  h/k = %.5f" % (m, ratio))


def fig02():
    means = np.array([channel_fits(100)[f"rod{i}_C"]["mean_C"] for i in range(1, 6)])
    k = 164.5
    grid = np.linspace(18.0, 27.5, 70)
    ms = [profile_m(means, t)[1] for t in grid]
    hs = [k * m * m * D / 4.0 for m in ms]

    fig, ax1 = plt.subplots(figsize=(6.7, 2.95))
    ax1.plot(grid, ms, color=C["blue"], lw=1.6, label="$m$ from the 100 s mean profile")
    ax1.set(xlabel="assumed room temperature $T_\\infty$   (°C)", ylabel="$m$   (1/m)")
    ax1.axvline(24.125, color=C["grey"], lw=.9, ls=":")
    ax1.annotate("adopted 24.13 °C\n$m$ = 5.36", xy=(24.4, 5.45), xytext=(24.9, 8.6),
                 fontsize=6.8, color=C["grey"], ha="left",
                 arrowprops=dict(arrowstyle="->", color=C["grey"], lw=.7))
    ax1.axvline(means[-1], color=C["red"], lw=.9, ls="--")
    ax1.text(means[-1] - .12, 10.2, "tip mean %.1f °C" % means[-1],
             fontsize=6.4, color=C["red"], ha="right", va="top", rotation=90)
    for t in (20, 22, 24, 26):
        mm = profile_m(means, t)[1]
        ax1.plot([t], [mm], "o", ms=4.6, color=C["orange"])
        ax1.annotate("%.2f" % mm, (t, mm), fontsize=6.5, color=C["orange"],
                     textcoords="offset points", xytext=(3, -11))
    ax1.set_xlim(17.6, 28.3)
    ax1.legend(loc="lower right", fontsize=7.0)

    ax2 = ax1.twinx()
    ax2.plot(grid, hs, color=C["orange"], lw=1.1, ls="--")
    ax2.set_ylabel("implied $h$   (W m$^{-2}$ K$^{-1}$)", color=C["orange"])
    ax2.tick_params(axis="y", colors=C["orange"])
    ax2.spines["right"].set_visible(True)
    ax2.grid(False)

    fig.tight_layout()
    fig.savefig(OUT / "fig02_room_sensitivity.png")
    plt.close(fig)
    for t in (18, 20, 22, 24, 26, 27):
        mm = profile_m(means, t)[1]
        print("fig02: T_inf %4.1f -> m %.2f -> h %.1f" % (t, mm, k * mm * mm * D / 4.0))


def fig03():
    kappa, nu = 6.80e-5, 1.20e-3
    w = np.logspace(-3.3, .25, 400)
    s = np.sqrt((nu + 1j * w) / kappa)

    fig, ax = plt.subplots(figsize=(6.7, 3.0))
    ax.plot(w, s.real, color=C["blue"], lw=1.6, label="$q$ = Re $s$  (amplitude decay)")
    ax.plot(w, s.imag, color=C["teal"], lw=1.6, label="$q'$ = Im $s$  (phase lag)")
    m = math.sqrt(nu / kappa)
    ax.axhline(m, color=C["blue"], lw=.9, ls=":")
    ax.text(.22, m * .80, "$m=\\sqrt{\\nu/\\kappa}$ = %.2f  ($\\omega\\to0$ limit)" % m,
            fontsize=6.8, color=C["blue"], ha="left")
    ax.axhline(5.3565, color=C["green"], lw=.9, ls="-.")
    ax.text(.22, 5.3565 * 1.22, "mean-profile $m$ = 5.36  (+28%)", fontsize=6.8,
            color=C["green"], ha="left")
    offs = {100: (6, 8), 200: (9, -3), 300: (-24, 5), 400: (-14, -15), 500: (2, 12)}
    for r in SUMM:
        p = int(r["period_s"])
        om = 2 * math.pi / p
        ax.plot(om, float(r["q_per_m"]), "o", ms=4.8, mfc="none", mec=C["blue"], mew=1.1)
        qpv = float(r["q_prime_per_m"])
        if qpv > 0:
            ax.plot(om, qpv, "s", ms=4.2, mfc="none", mec=C["teal"], mew=1.0)
        ax.annotate("%d s" % p, (om, float(r["q_per_m"])), fontsize=6.2, color=C["grey"],
                    textcoords="offset points", xytext=offs[p])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set(xlabel="drive frequency $\\omega$ (rad/s)  —  steady state is the $\\omega\\to0$ edge",
           ylabel="spatial rate  (1/m)",
           title="at $\\omega\\to0$: $q$ saturates at $m$, and $q'$ falls to zero")
    ax.legend(loc="lower right", fontsize=7.0)

    fig.tight_layout()
    fig.savefig(OUT / "fig03_dc_limit.png")
    plt.close(fig)
    print("fig03: m(omega->0) = %.2f ; sqrt(nu/kappa) = %.2f" % (m, math.sqrt(nu / kappa)))


if __name__ == "__main__":
    fig01()
    fig02()
    fig03()


