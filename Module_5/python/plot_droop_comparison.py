"""Build the Module 5 Part 4 measured-versus-predicted droop evidence."""

import csv
import os
import statistics
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter, SVGExporter
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "Module_5" / "data"
FIGURE_DIR = ROOT / "Module_5" / "figures"
SETPOINT_C = 30.0
# Provisional Module 4 heating slope; update after the Module 4 calibration audit.
CHI_HEAT_C_PER_PWM = 0.4954
FINAL_WINDOW_S = 20.0
RUNS = {
    0.25: "module_05_p_control_20260930_110723_090850.csv",
    0.5: "module_05_p_control_20260930_111214_398504.csv",
    1.0: "module_05_p_control_20260930_112131_559827.csv",
    2.0: "module_05_p_control_20260930_112429_084527.csv",
    4.0: "module_05_p_control_20260930_112955_213490.csv",
}


def read_rows(name):
    with (DATA_DIR / name).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def build_summary():
    first_run_name = RUNS[min(RUNS)]
    first_run = read_rows(first_run_name)
    baseline = []
    for row in first_run:
        if row["p_active"] == "1":
            break
        if int(row["pwm"]) == 0 and row["safety"] == "OK":
            baseline.append(float(row["temperature_C"]))
    if not baseline:
        raise ValueError("No valid PWM-0 baseline in the first run")
    ambient_c = statistics.mean(baseline)

    summary = []
    for gain, filename in sorted(RUNS.items()):
        rows = read_rows(filename)
        if any(row["safety"] != "OK" for row in rows):
            raise ValueError(f"Safety fault reported in {filename}")
        active = [row for row in rows if row["p_active"] == "1"]
        if not active or any(
            float(row["setpoint_C"]) != SETPOINT_C
            or float(row["Kp_pwm_per_C"]) != gain
            for row in active
        ):
            raise ValueError(f"Unexpected P settings in {filename}")
        end_s = float(active[-1]["time_s"])
        final = [
            row for row in active
            if float(row["time_s"]) >= end_s - FINAL_WINDOW_S
        ]
        if len(final) < 10:
            raise ValueError(f"Too few final-window samples in {filename}")
        temperature_c = statistics.mean(float(row["temperature_C"]) for row in final)
        measured_droop_c = SETPOINT_C - temperature_c
        predicted_droop_c = (SETPOINT_C - ambient_c) / (
            1.0 + CHI_HEAT_C_PER_PWM * gain
        )
        summary.append({
            "source_csv": filename,
            "setpoint_C": SETPOINT_C,
            "kp_pwm_per_C": gain,
            "ambient_reference_C": round(ambient_c, 4),
            "ambient_source_csv": first_run_name,
            "chi_heat_C_per_pwm": CHI_HEAT_C_PER_PWM,
            "final_window_start_s": float(final[0]["time_s"]),
            "final_window_end_s": end_s,
            "final_window_samples": len(final),
            "mean_temperature_C": round(temperature_c, 4),
            "mean_final_pwm": round(statistics.mean(float(row["pwm"]) for row in final), 3),
            "measured_droop_C": round(measured_droop_c, 4),
            "predicted_droop_C": round(predicted_droop_c, 4),
            "measured_minus_predicted_C": round(measured_droop_c - predicted_droop_c, 4),
        })
    return ambient_c, summary


def save_summary(summary):
    destination = DATA_DIR / "part_04_droop_comparison.csv"
    with destination.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    return destination


def save_figure(ambient_c, summary):
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    pg.setConfigOptions(antialias=True)
    plot = pg.PlotWidget()
    plot.resize(980, 620)
    plot.setBackground("w")
    plot.setTitle("P-only temperature control: droop versus gain", color="#202830", size="16pt")
    plot.setLabel("bottom", "Proportional gain Kp", units="PWM/°C", **{"font-size": "12pt"})
    plot.setLabel("left", "Steady-state droop", units="°C", **{"font-size": "12pt"})
    plot.showGrid(x=True, y=True, alpha=0.18)
    plot.setXRange(0, 4.35, padding=0)
    plot.setYRange(0, 7.1, padding=0)
    for axis_name in ("left", "bottom"):
        plot.getAxis(axis_name).setTickFont(QFont("Arial", 11))
        plot.getAxis(axis_name).setPen(pg.mkPen("#65717d"))
        plot.getAxis(axis_name).setTextPen(pg.mkPen("#202830"))
    plot.addLegend(offset=(-15, 15))

    model_gains = [i * 0.025 for i in range(169)]
    model_droop = [
        (SETPOINT_C - ambient_c) / (1.0 + CHI_HEAT_C_PER_PWM * gain)
        for gain in model_gains
    ]
    plot.plot(
        model_gains, model_droop,
        pen=pg.mkPen("#c57425", width=3, style=pg.QtCore.Qt.PenStyle.DashLine),
        name="Model prediction",
    )
    plot.plot(
        [row["kp_pwm_per_C"] for row in summary],
        [row["measured_droop_C"] for row in summary],
        pen=pg.mkPen("#235f9e", width=2),
        symbol="o", symbolSize=11,
        symbolBrush=pg.mkBrush("#235f9e"),
        symbolPen=pg.mkPen("#ffffff", width=1),
        name="Measured: final 20 s",
    )
    app.processEvents()
    svg_path = FIGURE_DIR / "part_04_measured_vs_predicted_droop.svg"
    png_path = FIGURE_DIR / "part_04_measured_vs_predicted_droop.png"
    SVGExporter(plot.plotItem).export(str(svg_path))
    image_exporter = ImageExporter(plot.plotItem)
    image_exporter.parameters()["width"] = 1400
    image_exporter.export(str(png_path))
    plot.close()
    return svg_path, png_path


if __name__ == "__main__":
    ambient, rows = build_summary()
    print(save_summary(rows))
    print(*save_figure(ambient, rows), sep="\n")
