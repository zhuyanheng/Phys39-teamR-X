"""Figures for the rho-c -> kappa/nu derivation note.

Produces two raster figures (220 dpi) used by
``Module_8/docs/f1_derivation_kappa_nu.html``:

    fig01_slice_balance.png   energy balance on one slice dx of the rod
    fig02_one_denominator.png the single shared denominator rho*c*A

Labels stay in English/mathtext on purpose: the Chinese explanation lives in
the HTML, so the figures never depend on a CJK font at draw time.

Usage
-----
    .venv/bin/python Module_8/python/derivation_figures.py
"""

from __future__ import annotations

import pathlib

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

NAVY = "#0f3d5c"
TEAL = "#14506e"
RED = "#b03a2e"
GREEN = "#2e7d4f"
ORANGE = "#c55a11"

OUT_DIR = pathlib.Path(__file__).resolve().parents[1] / "figures" / "derivation"
DPI = 220

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "mathtext.fontset": "dejavusans",
        "savefig.dpi": DPI,
    }
)


def _arrow(fig, xy_from, xy_to, color, lw=1.3):
    """Straight arrow in figure coordinates."""
    fig.patches.append(
        FancyArrowPatch(
            xy_from,
            xy_to,
            arrowstyle="-|>",
            mutation_scale=9,
            linewidth=lw,
            color=color,
            shrinkA=0.0,
            shrinkB=0.0,
            transform=fig.transFigure,
        )
    )


def fig01_slice_balance() -> pathlib.Path:
    fig = plt.figure(figsize=(7.2, 2.75))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.2)
    ax.axis("off")

    rod_y, rod_h = 1.15, 0.62
    x0, x1 = 0.85, 9.15
    ax.add_patch(
        Rectangle((x0, rod_y), x1 - x0, rod_h,
                  facecolor="#e4edf3", edgecolor=NAVY, linewidth=1.4)
    )

    sx, sw = 4.05, 0.85
    ax.add_patch(
        Rectangle((sx, rod_y), sw, rod_h, facecolor="#ffe3c2",
                  edgecolor=ORANGE, linewidth=1.5, hatch="///")
    )

    mid = rod_y + rod_h * 0.5
    ax.annotate("", xy=(sx, mid), xytext=(sx - 0.55, mid),
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.6,
                                mutation_scale=9))
    ax.annotate("", xy=(sx + sw + 0.55, mid), xytext=(sx + sw, mid),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.6,
                                mutation_scale=9))

    for xa in (sx + 0.12, sx + sw / 2, sx + sw - 0.12):
        ax.annotate("", xy=(xa, rod_y + rod_h + 0.62),
                    xytext=(xa, rod_y + rod_h + 0.04),
                    arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.4,
                                    mutation_scale=8))

    ax.text(sx - 0.62, mid + 0.28, r"$\dot Q(x)$", color=GREEN,
            fontsize=10.5, ha="right", va="center")
    ax.text(sx + sw + 0.66, mid + 0.28, r"$\dot Q(x+\mathrm{d}x)$",
            color=RED, fontsize=10.5, ha="left", va="center")
    ax.text(sx + sw / 2, rod_y + rod_h + 0.86,
            r"$h\,P\,\mathrm{d}x\,\theta$   to ambient",
            color=ORANGE, fontsize=10.5, ha="center", va="center")

    ax.annotate("", xy=(sx, rod_y - 0.30), xytext=(x0, rod_y - 0.30),
                arrowprops=dict(arrowstyle="<|-|>", color=TEAL, lw=0.9,
                                mutation_scale=7))
    ax.annotate("", xy=(x1, rod_y - 0.30), xytext=(sx + sw, rod_y - 0.30),
                arrowprops=dict(arrowstyle="<|-|>", color=TEAL, lw=0.9,
                                mutation_scale=7))
    for xd in (sx, sx + sw):
        ax.plot([xd, xd], [rod_y - 0.42, rod_y], color=TEAL, lw=0.8,
                ls=(0, (3, 2)))

    ax.text((x0 + sx) / 2, rod_y - 0.52, r"$x$", color=TEAL, ha="center",
            va="center", fontsize=9.5)
    ax.text(sx + sw / 2, rod_y - 0.52, r"$\mathrm{d}x$", color=ORANGE,
            ha="center", va="center", fontsize=10)
    ax.text((sx + sw + x1) / 2, rod_y - 0.52, r"$L-x$", color=TEAL,
            ha="center", va="center", fontsize=9.5)
    ax.text(x1 + 0.12, mid, r"$A,\ P$", color=NAVY, ha="left", va="center",
            fontsize=9.5)
    return _save(fig, "fig01_slice_balance.png")


def _save(fig, name: str) -> pathlib.Path:
    path = OUT_DIR / name
    fig.savefig(path, bbox_inches="tight", pad_inches=0.05, facecolor="white")
    plt.close(fig)
    return path



def fig02_one_denominator() -> pathlib.Path:
    fig = plt.figure(figsize=(7.2, 4.15))
    fig.patch.set_facecolor("white")
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8.6)
    ax.axis("off")

    def box(x, y, w, h, text, edge, face, fs=9.8):
        ax.add_patch(
            FancyBboxPatch(
                (x, y), w, h,
                boxstyle="round,pad=0.0,rounding_size=0.10",
                facecolor=face, edgecolor=edge, linewidth=1.3,
            )
        )
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color="#1a1a1a", linespacing=1.7)

    box(0.55, 6.55, 3.85, 1.40,
        "axial transport\n" r"$kA$    [W m K$^{-1}$]", NAVY, "#eaf1f6")
    box(5.60, 6.55, 3.85, 1.40,
        "lateral transport\n" r"$hP$    [W m$^{-1}$ K$^{-1}$]", ORANGE, "#fdf1e6")

    box(0.55, 4.50, 8.90, 1.30,
        "one shared denominator:   " r"$\rho c A$    [J m$^{-1}$ K$^{-1}$]"
        "\nstorage of the slice  (heat capacity = the thermal inertia)",
        RED, "#fdeeeb", fs=10.2)

    box(0.55, 2.40, 3.85, 1.40,
        r"$\kappa = kA/(\rho c A) = k/(\rho c)$" "\n" r"[m$^2$ s$^{-1}$]",
        NAVY, "#eaf1f6", fs=10.2)
    box(5.60, 2.40, 3.85, 1.40,
        r"$\nu = hP/(\rho c A)$" "\n" r"[s$^{-1}$]",
        ORANGE, "#fdf1e6", fs=10.2)

    box(1.60, 0.40, 6.80, 1.20,
        r"$m^2 = \nu/\kappa = hP/(kA)$    [m$^{-2}$]"
        "\nthe storage cancels: only the two channels are left to compete",
        GREEN, "#eaf4ee", fs=10.2)

    for xc in (2.475, 7.525):
        _arrow(fig, (xc / 10, 6.52 / 8.6), (xc / 10, 5.84 / 8.6), "#8a8a8a")
        _arrow(fig, (xc / 10, 4.48 / 8.6), (xc / 10, 3.84 / 8.6), "#8a8a8a")
        _arrow(fig, (xc / 10, 2.38 / 8.6), (5.0 / 10, 1.64 / 8.6), "#8a8a8a")

    ax.text(2.60, 6.17, r"$\div$", fontsize=15, color=RED, ha="center",
            va="center")
    ax.text(2.95, 6.17, "divide every term by the same thing", fontsize=8.2,
            color="#666", ha="left", va="center")

    return _save(fig, "fig02_one_denominator.png")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for build in (fig01_slice_balance, fig02_one_denominator):
        print(build())


if __name__ == "__main__":
    main()
