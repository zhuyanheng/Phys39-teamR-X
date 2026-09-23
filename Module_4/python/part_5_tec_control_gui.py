import csv
import math
import sys
import time
from datetime import datetime
from pathlib import Path

import pyqtgraph as pg
import serial
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


# --------------------------------------------------
# User settings
# --------------------------------------------------

SERIAL_PORT = "/dev/cu.usbmodem101"
BAUD_RATE = 9600

WINDOW_DURATION_S = 60.0
PLOT_UPDATE_INTERVAL_MS = 100

TEMPERATURE_MIN_C = 10.0
TEMPERATURE_MAX_C = 70.0

CSV_FILENAME = "module_04_tec"


# --------------------------------------------------
# Serial-line parser
# --------------------------------------------------

def parse_measurement(line):
    """Parse the labeled measurement line sent by the Arduino."""

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

    if not math.isfinite(time_s):
        return None

    if not 0 <= pwm <= 255:
        return None

    if heat_cool not in (0, 1):
        return None

    safety = fields.get("Safety", "UNKNOWN")
    heat_pwm = fields.get("Heat PWM", "")
    cool_pwm = fields.get("Cool PWM", "")
    limit_c = fields.get("Limit (C)", "")
    low_limit_c = fields.get("Low Limit (C)", "")
    operating_high_c = fields.get("Operating High (C)", "")
    return time_s, temperature_c, pwm, heat_cool, safety, heat_pwm, cool_pwm, limit_c, low_limit_c, operating_high_c


# --------------------------------------------------
# Main application window
# --------------------------------------------------

class TecControlWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Module 4 TEC Control and Safety")
        self.resize(1050, 850)

        self.times = []
        self.temperatures = []
        self.measured_pwms = []
        self.measured_directions = []
        self.serial_buffer = ""

        self.heat_mode = False

        self.open_serial_port()
        self.open_csv_file()
        self.create_interface()
        self.create_timer()

        # Always begin with a zero-PWM command.
        self.send_command(0, self.heat_mode)

    def open_serial_port(self):
        self.serial_port = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            timeout=0,
        )

        # Opening the serial connection may reset the Arduino.
        time.sleep(2.0)
        self.serial_port.reset_input_buffer()

    def open_csv_file(self):
        script_directory = Path(__file__).resolve().parent
        data_directory = script_directory.parent / "data"
        data_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.csv_path = data_directory / f"{CSV_FILENAME}_{timestamp}.csv"

        self.csv_file = self.csv_path.open(
            mode="x",
            newline="",
            encoding="utf-8",
        )

        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(
            ["time_s", "temperature_C", "pwm", "heat_cool", "safety",
             "heat_pwm_firmware", "cool_pwm_firmware", "limit_C", "low_limit_C",
             "operating_high_C"]
        )
        self.csv_file.flush()

    def create_interface(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        main_layout.addWidget(self.create_control_group())
        main_layout.addWidget(self.create_measurement_group())

        self.temperature_plot = self.create_temperature_plot()
        self.pwm_plot = self.create_pwm_plot()

        main_layout.addWidget(self.temperature_plot)
        main_layout.addWidget(self.pwm_plot)

        self.statusBar().showMessage(
            f"Connected to {SERIAL_PORT} | Saving to {self.csv_path.name}"
        )

    def create_control_group(self):
        group = QGroupBox("Manual Commands")
        layout = QGridLayout(group)

        self.direction_button = QPushButton("COOL")
        self.direction_button.setCheckable(True)
        self.direction_button.setChecked(False)
        self.direction_button.setMinimumHeight(42)
        self.direction_button.toggled.connect(
            self.handle_direction_change
        )
        self.update_direction_button_style()

        self.pwm_slider = QSlider(Qt.Orientation.Horizontal)
        self.pwm_slider.setRange(0, 255)
        self.pwm_slider.setValue(0)
        self.pwm_slider.setTickPosition(
            QSlider.TickPosition.TicksBelow
        )
        self.pwm_slider.setTickInterval(25)
        self.pwm_slider.valueChanged.connect(
            self.handle_slider_change
        )

        self.pwm_input = QLineEdit("0")
        self.pwm_input.setValidator(QIntValidator(0, 255, self))
        self.pwm_input.setMaximumWidth(80)
        self.pwm_input.editingFinished.connect(
            self.handle_text_entry
        )

        self.command_label = QLabel("Command: PWM 0, COOL")

        layout.addWidget(QLabel("Direction"), 0, 0)
        layout.addWidget(self.direction_button, 0, 1)
        layout.addWidget(QLabel("PWM command"), 1, 0)
        layout.addWidget(self.pwm_slider, 1, 1)
        layout.addWidget(self.pwm_input, 1, 2)
        layout.addWidget(self.command_label, 2, 0, 1, 3)

        return group

    def create_measurement_group(self):
        group = QGroupBox("Arduino Measurements")
        layout = QHBoxLayout(group)

        self.temperature_label = QLabel("Temperature: -- C")
        self.time_label = QLabel("Time: -- s")
        self.measured_pwm_label = QLabel("PWM: --")
        self.measured_direction_label = QLabel("Direction: --")
        self.safety_label = QLabel("Safety: --")

        layout.addWidget(self.temperature_label)
        layout.addWidget(self.time_label)
        layout.addWidget(self.measured_pwm_label)
        layout.addWidget(self.measured_direction_label)
        layout.addWidget(self.safety_label)

        return group

    def create_temperature_plot(self):
        plot = pg.PlotWidget(title="Temperature vs Arduino Time")
        plot.setBackground("w")
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setLabel("bottom", "Arduino Time", units="s")
        plot.setLabel("left", "Temperature", units="C")
        plot.setYRange(TEMPERATURE_MIN_C, TEMPERATURE_MAX_C)
        plot.setXRange(0, WINDOW_DURATION_S)

        self.temperature_curve = plot.plot(
            [],
            [],
            pen=pg.mkPen(color=(20, 90, 210), width=2),
        )

        return plot

    def create_pwm_plot(self):
        plot = pg.PlotWidget(title="Measured PWM vs Arduino Time")
        plot.setBackground("w")
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setLabel("bottom", "Arduino Time", units="s")
        plot.setLabel("left", "PWM")
        plot.setYRange(0, 255)
        plot.setXRange(0, WINDOW_DURATION_S)

        self.heat_pwm_curve = plot.plot(
            [],
            [],
            pen=pg.mkPen(color=(220, 30, 30), width=2),
            connect="finite",
            name="HEAT",
        )

        self.cool_pwm_curve = plot.plot(
            [],
            [],
            pen=pg.mkPen(color=(30, 90, 220), width=2),
            connect="finite",
            name="COOL",
        )

        plot.addLegend()

        return plot

    def create_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_serial_data)
        self.timer.start(PLOT_UPDATE_INTERVAL_MS)

    def update_direction_button_style(self):
        if self.heat_mode:
            self.direction_button.setText("HEAT")
            self.direction_button.setStyleSheet(
                "background-color: #d62828; color: white; font-weight: bold;"
            )
        else:
            self.direction_button.setText("COOL")
            self.direction_button.setStyleSheet(
                "background-color: #2563eb; color: white; font-weight: bold;"
            )

    def handle_direction_change(self, checked):
        self.heat_mode = checked
        self.update_direction_button_style()

        # A direction change forces the command back to zero PWM.
        if self.pwm_slider.value() != 0:
            self.pwm_slider.setValue(0)
        else:
            self.update_command_display()
            self.send_command(0, self.heat_mode)

    def handle_slider_change(self, value):
        self.pwm_input.setText(str(value))
        self.update_command_display()
        self.send_command(value, self.heat_mode)

    def handle_text_entry(self):
        text = self.pwm_input.text().strip()

        try:
            value = int(text)
        except ValueError:
            value = 0

        value = max(0, min(255, value))
        self.pwm_input.setText(str(value))

        if self.pwm_slider.value() != value:
            self.pwm_slider.setValue(value)
        else:
            self.update_command_display()
            self.send_command(value, self.heat_mode)

    def update_command_display(self):
        direction = "HEAT" if self.heat_mode else "COOL"
        pwm = self.pwm_slider.value()
        self.command_label.setText(
            f"Command: PWM {pwm}, {direction}"
        )

    def send_command(self, pwm, heat_mode):
        direction = "HEAT" if heat_mode else "COOL"
        command = f"SET PWM {pwm} DIR {direction}\n"

        try:
            self.serial_port.write(command.encode("utf-8"))
            print(f"Sent: {command.strip()}")
        except serial.SerialException as error:
            self.stop_after_serial_error(error)

    def read_serial_data(self):
        try:
            bytes_available = self.serial_port.in_waiting

            if bytes_available <= 0:
                return

            new_data = self.serial_port.read(bytes_available).decode(
                "utf-8",
                errors="ignore",
            )
        except serial.SerialException as error:
            self.stop_after_serial_error(error)
            return

        self.serial_buffer += new_data

        while "\n" in self.serial_buffer:
            line, self.serial_buffer = self.serial_buffer.split("\n", 1)
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
        heat_cool,
        safety,
        heat_pwm,
        cool_pwm,
        limit_c,
        low_limit_c,
        operating_high_c,
    ):
        if self.times and time_s < self.times[-1]:
            self.clear_plot_data()

        self.times.append(time_s)
        self.temperatures.append(temperature_c)
        self.measured_pwms.append(pwm)
        self.measured_directions.append(heat_cool)

        minimum_visible_time = time_s - WINDOW_DURATION_S

        while self.times and self.times[0] < minimum_visible_time:
            self.times.pop(0)
            self.temperatures.pop(0)
            self.measured_pwms.pop(0)
            self.measured_directions.pop(0)

        direction_text = "HEAT" if heat_cool == 1 else "COOL"

        self.temperature_label.setText(
            f"Temperature: {temperature_c:.2f} C"
        )
        self.time_label.setText(f"Time: {time_s:.2f} s")
        self.measured_pwm_label.setText(f"PWM: {pwm}")
        self.measured_direction_label.setText(
            f"Direction: {direction_text}"
        )
        self.safety_label.setText(
            f"Safety: {safety} | Operating: {low_limit_c}–{operating_high_c} C"
            f" | Safety limit: {limit_c} C"
        )
        self.safety_label.setStyleSheet(
            "color: red; font-weight: bold;" if safety != "OK" else "color: green;"
        )
        if safety == "SHUTDOWN":
            self.pwm_slider.blockSignals(True)
            self.pwm_slider.setValue(0)
            self.pwm_slider.blockSignals(False)
            self.pwm_input.setText("0")
            self.update_command_display()

        print(
            f"Temperature (C): {temperature_c:.2f}, "
            f"Time (s): {time_s:.2f}, "
            f"PWM: {pwm}, "
            f"Heat/Cool: {heat_cool}, Safety: {safety}, "
            f"Heat PWM: {heat_pwm}, Cool PWM: {cool_pwm}, "
            f"Limit (C): {limit_c}, Low Limit (C): {low_limit_c}, "
            f"Operating High (C): {operating_high_c}"
        )

        self.csv_writer.writerow(
            [f"{time_s:.2f}", f"{temperature_c:.2f}", pwm, heat_cool,
             safety, heat_pwm, cool_pwm, limit_c, low_limit_c, operating_high_c]
        )
        self.csv_file.flush()

        self.update_plots(time_s)

    def update_plots(self, newest_time):
        self.temperature_curve.setData(
            self.times,
            self.temperatures,
        )

        heat_values = [
            pwm if direction == 1 else math.nan
            for pwm, direction in zip(
                self.measured_pwms,
                self.measured_directions,
            )
        ]

        cool_values = [
            pwm if direction == 0 else math.nan
            for pwm, direction in zip(
                self.measured_pwms,
                self.measured_directions,
            )
        ]

        self.heat_pwm_curve.setData(self.times, heat_values)
        self.cool_pwm_curve.setData(self.times, cool_values)

        right_edge = max(WINDOW_DURATION_S, newest_time)
        left_edge = max(0.0, right_edge - WINDOW_DURATION_S)

        self.temperature_plot.setXRange(
            left_edge,
            right_edge,
            padding=0,
        )
        self.pwm_plot.setXRange(
            left_edge,
            right_edge,
            padding=0,
        )

    def clear_plot_data(self):
        self.times.clear()
        self.temperatures.clear()
        self.measured_pwms.clear()
        self.measured_directions.clear()

    def stop_after_serial_error(self, error):
        self.timer.stop()
        self.statusBar().showMessage(f"Serial error: {error}")

        QMessageBox.critical(
            self,
            "Serial Error",
            str(error),
        )

    def closeEvent(self, event):
        self.timer.stop()

        if self.serial_port.is_open:
            try:
                self.serial_port.write(b"SET PWM 0 DIR COOL\n")
            except serial.SerialException:
                pass

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
        window = TecControlWindow()
    except serial.SerialException as error:
        QMessageBox.critical(
            None,
            "Serial Port Error",
            (
                f"Could not open {SERIAL_PORT}.\n\n"
                f"{error}\n\n"
                "Close Arduino Serial Monitor and check the selected port."
            ),
        )
        return 1

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
