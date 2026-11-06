"""Reproduce A4's *provisional* calculations, not a fit of measured temperatures.

Run from the project root with .venv/bin/python. All input values, source pages,
acceptance criteria, and checks are retained in the JSON output. Change the
geometry inputs only when remeasured; regenerate the paper tables as well.
"""
import csv
import json
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/module7-matplotlib")
MODULE = Path(__file__).resolve().parents[2]
OUTPUT = MODULE / "data/processed/a4_predictions"
FIGURES = MODULE / "figures/a4"
DIAMETER_M = 0.01277  # Measured by vernier caliper, 2026-11-04.
INSTRUMENT_PRECISION_M = 0.00001  # Operator specification, not standard uncertainty.
LENGTH_M = 0.2715
POSITIONS_M = (0, 0.0385, 0.0895, 0.1405, 0.1915)
HOLES = (2, 5, 7, 8, 9)
H = 10.0
K_VALUES = (166.0, 167.0, 172.0)
MATERIALS = (
    ("Pure silver", 427.0, "A.1, p. 740, 20 C"),
    ("Pure aluminum", 237.0, "A.1, p. 739, 20 C"),
    ("Steel, 0.5% carbon", 54.0, "A.1, p. 739, 20 C"),
    ("Ice", 2.215, "A.2, p. 742, 0 C"),
    ("Spruce, across grain", 0.11, "A.2, p. 744, 20 C"),
    ("85% magnesia insulation", 0.067, "A.2, p. 743, 38 C"),
    ("Silica aerogel", 0.024, "A.2, p. 743, 0 C"),
)


def finite(m, length, x):
    return math.cosh(m * (length - x)) / math.cosh(m * length)


def semi(m, x):
    return math.exp(-m * x)


def write_csv(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def calculate():
    radius = DIAMETER_M / 2
    area = math.pi * radius ** 2
    perimeter = math.pi * DIAMETER_M
    slab = [{"material": name, "k_W_mK": k, "delta_T_K": 50 / k,
             "hot_side_C": -40 + 50 / k, "source": source}
            for name, k, source in MATERIALS]
    groups, sensor_rows = [], []
    for k in K_VALUES:
        m = math.sqrt(H * perimeter / (k * area))
        mL = m * LENGTH_M
        transverse = H * (area / perimeter) / k
        groups.append({"k_W_mK": k, "m_per_m": m, "decay_length_m": 1 / m,
                       "mL": mL, "Bi_parallel": mL ** 2,
                       "Bi_perp": transverse, "Theta_tip": finite(m, LENGTH_M, LENGTH_M)})
        for channel, (hole, x) in enumerate(zip(HOLES, POSITIONS_M), 1):
            f, s = finite(m, LENGTH_M, x), semi(m, x)
            error = abs(f - s) / abs(f)
            sensor_rows.append({"channel": f"A{channel}", "hole": hole, "x_m": x,
                                "k_W_mK": k, "Theta_finite": f,
                                "Theta_semi": s, "epsilon_T": error,
                                "passes_5_percent": error < 0.05})
        assert math.isclose(transverse, (m * radius / 2) ** 2, rel_tol=1e-12)
        assert finite(m, LENGTH_M, 0) == 1
        assert -m * math.sinh(m * (LENGTH_M - LENGTH_M)) / math.cosh(mL) == 0
        for x in POSITIONS_M:
            # Independent exponential expression for the same relative error.
            b, a = math.exp(-2 * m * (LENGTH_M - x)), math.exp(-2 * m * LENGTH_M)
            direct = abs(finite(m, LENGTH_M, x) - semi(m, x)) / finite(m, LENGTH_M, x)
            assert math.isclose(direct, (b - a) / (1 + b), abs_tol=1e-14)
        assert math.isclose(finite(m, 100, 0.2), semi(m, 0.2), rel_tol=1e-12)
    # Example 4.8 and Problem 4.20: use the example's rod, not the course rod.
    d, length, k, h, h_tip, theta0 = 0.02, 0.08, 205.0, 120.0, 120.0, 124.0
    a, p = math.pi * d ** 2 / 4, math.pi * d
    m = math.sqrt(h * p / (k * a))
    M, b = m * length, h_tip / (m * k)
    insulated_tip = 1 / math.cosh(M)
    convecting_tip = 1 / (math.cosh(M) + b * math.sinh(M))
    scale = math.sqrt(k * a * h * p) * theta0
    q_insulated = scale * math.tanh(M)
    q_convecting = scale * (math.tanh(M) + b) / (1 + b * math.tanh(M))
    example = {"m_per_m": m, "mL": M, "Bi_tip": h_tip * length / k,
               "b": b, "Theta_tip_insulated": insulated_tip,
               "Theta_tip_convecting": convecting_tip,
               "T_tip_insulated_C": 26 + theta0 * insulated_tip,
               "T_tip_convecting_C": 26 + theta0 * convecting_tip,
               "tip_excess_relative_error": (insulated_tip - convecting_tip) / convecting_tip,
               "Q_insulated_W": q_insulated, "Q_convecting_W": q_convecting,
               "heat_rate_relative_error": (q_convecting - q_insulated) / q_convecting}
    assert abs(slab[0]["delta_T_K"] - 0.117) < 0.0001
    assert abs(example["heat_rate_relative_error"] * 100 - 3.67) < 0.01
    # Problem 4.12 imposes a temperature (not an insulated tip) at x=L.
    m, length = 4, 0.3
    fixed_tip = lambda x: math.sinh(m * (length - x)) / math.sinh(m * length)
    assert fixed_tip(0) == 1 and fixed_tip(length) == 0
    for x in POSITIONS_M:
        long_fixed_tip = math.sinh(4 * (20 - x)) / math.sinh(4 * 20)
        assert math.isclose(long_fixed_tip, semi(4, x), rel_tol=1e-12)
    return {"kind": "provisional_theory_not_measured_fit",
            "inputs": {"diameter_m": DIAMETER_M, "diameter_status": "measured",
                       "diameter_method": "vernier caliper",
                       "instrument_precision_m": INSTRUMENT_PRECISION_M,
                       "instrument_precision_is_standard_uncertainty": False,
                       "analysis_length_m": LENGTH_M, "physical_origin_hole": 2,
                       "holes": HOLES, "positions_m": POSITIONS_M, "h_W_m2K": H,
                       "k_W_mK": K_VALUES, "k_source": "Lienhard v6, Table A.1 p.739: 6061-T6; 166 at 0 C, 167 at 20 C, 172 at 100 C",
                       "k_range_interpretation": "conservative temperature envelope, not a statistical confidence interval",
                       "finite_error_acceptance": "epsilon_T < 0.05"},
            "slab": slab, "rod": groups, "sensors": sensor_rows,
            "example_4_8_and_problem_4_20": example,
            "checks": {"silver_textbook_answer": True, "heat_rate_textbook_answer": True,
                       "finite_boundary_conditions": True, "independent_error_formula": True,
                       "Biot_identity": True, "long_rod_limits_both_tip_conditions": True}}


def main():
    result = calculate()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / "a4_problem_1_3.csv", result["slab"])
    write_csv(OUTPUT / "a4_sensor_predictions.csv", result["sensors"])
    (OUTPUT / "a4_numeric_checks.json").write_text(json.dumps(result, indent=2) + "\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11})
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 3.8), constrained_layout=True)
    colors = ["#245a81", "#555555", "#b45b22"]
    xs = [LENGTH_M * i / 400 for i in range(401)]
    for group, color in zip(result["rod"], colors):
        m, k = group["m_per_m"], group["k_W_mK"]
        f = [finite(m, LENGTH_M, x) for x in xs]
        s = [semi(m, x) for x in xs]
        axes[0].plot(xs, f, color=color, label=f"Finite, k={k:g}")
        axes[0].plot(xs, s, color=color, ls="--", alpha=.7)
        axes[1].plot(xs, [100 * abs(a-b)/a for a, b in zip(f, s)], color=color,
                     label=f"k={k:g} W/(m K)")
    axes[0].plot([], [], color="#222222", ls="--", label="Semi-infinite (dashed)")
    axes[1].axhline(5, color="#666666", ls="--", label="5% criterion")
    for ax in axes:
        for x in POSITIONS_M:
            ax.axvline(x, color="#666666", alpha=.75, lw=1.2, ls=":", zorder=1)
        ax.grid(alpha=.2)
        ax.set_xlabel("x from physical hole 2 (m)")
        ax.legend(fontsize=10)
    axes[0].set_ylabel("Normalized excess temperature")
    axes[1].set_ylabel("Finite-length approximation error (%)")
    axes[0].set_title("Finite vs semi-infinite prediction")
    axes[1].set_title("Error at the installed positions")
    fig.savefig(FIGURES / "a4_finite_length_prediction.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"checks": result["checks"], "rod": result["rod"],
                      "problem_4_20_error_percent": 100*result["example_4_8_and_problem_4_20"]["heat_rate_relative_error"]}, indent=2))


if __name__ == "__main__":
    main()
