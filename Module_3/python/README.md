# Module 3 Python Scripts

This directory contains the Python GUI applications used for the Module 3 experiments.
These scripts communicate with the Part 6 Arduino sketch via serial to log temperature data, send manual control commands, and visualize the results.

## Scripts

| Part | Script | Purpose |
|---|---|---|
| Part 4 | [Temperature Strip Chart](./part_4_graphing.py) | A display-only GUI. Reads Arduino measurements, plots temperature and PWM versus time in a 60-second rolling window, and logs data to CSV. |
| Part 5 | [TEC Control GUI](./part_5_tec_control_gui.py) | The complete manual-control interface. Adds heat/cool toggles, a PWM slider, a synchronized text box, and a second live plot for PWM vs. time. |
| Evidence figure | [Part 7 record plot](./plot_part_7_record.py) | Recreates the labeled low-power heat/cool figure from the canonical Part 7 CSV file. |

## Dependencies

Install the repository dependencies from the repository root:

    python3 -m pip install -r requirements.txt

## Serial Communication

### Port Configuration

Before running any script, update the `SERIAL_PORT` variable at the top of the Python file to match your system's Arduino connection:

- **macOS**: `SERIAL_PORT = "/dev/cu.usbmodem101"`
- **Windows**: `SERIAL_PORT = "COM3"` (or the correct COM port)

Baud rate is set to `9600` to match the Arduino sketch.

### Command Format (Part 5)

The GUI sends newline-terminated commands to the Arduino:

    SET PWM <0-255> DIR <HEAT/COOL>\n

The Arduino responds with measurement lines:

    Temperature (C): XX.XX, Time (s): XX.XX, PWM: XXX, Heat/Cool: X\n

## Usage

1. Upload the corresponding Arduino sketch (Part 4 for `part_4_graphing.py`, or Part 6 for `part_5_tec_control_gui.py`).
2. **Close the Arduino Serial Monitor.** The serial port is exclusive; the Python script will fail if the Serial Monitor is open.
3. Run the required Python script from the repository root.

   Display-only strip chart:

       python3 Module_3/python/part_4_graphing.py

   Manual-control GUI:

       python3 Module_3/python/part_5_tec_control_gui.py

4. To stop the script safely, close the GUI window. The script will automatically send a zero-PWM command (`SET PWM 0 DIR COOL\n`) to the Arduino and safely close the CSV file.

## Data Output

- **Part 4**: Saves data to `Module_3/data/part_4_data.csv`
- **Part 5**: Saves data to `Module_3/data/part_7_integrated_control_data.csv`
- **Format**: `time_s, temperature_C, pwm, heat_cool` (1 = HEAT, 0 = COOL)

## Notes

- **Safety**: The Python GUI sends a `PWM 0` command immediately upon connection. Always ensure the Arduino starts with PWM 0.
- **GUI Sync**: In Part 5, the PWM slider and text box are two-way synchronized. If you type an invalid number (e.g., 300 or -10), the script automatically clamps it to the valid `0-255` range.
- **Direction Change**: Changing the direction between HEAT and COOL automatically resets the PWM command to 0 to prevent sudden current spikes.
- **Data Logging**: Both scripts save CSV files under `Module_3/data`. Their paths are calculated from each script's location, so they do not depend on the terminal's current directory.
