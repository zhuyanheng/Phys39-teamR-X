"""Build representative low- and high-gain P-control strip-chart traces.

Each figure shows measured temperature versus time with the setpoint as a
reference line (left axis) and the commanded PWM magnitude versus time (right
axis), matching the live GUI strip chart. Pure-stdlib SVG output; no GUI or
third-party packages are required. Outputs go to docs/figures/module_05/.
"""

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "Module_5" / "data"
FIGURE_DIR = ROOT / "docs" / "figures" / "module_05"

RUNS = {
    "low_gain_kp0.25": "20260930_110723_droop_kp0p25.csv",
    "high_gain_kp4": "20260930_112955_droop_kp4.csv",
}
SETPOINT_C = 30.0
TEMP_COLOR = "#235f9e"
PWM_COLOR = "#c62828"
SETPOINT_COLOR = "#c57425"

WIDTH = 920
HEIGHT = 430
LEFT, RIGHT = 70, WIDTH - 70
TOP, BOTTOM = 56, HEIGHT - 56


def read_rows(name):
    with (DATA_DIR / name).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def nice_ticks(lo, hi, count=6):
    span = hi - lo
    if span <= 0:
        return [lo]
    raw = span / max(1, count - 1)
    pow10 = 10 ** math.floor(math.log10(raw))
    step = raw
    for mult in (1.0, 2.0, 2.5, 5.0, 10.0):
        if raw <= mult * pow10:
            step = mult * pow10
            break
    else:
        step = 10 * pow10
    ticks = []
    value = math.ceil(lo / step - 1e-9) * step
    while value <= hi + 1e-9:
        ticks.append(value)
        value += step
    return ticks


def fmt(v):
    return f"{v:g}"


def build_svg(rows, gain, title):
    times = [float(r["time_s"]) for r in rows]
    temps = [float(r["temperature_C"]) for r in rows]
    pwms = [float(r["pwm"]) for r in rows]

    t_lo, t_hi = min(times), max(times)
    temp_lo = min(min(temps), SETPOINT_C) - 1.0
    temp_hi = max(max(temps), SETPOINT_C) + 1.0
    pwm_hi = max(5.0, (math.ceil(max(pwms) / 5.0)) * 5.0)

    def xp(t):
        return LEFT + (t - t_lo) * (RIGHT - LEFT) / (t_hi - t_lo)

    def yp_temp(v):
        return TOP + (temp_hi - v) * (BOTTOM - TOP) / (temp_hi - temp_lo)

    def yp_pwm(v):
        return TOP + (pwm_hi - v) * (BOTTOM - TOP) / pwm_hi

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    s.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#fff"/>')
    s.append(f'<text x="{WIDTH/2}" y="26" text-anchor="middle" font-family="Arial" font-size="16" fill="#202830">{title}</text>')

    for t in nice_ticks(t_lo, t_hi):
        x = xp(t)
        s.append(f'<line x1="{x:.1f}" y1="{TOP}" x2="{x:.1f}" y2="{BOTTOM}" stroke="#e3e8ee"/>')
        s.append(f'<text x="{x:.1f}" y="{HEIGHT-34}" text-anchor="middle" font-family="Arial" font-size="11" fill="#4b5563">{fmt(t)}</text>')
    s.append(f'<text x="{(LEFT+RIGHT)/2}" y="{HEIGHT-10}" text-anchor="middle" font-family="Arial" font-size="12" fill="#202830">Arduino time (s)</text>')

    for v in nice_ticks(temp_lo, temp_hi):
        y = yp_temp(v)
        s.append(f'<line x1="{LEFT}" y1="{y:.1f}" x2="{RIGHT}" y2="{y:.1f}" stroke="#e3e8ee"/>')
        s.append(f'<text x="{LEFT-8}" y="{y+4:.1f}" text-anchor="end" font-family="Arial" font-size="11" fill="#235f9e">{fmt(v)}</text>')
    s.append(f'<text x="16" y="{(TOP+BOTTOM)/2}" text-anchor="middle" font-family="Arial" font-size="12" fill="#235f9e" transform="rotate(-90 16 {(TOP+BOTTOM)/2})">Temperature (°C)</text>')

    for v in nice_ticks(0.0, pwm_hi):
        y = yp_pwm(v)
        s.append(f'<text x="{RIGHT+8}" y="{y+4:.1f}" font-family="Arial" font-size="11" fill="#c62828">{fmt(v)}</text>')
    s.append(f'<text x="{WIDTH-14}" y="{(TOP+BOTTOM)/2}" text-anchor="middle" font-family="Arial" font-size="12" fill="#c62828" transform="rotate(90 {WIDTH-14} {(TOP+BOTTOM)/2})">PWM</text>')

    s.append(f'<rect x="{LEFT}" y="{TOP}" width="{RIGHT-LEFT}" height="{BOTTOM-TOP}" fill="none" stroke="#46505b"/>')

    ysp = yp_temp(SETPOINT_C)
    s.append(f'<line x1="{LEFT}" y1="{ysp:.1f}" x2="{RIGHT}" y2="{ysp:.1f}" stroke="{SETPOINT_COLOR}" stroke-width="2" stroke-dasharray="7,5"/>')

    s.append('<polyline points="' + " ".join(f"{xp(t):.1f},{yp_pwm(p):.1f}" for t, p in zip(times, pwms)) + f'" fill="none" stroke="{PWM_COLOR}" stroke-width="1.6"/>')
    s.append('<polyline points="' + " ".join(f"{xp(t):.1f},{yp_temp(v):.1f}" for t, v in zip(times, temps)) + f'" fill="none" stroke="{TEMP_COLOR}" stroke-width="2.2"/>')

    lx, ly = LEFT + 12, TOP + 14
    for color, label in [(TEMP_COLOR, "Temperature"), (SETPOINT_COLOR, f"Setpoint {SETPOINT_C:g} °C"), (PWM_COLOR, "PWM")]:
        s.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+18}" y2="{ly}" stroke="{color}" stroke-width="2.2"/>')
        s.append(f'<text x="{lx+24}" y="{ly+4}" font-family="Arial" font-size="11" fill="#202830">{label}</text>')
        lx += 24 + len(label) * 6.5 + 16

    s.append("</svg>")
    return "\n".join(s)


def main():
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for label, filename in RUNS.items():
        rows = read_rows(filename)
        active = [r for r in rows if r["p_active"] == "1"]
        gain = float(active[0]["Kp_pwm_per_C"]) if active else 0.0
        title = f"P-only strip chart, Kp = {gain:g} PWM/°C, setpoint 30 °C (final {rows[-1]['temperature_C']} °C)"
        out = FIGURE_DIR / f"{label}_trace.svg"
        out.write_text(build_svg(rows, gain, title), encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
