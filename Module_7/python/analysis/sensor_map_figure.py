"""Draw the delivered rod sensor map (Part 1) from the recorded geometry.

Usage: .venv/bin/python Module_7/python/analysis/sensor_map_figure.py
Writes Module_7/figures/part_01_sensor_map.png.

This is a drawing of the installation, not a measurement: every distance comes
from docs/module_notes/module_07_rod_instrument.md (physical holes 2, 5, 7, 8, 9,
origin at hole 2, L = 27.15 cm, d = 12.7 mm nominal). The ruler uncertainty of
the hole distances and of L has not been recorded, so the figure states that
instead of inventing error bars.
"""
import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/module7-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

MODULE = Path(__file__).resolve().parents[2]
POSITIONS_CM = (0.0, 3.85, 8.95, 14.05, 19.15)
HOLES = (2, 5, 7, 8, 9)
LENGTH_CM = 27.15
BOTTOM_REFERENCE_CM = -3.00
COLORS = ["#245a81", "#2f7d4f", "#927919", "#b45b22", "#693f85"]


def dimension(axes, x0, x1, y, label):
    """A double-headed arrow between two positions, with its value below it."""
    axes.annotate("", xy=(x1, y), xytext=(x0, y),
                  arrowprops={"arrowstyle": "<->", "color": "#444444",
                              "lw": 1.0, "shrinkA": 0, "shrinkB": 0})
    axes.text((x0 + x1) / 2.0, y - 0.20, label, ha="center", va="top",
              fontsize=9, color="#444444")


def draw(path):
    figure, axes = plt.subplots(figsize=(13.4, 5.4), constrained_layout=True)
    axes.set_xlim(BOTTOM_REFERENCE_CM - 4.5, LENGTH_CM + 15.0)
    axes.set_ylim(-2.9, 2.4)
    axes.axis("off")

    rod_top, rod_bottom = 0.9, 0.0
    axes.add_patch(Rectangle((0.0, rod_bottom), LENGTH_CM, rod_top - rod_bottom,
                            facecolor="#dfe3e8", edgecolor="#111111", lw=1.3,
                            zorder=1))
    axes.add_patch(Rectangle((BOTTOM_REFERENCE_CM, 0.15), -BOTTOM_REFERENCE_CM,
                             rod_top - 0.30, facecolor="#c9a227",
                            edgecolor="#111111", lw=1.3, zorder=1))
    axes.text(BOTTOM_REFERENCE_CM / 2.0, (rod_top + 0.15) / 2.0,
              "TEC base\nA0 = tec_C", ha="center", va="center", fontsize=8.5)
    axes.text(BOTTOM_REFERENCE_CM - 0.2, -0.20,
              "bottom reference point:\n3.00 cm from hole 2, not surveyed",
              ha="left", va="top", fontsize=8, color="#666666")

    for index, x_cm in enumerate(POSITIONS_CM):
        axes.plot([x_cm], [(rod_top + rod_bottom) / 2.0], "o", ms=11,
                  color=COLORS[index], zorder=3)
        axes.plot([x_cm, x_cm], [(rod_top + rod_bottom) / 2.0, rod_top + 0.12],
                  color=COLORS[index], lw=0.8, ls=":", zorder=2)
        axes.text(x_cm, rod_top + 0.18, f"T{index + 1}", ha="center",
                  va="bottom", fontsize=12, color=COLORS[index],
                  fontweight="bold")

    axes.plot([LENGTH_CM, LENGTH_CM], [rod_bottom - 0.05, rod_top + 0.12],
              color="#111111", lw=1.0, ls="--")
    axes.text(LENGTH_CM, rod_top + 0.18, "tip", ha="center", va="bottom",
              fontsize=10)

    segments = [POSITIONS_CM[i + 1] - POSITIONS_CM[i]
                for i in range(len(POSITIONS_CM) - 1)] + [LENGTH_CM - POSITIONS_CM[-1]]
    edges = list(POSITIONS_CM) + [LENGTH_CM]
    for index, gap_cm in enumerate(segments):
        dimension(axes, edges[index], edges[index + 1], -1.35, f"{gap_cm:.2f} cm")
    dimension(axes, BOTTOM_REFERENCE_CM, 0.0, -1.35, "3.00 cm")

    axes.annotate("", xy=(6.0, -2.45), xytext=(0.0, -2.45),
                  arrowprops={"arrowstyle": "->", "color": "#111111", "lw": 1.4})
    axes.text(6.3, -2.45, "x, positive towards the tip", ha="left", va="center",
              fontsize=9)

    rows = [f"T{i + 1}  {channel}, hole {hole}, x = {x_cm:.2f} cm"
            for i, (channel, hole, x_cm) in enumerate(
                zip(("A1 rod1_C", "A2 rod2_C", "A3 rod3_C", "A4 rod4_C",
                     "A5 rod5_C"), HOLES, POSITIONS_CM))]
    axes.text(LENGTH_CM + 1.6, 1.95,
              "channels and holes\n" + "\n".join(rows) +
              f"\nx = L = {LENGTH_CM:.2f} cm at the rod tip (no probe)",
              ha="left", va="top", fontsize=9)

    axes.text(BOTTOM_REFERENCE_CM - 4.0, 2.30,
              "Aluminium 6061, d = 12.7 mm nominal (never measured); distances "
              "are ruler readings\nfrom the field record, not a survey",
              ha="left", va="top", fontsize=8.5, color="#444444")
    figure.suptitle("Module 7 rod sensor map: five rod holes, six channels, "
                    "origin at hole 2", fontsize=12)

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return Path(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=MODULE / "figures/part_01_sensor_map.png")
    args = parser.parse_args(argv)
    print(draw(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
