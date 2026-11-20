"""Refit the recorded rod phases with an estimated sequential ADC timing model."""

import hashlib
import json
import math
from pathlib import Path

from angstrom_fit import CHANNELS, MODULE, REQUIRED_PRODUCTION_PERIODS, ROOT, fit_finite_periodic, infer

# Module 1, Part 3D measured 112012 microseconds for 1000 conversions.
SECONDS_PER_CONVERSION = 112012e-6 / 1000
ADC_COUNTS = (1000, 100, 100, 100, 100, 100)
TIMING_EVIDENCE = ROOT / "docs/module_notes/module_01_evidence.md"
FIRMWARE = MODULE / "arduino/module_08_rod_controller/module_08_rod_controller.ino"
REVIEW = MODULE / "data/processed/five_period_review"
OUTPUT = MODULE / "data/processed/transport_note/m08_scan_timing_sensitivity.json"


def sample_midpoints():
    """Approximate each average's center in time relative to the scan start."""
    elapsed = 0.0
    midpoints = {}
    for channel, count in zip(CHANNELS, ADC_COUNTS):
        # The first conversion after selecting the channel is discarded.
        midpoints[channel] = elapsed + (1 + count / 2) * SECONDS_PER_CONVERSION
        elapsed += (1 + count) * SECONDS_PER_CONVERSION
    return midpoints, elapsed


def compare_period(period, offsets):
    path = REVIEW / f"m08_pi_p{period}s_analysis.json"
    content = path.read_bytes()
    analysis = json.loads(content)["analysis"]
    channels = [f"rod{sensor}_C" for sensor in analysis["selected_rod_sensors"]]
    geometry = analysis["geometry"]
    initial = analysis["finite_periodic_fit"]
    omega = 2 * math.pi / period
    corrected_fits = []
    for channel in channels:
        fit = analysis["channel_fits"][channel]
        corrected_fits.append({
            "amplitude_C": fit["amplitude_C"],
            "phase_rad": fit["phase_rad"] - omega * offsets[channel],
        })
    spatial = fit_finite_periodic(
        analysis["positions_m"], corrected_fits, geometry["analysis_length_m"],
        (initial["q_per_m"], initial["q_prime_per_m"]),
    )
    adjusted = infer(spatial["q_per_m"], spatial["q_prime_per_m"], period)
    baseline = analysis["transport"]
    return {
        "period_s": period,
        "source": str(path.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(content).hexdigest(),
        "phase_adjustment_rad": {ch: -omega * offsets[ch] for ch in channels},
        "baseline": {k: baseline[k] for k in ("kappa_m2_s", "nu_per_s")},
        "timing_scenario": {k: adjusted[k] for k in ("kappa_m2_s", "nu_per_s")},
        "kappa_change_percent": 100 * (adjusted["kappa_m2_s"] / baseline["kappa_m2_s"] - 1),
        "nu_change_per_s": adjusted["nu_per_s"] - baseline["nu_per_s"],
    }


def main():
    midpoints, duration = sample_midpoints()
    offsets = {key: value - midpoints["rod1_C"] for key, value in midpoints.items()}
    result = {
        "method": "Estimated centers of sample blocks using Module 1 conversion timing and Module 8 scan order.",
        "limitations": "The recorded timestamp follows the scan. Firmware overhead was not timed in this run. This is a sensitivity scenario and does not set measured sample_time_offsets_s.",
        "timing_evidence": str(TIMING_EVIDENCE.relative_to(ROOT)),
        "firmware": str(FIRMWARE.relative_to(ROOT)),
        "firmware_sha256": hashlib.sha256(FIRMWARE.read_bytes()).hexdigest(),
        "seconds_per_conversion": SECONDS_PER_CONVERSION,
        "estimated_adc_scan_duration_s": duration,
        "estimated_midpoint_offsets_relative_to_T1_s": offsets,
        "records": [compare_period(period, offsets) for period in sorted(REQUIRED_PRODUCTION_PERIODS)],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
