"""Draw the one figure behind Q7 of Module_8/docs/f1_oral_answers.html.

Compares the semi-infinite rod with the finite insulated-tip rod for the two
fields the write-up uses:

  left    mean field  (real decay constant m)   - models visibly separate
  middle  periodic amplitude (complex s = q+iq') - separation only near the tip
  right   periodic phase                         - the reflected wave bends it

All numbers come from Module_8/data/processed/; nothing is refitted here.
"""
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/module8-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
M = ROOT / "Module_8"
PROC = M / "data/processed"
OUT = M / "figures/f1_oral"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 8.5, "axes.titlesize": 8.8, "axes.labelsize": 8.3,
    "axes.grid": True, "grid.alpha": .25, "grid.linewidth": .6,
    "legend.fontsize": 7.0, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 170, "savefig.bbox": "tight", "savefig.pad_inches": .02,
})
C = dict(blue="#1f4e79", orange="#c55a11", green="#2e7d32", grey="#666666",
         red="#b03a2e", teal="#0f6e6e")

X = np.array([0.0, 0.0385, 0.0895, 0.1405, 0.1915])
L = 0.2715

TRANSPORT = json.loads((PROC / "transport_note/m08_transport_parameters.json").read_text())
REC = {int(r["period_s"]): r for r in TRANSPORT["records"]}


def fits(period):
    p = PROC / f"five_period_review/m08_pi_p{int(period)}s_analysis.json"
    return json.loads(p.read_text())["analysis"]["channel_fits"]


def finite(x, s, real=False):
    """Insulated-tip finite rod, normalised to 1 at x = 0."""
    f = np.cosh if real else np.cosh
    return f(s * (L - x)) / f(s * L)


def main():
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(6.9, 2.55))
    xs = np.linspace(0, L, 200)

    # ---------- mean field ----------
    r = REC[100]
    m = r["mean_profile_fit"]["m_per_m"]
    fin = finite(xs, m, real=True)
    semi = np.exp(-m * xs)
    ax1.plot(xs * 100, fin, color=C["green"], lw=1.3, label="finite (cosh)")
    ax1.plot(xs * 100, semi, color=C["orange"], lw=1.1, ls="--", label="semi-infinite (exp)")
    a = fits(100)
    means = np.array([a[f"rod{i}_C"]["mean_C"] for i in range(1, 6)])
    Tinf = r["mean_profile_fit"]["room_reference_C"]
    ax1.plot(X * 100, (means - Tinf) / (means[0] - Tinf), "o", ms=4.6, mfc="none",
             mec=C["blue"], mew=1.0, label="measured")
    ax1.axvline(L * 100, color=C["grey"], lw=.9, ls=":")
    ax1.annotate("tip: finite 44%\nsemi-infinite 23%", xy=(L * 100, .44), xytext=(14.0, .80),
                 fontsize=6.6, color=C["grey"], ha="left",
                 arrowprops=dict(arrowstyle="->", color=C["grey"], lw=.7))
    ax1.set(xlabel="distance from T1 (cm)", ylabel="normalised mean $\\theta$",
            title=f"mean field: $mL$ = {m * L:.2f} $< 3$")
    ax1.legend(loc="lower left", fontsize=6.3)

    # ---------- periodic amplitude ----------
    for period, col in ((200, C["blue"]), (500, C["teal"])):
        rec = REC[period]
        s = rec["q_per_m"] + 1j * rec["q_prime_per_m"]
        ax2.plot(xs * 100, np.abs(finite(xs, s)), color=col, lw=1.3,
                 label=f"finite, {period} s ($qL$ = {rec['q_per_m'] * L:.2f})")
        ax2.plot(xs * 100, np.exp(-rec["q_per_m"] * xs), color=col, lw=1.0, ls="--",
                 label=f"semi-infinite, {period} s")
        f = fits(period)
        amp = np.array([f[f"rod{i}_C"]["amplitude_C"] for i in range(1, 6)]) / f["rod1_C"]["amplitude_C"]
        ax2.plot(X * 100, amp, "o", ms=3.6, mfc="none", mec=col, mew=.9)
    ax2.axvline(L * 100, color=C["grey"], lw=.9, ls=":")
    ax2.set(xlabel="distance from T1 (cm)", ylabel="$\\Theta(x)\\,/\\,\\Theta_0$",
            title="amplitude envelope")
    ax2.set_yscale("log")
    ax2.legend(handles=[Line2D([], [], color=C["grey"], lw=1.3, label="finite (cosh)"),
                        Line2D([], [], color=C["grey"], lw=1.0, ls="--", label="semi-infinite (exp)")],
               loc="lower left", fontsize=6.0)

    # ---------- periodic phase error ----------
    xsp = np.linspace(0, 0.205, 120)      # stop before the tip turnaround
    for period, col in ((200, C["blue"]), (500, C["teal"])):
        rec = REC[period]
        qp = rec["q_prime_per_m"]
        s = rec["q_per_m"] + 1j * qp
        zf = finite(xsp, s)
        phf = np.unwrap(np.angle(zf / zf[0]))
        dev = np.degrees(phf + qp * xsp)         # 0 = pure travelling wave e^{-q'x}
        ax3.plot(xsp * 100, dev, color=col, lw=1.3, label=f"{period} s model")
        f = fits(period)
        ph = np.unwrap([f[f"rod{i}_C"]["phase_rad"] for i in range(1, 6)])
        ax3.plot(X * 100, np.degrees(ph - ph[0] + qp * X), "o", ms=3.6,
                 mfc="none", mec=col, mew=.9)
    ax3.axhline(0, color=C["grey"], lw=.9, ls="--")
    ax3.set_xlim(0, 21.5)
    ax3.annotate("reflected wave\nbends the phase", xy=(15.0, -4.6), xytext=(1.0, -8.6),
                 fontsize=6.6, color=C["grey"], ha="left",
                 arrowprops=dict(arrowstyle="->", color=C["grey"], lw=.7))
    ax3.set(xlabel="distance from T1 (cm)", ylabel="phase $-$ pure wave  (deg)",
            title="phase error")
    ax3.legend(loc="lower left", fontsize=6.0)

    fig.tight_layout()
    fig.savefig(OUT / "fig01_semi_vs_finite.png")
    plt.close(fig)
    print("wrote", OUT / "fig01_semi_vs_finite.png")


if __name__ == "__main__":
    main()
