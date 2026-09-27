import csv
import math
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIRECTORY.parent / "data" / "part_7_integrated_control_data.csv"
OUTPUT_PATH = SCRIPT_DIRECTORY.parent / "figures" / "part_7_heat_cool_record.png"


def read_data():
    times = []
    temperatures = []
    pwms = []
    directions = []

    with DATA_PATH.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            times.append(float(row["time_s"]))
            temperatures.append(float(row["temperature_C"]))
            pwms.append(int(row["pwm"]))
            directions.append(int(row["heat_cool"]))

    return times, temperatures, pwms, directions


def selected_values(values, pwms, directions, selected_direction):
    return [
        value if pwm > 0 and direction == selected_direction else math.nan
        for value, pwm, direction in zip(values, pwms, directions)
    ]


def main():
    times, temperatures, pwms, directions = read_data()
    heat_temperatures = selected_values(temperatures, pwms, directions, 1)
    cool_temperatures = selected_values(temperatures, pwms, directions, 0)
    heat_pwms = selected_values(pwms, pwms, directions, 1)
    cool_pwms = selected_values(pwms, pwms, directions, 0)

    pg.setConfigOption("background", "w")
    pg.setConfigOption("foreground", "#333333")

    app = QApplication.instance() or QApplication([])
    figure = pg.GraphicsLayoutWidget(show=False)
    figure.resize(1600, 1000)

    title = pg.LabelItem(
        "Module 3 Part 7: Low-Power Manual Heat/Cool Record",
        size="18pt",
        bold=True,
        color="#222222",
    )
    subtitle = pg.LabelItem(
        "PWM limit used: 40/255 | Thermistor average: 1000 samples | "
        "Serial rate: 9600 baud",
        size="11pt",
        color="#444444",
    )
    figure.addItem(title, row=0, col=0)
    figure.addItem(subtitle, row=1, col=0)

    temperature_plot = figure.addPlot(row=2, col=0)
    temperature_plot.setLabel("left", "Temperature", units="C")
    temperature_plot.setLabel("bottom", "Arduino Time", units="s")
    temperature_plot.showGrid(x=True, y=True, alpha=0.25)
    temperature_plot.setYRange(19, 31)
    temperature_plot.addLegend(offset=(12, 12))
    temperature_plot.plot(
        times,
        temperatures,
        pen=pg.mkPen("#777777", width=2),
        name="All measurements",
    )
    temperature_plot.plot(
        times,
        heat_temperatures,
        pen=pg.mkPen("#d55e00", width=4),
        connect="finite",
        name="HEAT, PWM 40",
    )
    temperature_plot.plot(
        times,
        cool_temperatures,
        pen=pg.mkPen(
            "#0072b2",
            width=4,
            style=Qt.PenStyle.DashLine,
        ),
        connect="finite",
        name="COOL, PWM 40",
    )

    pwm_plot = figure.addPlot(row=3, col=0)
    pwm_plot.setLabel("left", "PWM command", units="0-255")
    pwm_plot.setLabel("bottom", "Arduino Time", units="s")
    pwm_plot.showGrid(x=True, y=True, alpha=0.25)
    pwm_plot.setYRange(0, 50)
    pwm_plot.setXLink(temperature_plot)
    pwm_plot.addLegend(offset=(12, 12))
    pwm_plot.plot(
        times,
        heat_pwms,
        pen=pg.mkPen("#d55e00", width=4),
        connect="finite",
        name="HEAT command",
    )
    pwm_plot.plot(
        times,
        cool_pwms,
        pen=pg.mkPen(
            "#0072b2",
            width=4,
            style=Qt.PenStyle.DashLine,
        ),
        connect="finite",
        name="COOL command",
    )

    note = pg.LabelItem(
        "Observed active intervals: HEAT 26.0-65.0 s, 22.06-28.90 C; "
        "COOL 88.5-179.0 s, 27.68-20.87 C.",
        size="10pt",
        color="#333333",
    )
    figure.addItem(note, row=4, col=0)

    app.processEvents()
    if not figure.grab().save(str(OUTPUT_PATH), "PNG"):
        raise RuntimeError(f"Could not save {OUTPUT_PATH}")

    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
