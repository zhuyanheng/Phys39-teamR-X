import csv
import math
import sys
import time
from pathlib import Path

import pyqtgraph as pg
import serial
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox


# --------------------------------------------------
# User settings
# --------------------------------------------------

SERIAL_PORT = "/dev/cu.usbmodem101"
BAUD_RATE = 9600

WINDOW_DURATION_S = 60.0
PLOT_UPDATE_INTERVAL_MS = 100

TEMPERATURE_MIN_C = 10.0
TEMPERATURE_MAX_C = 50.0

CSV_FILENAME = "module_03_part_4_data.csv"


# --------------------------------------------------
# Serial-line parser
# --------------------------------------------------

def parse_measurement(line):
    """
    Parse an Arduino measurement line.

    Required fields:
        Temperature (C)
        Time (s)
        PWM
        Heat/Cool

    Additional fields, such as Voltage (V), are ignored.
    """

    fields = {}

    for section in line.split(","):
        if ":" not in section:
            continue

        label, value = section.split(":", 1)
        fields[label.strip()] = value.strip()

    try:
        temperature_c = float(fields["Temperature (C)"])
        time_s = float(fields["Time (s)"])
        pwm = int(float(fields["PWM"]))
        heat_cool = int(float(fields["Heat/Cool"]))

    except (KeyError, ValueError):
        return None

    if not math.isfinite(temperature_c):
        return None

    if not math.isfinite(time_s):
        return None

    if not 0 <= pwm <= 255:
        return None

    if heat_cool not in (0, 1):
        return None

    return time_s, temperature_c, pwm, heat_cool


# --------------------------------------------------
# Main application window
# --------------------------------------------------

class TemperatureStripChart(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Module 3 Temperature Strip Chart")
        self.resize(900, 550)

        self.times = []
        self.temperatures = []
        self.serial_buffer = ""

        self.open_serial_port()
        self.open_csv_file()
        self.create_plot()
        self.create_timer()

    def open_serial_port(self):
        self.serial_port = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=0
        )

        # Opening the serial port may reset the Arduino.
        time.sleep(2.0)
        self.serial_port.reset_input_buffer()

    def open_csv_file(self):
        csv_path = Path(CSV_FILENAME)

        self.csv_file = csv_path.open(
            mode="w",
            newline="",
            encoding="utf-8"
        )

        self.csv_writer = csv.writer(self.csv_file)

        self.csv_writer.writerow([
            "time_s",
            "temperature_C",
            "pwm",
            "heat_cool"
        ])

        self.csv_file.flush()

    def create_plot(self):
        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        self.plot_widget.setLabel(
            "bottom",
            "Arduino Time",
            units="s"
        )

        self.plot_widget.setLabel(
            "left",
            "Temperature",
            units="C"
        )

        self.plot_widget.setYRange(
            TEMPERATURE_MIN_C,
            TEMPERATURE_MAX_C
        )

        self.plot_widget.setXRange(
            0,
            WINDOW_DURATION_S
        )

        temperature_pen = pg.mkPen(
            color=(0, 90, 220),
            width=2
        )

        self.temperature_curve = self.plot_widget.plot(
            [],
            [],
            pen=temperature_pen
        )

    def create_timer(self):
        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.read_serial_data
        )

        self.timer.start(
            PLOT_UPDATE_INTERVAL_MS
        )

    def read_serial_data(self):
        bytes_available = self.serial_port.in_waiting

        if bytes_available <= 0:
            return

        new_data = self.serial_port.read(
            bytes_available
        ).decode(
            "utf-8",
            errors="ignore"
        )

        self.serial_buffer += new_data

        while "\n" in self.serial_buffer:
            line, self.serial_buffer = (
                self.serial_buffer.split("\n", 1)
            )

            line = line.strip()

            if not line:
                continue

            measurement = parse_measurement(line)

            if measurement is None:
                continue

            self.process_measurement(*measurement)

    def process_measurement(
        self,
        time_s,
        temperature_c,
        pwm,
        heat_cool
    ):
        # Clear the plot if the Arduino time resets.
        if self.times and time_s < self.times[-1]:
            self.times.clear()
            self.temperatures.clear()

        self.times.append(time_s)
        self.temperatures.append(temperature_c)

        # Remove data outside the visible rolling window.
        minimum_visible_time = (
            time_s - WINDOW_DURATION_S
        )

        while (
            self.times
            and self.times[0] < minimum_visible_time
        ):
            self.times.pop(0)
            self.temperatures.pop(0)

        # Print only the extracted values.
        print(
            f"Temperature (C): {temperature_c:.2f}, "
            f"Time (s): {time_s:.2f}, "
            f"PWM: {pwm}, "
            f"Heat/Cool: {heat_cool}"
        )

        # Save the accepted measurement to CSV.
        self.csv_writer.writerow([
            f"{time_s:.2f}",
            f"{temperature_c:.2f}",
            pwm,
            heat_cool
        ])

        self.csv_file.flush()

        # Update the temperature plot.
        self.temperature_curve.setData(
            self.times,
            self.temperatures
        )

        right_edge = max(
            WINDOW_DURATION_S,
            time_s
        )

        left_edge = max(
            0.0,
            right_edge - WINDOW_DURATION_S
        )

        self.plot_widget.setXRange(
            left_edge,
            right_edge,
            padding=0
        )

    def closeEvent(self, event):
        self.timer.stop()

        if self.serial_port.is_open:
            self.serial_port.close()

        self.csv_file.flush()
        self.csv_file.close()

        event.accept()


# --------------------------------------------------
# Program entry point
# --------------------------------------------------

def main():
    app = QApplication(sys.argv)

    try:
        window = TemperatureStripChart()

    except serial.SerialException as error:
        QMessageBox.critical(
            None,
            "Serial Port Error",
            (
                f"Could not open {SERIAL_PORT}.\n\n"
                f"{error}\n\n"
                "Close Arduino Serial Monitor and check "
                "the selected serial port."
            )
        )

        return 1

    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())