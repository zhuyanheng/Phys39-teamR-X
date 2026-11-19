"""Transport conversion and model-consistency note for Module 8 (offline only).

Reads the frozen five-period analyses and the raw PI records, never the serial port.
Produces:
  data/processed/transport_note/m08_transport_parameters.json   (k, h, drift, conditioning)
  data/processed/transport_note/m08_transport_summary.csv
  data/processed/transport_note/*.png

Why this module exists: five_period_review.py deliberately stops at kappa/nu and
records "k and h not computed". This module performs that conversion with sourced
material constants and, separately, quantifies the two things that actually limit
the answer: the drift-induced cycle spread and the conditioning of nu.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
MODULE = ROOT / "Module_8"
OUT = MODULE / "data/processed/transport_note"
FIG = MODULE / "figures/transport_note"
REVIEW = MODULE / "data/processed/five_period_review"
SENSOR_MAP = MODULE / "config/sensor_map.json"
M7_REF = MODULE / "data/reference/module_07_selected_stationary.json"
PERIODS = (100, 200, 300, 400, 500)
CHANNELS = ("tec_C", "rod1_C", "rod2_C", "rod3_C", "rod4_C", "rod5_C")
ROD = CHANNELS[1:]

# Sourced material inputs. Lienhard Table A.1 gives k only; rho and c are the
# standard 6061-T6 handbook values and are treated as rectangular bounds, not 1-sigma.
MATERIAL = {
    "density_kg_m3": 2700.0,
    "density_bound_kg_m3": 27.0,          # +/- 1 %
    "specific_heat_J_kgK": 896.0,
    "specific_heat_bound_J_kgK": 18.0,    # +/- 2 %
    "source": "Al 6061-T6 handbook values (rho 2680-2720 kg/m3, c 890-900 J/(kg K)); "
              "k compared with Lienhard Table A.1, 166-172 W/(m K)",
}
DIAMETER_M = 0.01277
DIAMETER_BOUND_M = 0.01e-3   # reported caliper resolution, treated as a bound
SCAN_SKEW_S = 0.17           # assumed, not measured (serial_protocol.md)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text())


def cycle_transport(q, qp, period):
    """kappa = w/(2qq'), nu = kappa(q^2 - q'^2); None where q' >= q."""
    w = 2 * math.pi / period
    kappa = w / (2 * q * qp)
    m2 = q * q - qp * qp
    return kappa, (kappa * m2 if m2 > 0 else None), m2


def material_conversion(kappa, nu):
    rho, c, d = MATERIAL["density_kg_m3"], MATERIAL["specific_heat_J_kgK"], DIAMETER_M
    k = rho * c * kappa
    h = None if nu is None else nu * rho * c * d / 4
    return k, h


def cosh_fit(x, means, length):
    """Fit a(xi) = Tinf + (a0 - Tinf) cosh[mu(1-xi)]/cosh(mu) with a0 profiled out.

    Two free parameters (mu, Tinf) on a grid, then quadratic refinement.
    No scipy in this environment; the profile likelihood is 2-D and smooth.
    """
    x = np.asarray(x, float)
    a = np.asarray(means, float)
    xi = x / length

    def ssr(mu, tinf):
        c = np.cosh(mu * (1 - xi)) / math.cosh(mu)
        # a = tinf + beta*c with beta = a0 - tinf; beta is linear, so profile it out.
        beta = float(c @ (a - tinf)) / float(c @ c)
        r = tinf + beta * c - a
        return float(r @ r), tinf + beta

    best = (np.inf, None, None)
    for mu in np.arange(0.2, 8.0001, 0.005):
        for tinf in np.arange(15.0, 32.0001, 0.05):
            s, a0 = ssr(mu, tinf)
            if s < best[0]:
                best = (s, mu, tinf)
                best_a0 = a0
    s0, mu0, t0 = best
    mu, tinf = mu0, t0
    for step_mu, step_t in ((0.005, 0.05), (0.001, 0.01), (0.0002, 0.002)):
        improved = True
        while improved:
            improved = False
            for dm, dt in ((step_mu, 0), (-step_mu, 0), (0, step_t), (0, -step_t)):
                nm = min(8.0, max(0.2, mu + dm))
                nt = min(32.0, max(15.0, tinf + dt))
                s, a0 = ssr(nm, nt)
                if s < s0 - 1e-12:
                    s0, mu, tinf, best_a0 = s, nm, nt, a0
                    improved = True
    resid = tinf + (best_a0 - tinf) * np.cosh(mu * (1 - xi)) / math.cosh(mu) - a
    return {
        "mu_mL": mu,
        "m_per_m": mu / length,
        "ambient_C_fitted": tinf,
        "ambient_at_grid_bound": bool(tinf in (15.0, 32.0)),
        "base_C_fitted": best_a0,
        "ssr_C2": s0,
        "rms_residual_C": float(np.sqrt(np.mean(resid ** 2))),
        "residuals_C": [float(v) for v in resid],
        "one_over_m_m": length / mu if mu > 0 else None,
        "free_parameters": 2,
        "data_points": int(a.size),
    }


def harmonic(t, y, period):
    """Least-squares A + C cos(wt) + S sin(wt); returns amplitude, phase, rms."""
    w = 2 * math.pi / period
    X = np.column_stack([np.ones_like(t), np.cos(w * t), np.sin(w * t)])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    amp = float(np.hypot(coef[1], coef[2]))
    phase = float(math.atan2(-coef[2], coef[1]))
    return {
        "mean": float(coef[0]),
        "amplitude": amp,
        "phase_rad": phase,
        "rms_residual": float(np.sqrt(np.mean(resid ** 2))),
    }


def finite_error(q, qp, length, x):
    """Complex semi-infinite vs finite insulated-tip relative error (single sensor)."""
    s = complex(q, qp)
    semi = np.exp(-s * x)
    finite = semi * (1 + np.exp(-2 * s * (length - x))) / (1 + np.exp(-2 * s * length))
    return float(abs(finite - semi) / abs(finite))


def load_period(period):
    path = REVIEW / ("m08_pi_p%ds_analysis.json" % period)
    run = load_json(path)
    return run, digest(path)


def analyse_period(period, run, source_sha):
    a = run["analysis"]
    src = run["source"]
    geom = a["geometry"]
    x = np.asarray(geom["x_m"], float)
    length = float(geom["analysis_length_m"])
    q = float(a["finite_periodic_fit"]["q_per_m"])
    qp = float(a["finite_periodic_fit"]["q_prime_per_m"])
    tr = a["transport"]
    kappa, nu, m2 = cycle_transport(q, qp, period)
    k, h = material_conversion(kappa, nu)

    # Cycle-to-cycle spread: the honest drift estimate, not a statistical SE.
    cyc = []
    for qq, qqp in a["finite_cycle_q_qprime"]:
        kc, nc, _ = cycle_transport(float(qq), float(qqp), period)
        cyc.append({"q": float(qq), "qp": float(qqp), "kappa": kc, "nu": nc})
    kaps = [c["kappa"] for c in cyc]
    nus = [c["nu"] for c in cyc if c["nu"] is not None]
    drift = {
        "cycles": len(cyc),
        "kappa_range_m2_s": [min(kaps), max(kaps)],
        "kappa_range_fraction": (max(kaps) - min(kaps)) / float(np.mean(kaps)),
        "nu_range_per_s": [min(nus), max(nus)] if nus else None,
        "nu_sign_changes": bool(nus) and (min(nus) < 0 < max(nus)),
        "note": "Cycle-to-cycle spread under a drifting mean field; not a confidence interval.",
    }

    # Why nu is fragile: (q^2+q'^2)/|q^2-q'^2| amplifies relative errors.
    conditioning = (q * q + qp * qp) / m2 if m2 > 0 else None

    # Mean-temperature finite-rod fit, all five rod sensors (better SNR than the
    # oscillation at T4/T5 because 1/m > 1/q).
    means = [a["channel_fits"][ch]["mean_C"] for ch in ROD]
    mean_fit = cosh_fit(x, means, length)
    # Ambient sensitivity: how mu and m move if Tinf is fixed at a plausible room value.
    sensitivity = []
    for tinf_guess in (20.0, 22.0, 24.0, 26.0, 28.0):
        best = None
        for mu in np.arange(0.2, 8.0001, 0.002):
            c = np.cosh(mu * (1 - x / length)) / math.cosh(mu)
            beta = float(c @ (np.asarray(means) - tinf_guess)) / float(c @ c)
            r = tinf_guess + beta * c - np.asarray(means)
            s = float(r @ r)
            if best is None or s < best[0]:
                best = (s, mu, tinf_guess + beta)
        sensitivity.append({"ambient_C_fixed": tinf_guess, "mu_mL": float(best[1]),
                            "m_per_m": float(best[1]) / length,
                            "rms_residual_C": float(np.sqrt(best[0] / len(means))),
                            "h_from_mean_W_m2K": (kappa * (float(best[1]) / length) ** 2
                                                  * MATERIAL["density_kg_m3"]
                                                  * MATERIAL["specific_heat_J_kgK"]
                                                  * DIAMETER_M / 4)})

    # Cross-check route 2: nu from the mean profile and the oscillation kappa.
    nu_from_mean = kappa * mean_fit["m_per_m"] ** 2
    h_from_mean = nu_from_mean * MATERIAL["density_kg_m3"] * MATERIAL["specific_heat_J_kgK"] * DIAMETER_M / 4

    per_sensor = {}
    for ch in ROD:
        f = a["channel_fits"][ch]
        per_sensor[ch] = {
            "mean_C": f["mean_C"], "amplitude_C": f["amplitude_C"],
            "phase_rad": f["phase_rad"], "amplitude_se_C": f["amplitude_se_C"],
            "phase_se_rad": f["phase_se_rad"], "rms_residual_C": f["rms_residual_C"],
            "finite_error": finite_error(q, qp, length, float(x[ROD.index(ch)])),
        }

    return {
        "period_s": period,
        "source": src,
        "analysis_json_sha256": source_sha,
        "model": a["main_inference_model"],
        "q_per_m": q, "q_prime_per_m": qp,
        "kappa_m2_s": kappa,
        "kappa_fit_se_m2_s": tr["kappa_se_m2_s"],
        "nu_per_s": nu,
        "nu_fit_se_per_s": tr["nu_se_per_s"],
        "physical_positive_loss": bool(m2 > 0),
        "m_per_m_from_slopes": math.sqrt(m2) if m2 > 0 else None,
        "conditioning_factor": conditioning,
        "k_W_mK": k, "h_W_m2K": h,
        "drift": drift,
        "mean_profile_fit": mean_fit,
        "mean_fit_ambient_sensitivity": sensitivity,
        "nu_from_mean_profile_per_s": nu_from_mean,
        "h_from_mean_profile_W_m2K": h_from_mean,
        "bi_perp": m2 * (DIAMETER_M / 4) ** 2 if m2 > 0 else None,
        "bi_perp_suppressed_reason": None if m2 > 0 else "m^2 <= 0 makes the transverse Biot number meaningless",
        "boundary_relative_rms": a["boundary_relative_rms"],
        "cycle_stationarity_passed": a["cycle_stationarity_passed"],
        "interval_s": [a["start_s"], a["end_s"]],
        "per_sensor": per_sensor,
        "limitations": a["warnings"],
    }


def actuator_response(period, run):
    """Measured A0/PWM transfer at the drive frequency from the raw record.

    The firmware's OPEN feedforward inverts a *static* curve; this measures the
    same path dynamically, which is what the boundary actually sees.
    """
    raw = ROOT / run["source"]["raw"]
    start = float(run["analysis"]["start_s"])
    end = float(run["analysis"]["end_s"])
    t, tec, pwm = [], [], []
    with raw.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("run_state") != "RUNNING":
                continue
            try:
                ts = float(row["time_s"])
                tv = float(row["tec_C"])
                pv = float(row["signed_pwm"])
            except (TypeError, ValueError):
                continue
            if start <= ts < end and all(map(math.isfinite, (ts, tv, pv))):
                t.append(ts), tec.append(tv), pwm.append(pv)
    if len(t) < 100:
        return None
    t = np.asarray(t)
    ft = harmonic(t, np.asarray(tec), period)
    fp = harmonic(t, np.asarray(pwm), period)
    if fp["amplitude"] <= 0.5:     # one PWM count is the quantisation floor
        return None
    return {
        "samples": int(t.size),
        "pwm_amplitude": fp["amplitude"],
        "pwm_mean": fp["mean"],
        "tec_amplitude_C": ft["amplitude"],
        "gain_C_per_pwm": ft["amplitude"] / fp["amplitude"],
        "phase_lag_rad": ((fp["phase_rad"] - ft["phase_rad"] + math.pi) % (2 * math.pi)) - math.pi,
        "pwm_rms_residual": fp["rms_residual"],
        "tec_rms_residual_C": ft["rms_residual"],
    }


def position_budget(period, rec):
    """Eight +/-1 mm corners on (x2, x3, L): refit the spatial slopes, no time refit."""
    geom = load_json(SENSOR_MAP)
    x0 = np.asarray(geom["x_m"], float)[:3]
    amps = [rec["per_sensor"][ch]["amplitude_C"] for ch in ROD[:3]]
    phases = list(np.unwrap([rec["per_sensor"][ch]["phase_rad"] for ch in ROD[:3]]))
    length0 = float(geom["analysis_length_m"])
    out = []
    for dx2 in (-1e-3, 1e-3):
        for dx3 in (-1e-3, 1e-3):
            for dL in (-1e-3, 1e-3):
                x = x0 + np.array([0.0, dx2, dx3])
                la = np.polyfit(x, np.log(amps), 1)
                lf = np.polyfit(x, phases, 1)
                kc, nc, _ = cycle_transport(float(-la[0]), float(-lf[0]), period)
                out.append({"dx2_m": dx2, "dx3_m": dx3, "dL_m": dL,
                            "kappa_m2_s": kc, "nu_per_s": nc, "length_m": length0 + dL})
    kaps = [o["kappa_m2_s"] for o in out]
    nus = [o["nu_per_s"] for o in out if o["nu_per_s"] is not None]
    return {
        "corners": out,
        "kappa_range_m2_s": [min(kaps), max(kaps)],
        "kappa_half_range_fraction": (max(kaps) - min(kaps)) / 2 / float(np.mean(kaps)),
        "nu_range_per_s": [min(nus), max(nus)] if nus else None,
    }


def budget(period, rec):
    """Reported uncertainty plus an explicit list of what is not included."""
    rho = MATERIAL["density_kg_m3"]
    c = MATERIAL["specific_heat_J_kgK"]
    kappa, nu = rec["kappa_m2_s"], rec["nu_per_s"]
    k, h = rec["k_W_mK"], rec["h_W_m2K"]
    u_rho = MATERIAL["density_bound_kg_m3"] / math.sqrt(3)
    u_c = MATERIAL["specific_heat_bound_J_kgK"] / math.sqrt(3)
    u_d = DIAMETER_BOUND_M / math.sqrt(3)
    u_kap = rec["kappa_fit_se_m2_s"] or 0.0
    u_nu = rec["nu_fit_se_per_s"] or 0.0
    pos = position_budget(period, rec)
    skew_phase = 2 * math.pi / period * SCAN_SKEW_S
    skew_qp = 2 * skew_phase / 0.0895
    skew_nu = abs(2 * kappa * skew_qp * rec["q_prime_per_m"]) if nu is not None else None

    k_parts = [u_rho / rho, u_c / c, u_kap / kappa, pos["kappa_half_range_fraction"]]
    h_parts = [u_rho / rho, u_c / c, u_d / DIAMETER_M,
               u_nu / abs(nu) if nu else None, pos["kappa_half_range_fraction"],
               (skew_nu / abs(nu)) if (nu and skew_nu) else None]
    comb = lambda parts: math.sqrt(sum(p * p for p in parts if p))
    return {
        "k_W_mK": k,
        "k_relative_parts": {"density": u_rho / rho, "specific_heat": u_c / c,
                             "fit_se": u_kap * rho * c / k if k else None,
                             "position_1mm": pos["kappa_half_range_fraction"]},
        "k_combined_relative": comb(k_parts),
        "k_absolute": comb(k_parts) * k if k else None,
        "h_W_m2K": h,
        "h_relative_parts": {"density": u_rho / rho, "specific_heat": u_c / c,
                             "diameter": u_d / DIAMETER_M,
                             "fit_se": (u_nu * rho * c * DIAMETER_M / 4 / abs(h)) if h else None,
                             "position_1mm": pos["kappa_half_range_fraction"],
                             "scan_skew_assumed": (skew_nu / abs(nu)) if (nu and skew_nu) else None},
        "h_combined_relative": comb(h_parts),
        "h_absolute": comb(h_parts) * abs(h) if h else None,
        "position_corners": pos,
        "nu_drift_range_per_s": rec["drift"]["nu_range_per_s"],
        "excluded": ["channel cross-calibration bias", "contact resistance and probe lag",
                     "nonuniform side convection", "unmeasured scan skew",
                     "model discrepancy and finite-length residual",
                     "temperature drift of rho and c"],
        "material": MATERIAL,
        "diameter_m": DIAMETER_M,
        "scan_skew_assumed_s": SCAN_SKEW_S,
    }




def figures(records, frf, path=FIG):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10})
    P = [r["period_s"] for r in records]
    rho, c = MATERIAL["density_kg_m3"], MATERIAL["specific_heat_J_kgK"]

    # 1) kappa and nu against drive period
    fig, ax = plt.subplots(1, 2, figsize=(10.4, 3.9), constrained_layout=True)
    kap = [r["kappa_m2_s"] * 1e5 for r in records]
    kap_se = [(r["kappa_fit_se_m2_s"] or 0) * 1e5 for r in records]
    lo = [r["drift"]["kappa_range_m2_s"][0] * 1e5 for r in records]
    hi = [r["drift"]["kappa_range_m2_s"][1] * 1e5 for r in records]
    ax[0].errorbar(P, kap, yerr=kap_se, fmt="o", color="#245a81", label="per period (joint fit SE)")
    ax[0].vlines(P, lo, hi, color="#245a81", alpha=.35, lw=6, label="single-cycle spread (drift)")
    ax[0].axhspan(166 / (rho * c) * 1e5, 172 / (rho * c) * 1e5, color="#b45b22", alpha=.15,
                  label="literature k/(rho c), 166-172 W/(m K)")
    ax[0].set_ylim(min(lo) - 0.15, max(hi) + 0.15)
    ax[0].ticklabel_format(axis="y", useOffset=False)
    ax[0].set_xlabel("drive period (s)")
    ax[0].set_ylabel("kappa ($10^{-5}$ m$^2$/s)")
    ax[0].set_title("Thermal diffusivity is consistent across periods")
    ax[0].legend(fontsize=7)

    nu = [r["nu_per_s"] if r["nu_per_s"] is not None else np.nan for r in records]
    nu_se = [r["nu_fit_se_per_s"] or 0 for r in records]
    ax[1].errorbar(P, nu, yerr=nu_se, fmt="o", color="#b45b22")
    ax[1].axhline(0, color="#666666", lw=1)
    for r in records:
        if r["nu_per_s"] is None:
            ax[1].plot(r["period_s"], 0, "o", mfc="none", mec="#b45b22", ms=7)
            ax[1].annotate("q' > q\nunphysical", (r["period_s"], 0), textcoords="offset points",
                           xytext=(0, 12), ha="center", fontsize=8, color="#b45b22")
        elif r["conditioning_factor"]:
            ax[1].annotate("%.0fx" % r["conditioning_factor"],
                           (r["period_s"], r["nu_per_s"]), textcoords="offset points",
                           xytext=(0, 9), ha="center", fontsize=8, color="#555555")
    ax[1].set_ylim(-2.5e-4, max(max(nu_se), 3e-3) * 1.05)
    ax[1].set_xlabel("drive period (s)")
    ax[1].set_ylabel("nu (1/s)")
    ax[1].set_title("Lateral loss is drift- and conditioning-limited")
    fig.savefig(path / "m08_transport_kappa_nu.png", dpi=180)
    plt.close(fig)

    # 2) k and h, with the independent mean-profile route for nu
    fig, ax = plt.subplots(1, 2, figsize=(10.4, 3.9), constrained_layout=True)
    ax[0].errorbar(P, [r["k_W_mK"] if r["k_W_mK"] is not None else np.nan for r in records],
                   yerr=[r["budget"]["k_absolute"] or 0 for r in records], fmt="o", color="#245a81")
    ax[0].axhspan(166, 172, color="#b45b22", alpha=.15, label="Lienhard Table A.1, 6061-T6")
    ax[0].set_xlabel("drive period (s)")
    ax[0].set_ylabel("k (W/(m K))")
    ax[0].set_title("Thermal conductivity")
    ax[0].legend(fontsize=8)

    ax[1].errorbar(P, [r["h_W_m2K"] if r["h_W_m2K"] is not None else np.nan for r in records],
                   yerr=[r["budget"]["h_absolute"] or 0 for r in records], fmt="o",
                   color="#b45b22", label="from q, q'")
    ax[1].plot(P, [r["h_from_mean_profile_W_m2K"] for r in records], "s", mfc="none",
               color="#245a81", label="from mean-profile m, same kappa")
    ax[1].axhline(10, color="#666666", ls="--", lw=1, label="course provisional h = 10")
    ax[1].set_xlabel("drive period (s)")
    ax[1].set_ylabel("h (W/(m$^2$ K))")
    ax[1].set_title("Side heat-transfer coefficient")
    ax[1].legend(fontsize=8)
    fig.savefig(path / "m08_transport_k_h.png", dpi=180)

    # 3) mean profile and its finite-rod fit
    fig, ax = plt.subplots(1, 2, figsize=(10.4, 3.9), constrained_layout=True)
    geom = load_json(SENSOR_MAP)
    xi = np.asarray(geom["x_m"], float) / float(geom["analysis_length_m"])
    grid = np.linspace(0, 1, 200)
    for r in records:
        f = r["mean_profile_fit"]
        base, amb = f["base_C_fitted"], f["ambient_C_fitted"]
        ax[0].plot(xi, [(r["per_sensor"][ch]["mean_C"] - amb) / (base - amb) for ch in ROD],
                   "o", ms=4)
        ax[0].plot(grid, np.cosh(f["mu_mL"] * (1 - grid)) / math.cosh(f["mu_mL"]),
                   lw=1, label="%d s: m = %.2f 1/m" % (r["period_s"], f["m_per_m"]))
    ax[0].set_xlabel("xi = x / L")
    ax[0].set_ylabel("(a - T_inf) / (a0 - T_inf)")
    ax[0].set_title("Mean profile: finite insulated-tip fit, 5 sensors")
    ax[0].legend(fontsize=7)
    for r in records:
        ax[1].plot(xi, r["mean_profile_fit"]["residuals_C"], "o-", ms=3, lw=1,
                   label="%d s" % r["period_s"])
    ax[1].axhline(0, color="#666666", lw=1)
    ax[1].set_xlabel("xi = x / L")
    ax[1].set_ylabel("residual (C)")
    ax[1].set_title("Same residual pattern at every period: a fixed spatial error")
    ax[1].legend(fontsize=7)
    fig.savefig(path / "m08_mean_profile_fit.png", dpi=180)
    plt.close(fig)

    # 4) measured actuator response vs the static curve that OPEN inverts
    fig, ax = plt.subplots(1, 2, figsize=(10.4, 3.9), constrained_layout=True)
    chi_dc = 0.49544628875665514
    pf = [p for p, v in frf.items() if v]
    ax[0].loglog(pf, [frf[p]["gain_C_per_pwm"] / chi_dc for p in pf], "o-", color="#245a81")
    ax[0].axhline(1, color="#666666", ls="--", lw=1, label="static Module 4 susceptibility")
    ax[0].set_xlabel("drive period (s)")
    ax[0].set_ylabel("|dT_A0 / dPWM| / chi_static")
    ax[0].set_title("The actuator is not static over 100-500 s")
    ax[0].legend(fontsize=8)
    ax[1].semilogx(pf, [frf[p]["phase_lag_rad"] for p in pf], "o-", color="#b45b22")
    ax[1].axhline(0, color="#666666", lw=1)
    ax[1].set_xlabel("drive period (s)")
    ax[1].set_ylabel("A0 lag behind PWM (rad)")
    ax[1].set_title("Measured lag at the drive frequency")
    fig.savefig(path / "m08_actuator_frf.png", dpi=180)
    plt.close(fig)

    # 5) per-sensor spatial consistency
    fig, ax = plt.subplots(1, 2, figsize=(10.4, 3.9), constrained_layout=True)
    x = np.asarray(geom["x_m"], float)
    for r in records:
        b1 = r["per_sensor"]["rod1_C"]["amplitude_C"]
        p1 = r["per_sensor"]["rod1_C"]["phase_rad"]
        ax[0].plot(x, [math.log(r["per_sensor"][ch]["amplitude_C"] / b1) for ch in ROD],
                   "o-", ms=4, lw=1, label="%d s" % r["period_s"])
        ph = np.unwrap([r["per_sensor"][ch]["phase_rad"] for ch in ROD])
        ax[1].plot(x, ph - p1, "o-", ms=4, lw=1, label="%d s" % r["period_s"])
    ax[0].set_xlabel("x (m)")
    ax[0].set_ylabel("ln(B_i / B_1)")
    ax[0].set_title("Amplitude decay, all five sensors")
    ax[0].legend(fontsize=7)
    ax[1].set_xlabel("x (m)")
    ax[1].set_ylabel("unwrapped phase - phase(T1)  (rad)")
    ax[1].set_title("Phase lag, all five sensors")
    ax[1].legend(fontsize=7)
    fig.savefig(path / "m08_spatial_per_sensor.png", dpi=180)
    plt.close(fig)



def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records, hashes = [], {}
    for period in PERIODS:
        run, sha = load_period(period)
        rec = analyse_period(period, run, sha)
        rec["budget"] = budget(period, rec)
        rec["actuator"] = actuator_response(period, run)
        records.append(rec)
        hashes[str(period)] = sha
        print("%3d s  q=%.3f q'=%.3f  kappa=%.3e  nu=%s  k=%s  h=%s"
              % (period, rec["q_per_m"], rec["q_prime_per_m"], rec["kappa_m2_s"],
                 "unphysical" if rec["nu_per_s"] is None else "%.3e" % rec["nu_per_s"],
                 "None" if rec["k_W_mK"] is None else "%.1f" % rec["k_W_mK"],
                 "None" if rec["h_W_m2K"] is None else "%.1f" % rec["h_W_m2K"]), flush=True)

    kaps = [r["kappa_m2_s"] for r in records]
    k_mean = float(np.mean(kaps))
    nus = [r["nu_per_s"] for r in records if r["nu_per_s"] is not None]
    pairs = [(abs(a - b) / math.hypot(ra["kappa_fit_se_m2_s"] or 1e-12,
                                      rb["kappa_fit_se_m2_s"] or 1e-12), a, b)
             for i, (a, ra) in enumerate(zip(kaps, records))
             for b, rb in list(zip(kaps, records))[i + 1:]]
    result = {
        "kind": "module_8_transport_conversion_offline",
        "created": "2026-11-18",
        "supersedes_field": "five_period_review summary field 'material_constants: k and h not computed'",
        "inputs": {
            "analysis_json_sha256": hashes,
            "sensor_map_sha256": digest(SENSOR_MAP),
            "module_07_reference_sha256": digest(M7_REF),
            "module_07_reference": load_json(M7_REF),
            "code_sha256": digest(Path(__file__)),
            "core_sha256": digest(Path(__file__).with_name("angstrom_fit.py")),
        },
        "material": MATERIAL,
        "records": records,
        "frequency_consistency": {
            "kappa_mean_m2_s": k_mean,
            "kappa_sem_across_periods_m2_s": float(np.std(kaps, ddof=1) / math.sqrt(len(kaps))),
            "kappa_span_fraction": (max(kaps) - min(kaps)) / k_mean,
            "kappa_largest_pairwise_difference_over_combined_se": max(p[0] for p in pairs),
            "nu_positive_periods_s": [r["period_s"] for r in records
                                      if r["nu_per_s"] and r["nu_per_s"] > 0],
            "nu_unphysical_periods_s": [r["period_s"] for r in records
                                        if not r["nu_per_s"] or r["nu_per_s"] <= 0],
            "nu_range_positive_per_s": [min(nus), max(nus)] if nus else None,
            "interpretation": "kappa is over-determined and consistent; nu is not, and the spread is "
                              "drift- plus conditioning-limited rather than statistical.",
        },
        "literature_bands": {
            "k_6061_T6_W_mK": [166.0, 172.0],
            "kappa_implied_m2_s": [166 / (MATERIAL["density_kg_m3"] * MATERIAL["specific_heat_J_kgK"]),
                                   172 / (MATERIAL["density_kg_m3"] * MATERIAL["specific_heat_J_kgK"])],
            "course_provisional_h_W_m2K": 10.0,
        },
        "limitations": [
            "No record passes the provisional settled-periodic span limits; these are diagnostic "
            "transport estimates with drift-dominated systematics, not certified production values.",
            "Cycle-to-cycle ranges under drift are reported instead of a confidence interval.",
            "nu is a difference of nearly equal quantities: (q^2+q'^2)/(q^2-q'^2) = 6-26, so nu is far "
            "less constrained than kappa; at 100 s q' > q, which no passive lateral loss can produce.",
            "The mean-profile ambient is fitted, not measured; there is no independent room thermometer.",
            "Channel cross-calibration was not performed; common-mode bias cancels in spatial slopes but "
            "not in the absolute mean profile.",
            "The material constants are handbook values, not measurements of this rod.",
        ],
    }
    (OUT / "m08_transport_parameters.json").write_text(json.dumps(result, indent=2) + "\n")

    with (OUT / "m08_transport_summary.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["period_s", "q_per_m", "q_prime_per_m", "m_from_slopes_per_m", "kappa_m2_s",
                    "kappa_fit_se_m2_s", "nu_per_s", "nu_fit_se_per_s", "conditioning_factor",
                    "k_W_mK", "k_absolute", "h_W_m2K", "h_absolute", "m_from_mean_profile_per_m",
                    "ambient_C_fitted", "mean_fit_rms_C", "h_from_mean_profile_W_m2K",
                    "bi_perp", "boundary_relative_rms", "actuator_gain_C_per_pwm",
                    "actuator_phase_lag_rad", "status"])
        for r in records:
            b = r["budget"]
            act = r["actuator"] or {}
            w.writerow([r["period_s"], r["q_per_m"], r["q_prime_per_m"], r["m_per_m_from_slopes"],
                        r["kappa_m2_s"], r["kappa_fit_se_m2_s"], r["nu_per_s"], r["nu_fit_se_per_s"],
                        r["conditioning_factor"], r["k_W_mK"], b["k_absolute"], r["h_W_m2K"],
                        b["h_absolute"], r["mean_profile_fit"]["m_per_m"],
                        r["mean_profile_fit"]["ambient_C_fitted"],
                        r["mean_profile_fit"]["rms_residual_C"], r["h_from_mean_profile_W_m2K"],
                        r["bi_perp"], r["boundary_relative_rms"],
                        act.get("gain_C_per_pwm"), act.get("phase_lag_rad"), "diagnostic_only"])

    figures(records, {r["period_s"]: r["actuator"] for r in records})
    print("wrote", OUT)
    return result


if __name__ == "__main__":
    main()

