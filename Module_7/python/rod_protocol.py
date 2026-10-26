"""Module 7 serial protocol for the six-channel rod instrument.

Hardware-free and GUI-free, so it can be tested without Qt, pyqtgraph, or a
serial port, in the same way Module_6/python/pi_controller.py keeps the control
arithmetic testable.

The firmware emits, once at startup,

    #firmware,module_07_rod_controller,2026-10-26
    #channels,tec=A0,rod1=A1,rod2=A2,rod3=A3,rod4=A4,rod5=A5
    #pins,heat=D9,cool=D10,baud=9600,report_ms=500
    #DATA,time_s,tec_C,rod1_C,rod2_C,rod3_C,rod4_C,rod5_C,pwm,heat_cool,
          heat_pwm,cool_pwm,limit_C,safety,rod_ok

and then one measurement line every 500 ms:

    DATA,12.50,23.41,23.38,23.36,23.34,23.31,23.29,120,1,120,0,60.00,OK,5

Only lines that start with ``DATA,`` are measurements. Every diagnostic line
starts with ``#`` so that a stray debug print can never be mistaken for data.
``FIELD_NAMES`` must stay in sync with ``printHeader()`` in
Module_7/arduino/module_07_rod_controller/module_07_rod_controller.ino.
"""
from __future__ import annotations

import math
from typing import NamedTuple, Optional, Sequence, Tuple

# Channel order: index 0 is the TEC base thermistor, 1..5 are rod 1..5.
CHANNELS = ("tec", "rod1", "rod2", "rod3", "rod4", "rod5")
ROD_CHANNELS = CHANNELS[1:]

DATA_PREFIX = "DATA,"
DIAGNOSTIC_PREFIX = "#"

#: Measurement columns, in DATA-line order. The GUI builds its CSV columns from
#: this tuple, so a channel can never be dropped by hand-editing a column list.
CHANNEL_FIELDS = ("time_s", "tec_C") + tuple(f"{channel}_C" for channel in ROD_CHANNELS)

FIELD_NAMES = CHANNEL_FIELDS + ("pwm", "heat_cool", "heat_pwm", "cool_pwm",
                                "limit_C", "safety", "rod_ok")


#: Values the firmware prints in the safety field.
SAFETY_OK = "OK"
SAFETY_SHUTDOWN = "SHUTDOWN"
VALID_SAFETY = (SAFETY_OK, SAFETY_SHUTDOWN)


class RodSample(NamedTuple):
    """One accepted ``DATA`` line."""

    time_s: float
    tec_c: float
    rods_c: Tuple[float, ...]
    pwm: int
    heat_cool: int
    heat_pwm: Optional[int]
    cool_pwm: Optional[int]
    limit_c: Optional[float]
    safety: str
    rod_ok: int

    @property
    def signed_pwm(self) -> int:
        """Positive heats, negative cools (Module 6 sign convention)."""
        return self.pwm if self.heat_cool else -self.pwm

    @property
    def measurement(self) -> tuple:
        """This sample's values in ``FIELD_NAMES`` order.

        The GUI writes ``dict(zip(FIELD_NAMES, sample.measurement))``, so the
        CSV measurement block cannot drift from the DATA line.
        """
        return ((self.time_s, self.tec_c) + tuple(self.rods_c)
                + (self.pwm, self.heat_cool, self.heat_pwm, self.cool_pwm,
                   self.limit_c, self.safety, self.rod_ok))

    @property
    def valid_rod_channels(self) -> int:
        return sum(1 for value in self.rods_c if math.isfinite(value))

    def issue(self, low_c: float = 10.0, high_c: float = 45.0) -> Optional[str]:
        """Return a one-line description of why this sample cannot drive PI.

        Only the TEC channel is in the control and safety path. An unusable rod
        channel is reported (``rod_ok``) but never blocks the actuator, because
        a loose rod probe must not abort a long steady-state run.
        """
        if not math.isfinite(self.time_s) or self.time_s < 0:
            return f"invalid Arduino time {self.time_s!r}"
        if not math.isfinite(self.tec_c):
            return "TEC channel is not a finite number"
        if not low_c <= self.tec_c <= high_c:
            return f"TEC channel {self.tec_c:.2f} C outside {low_c:g}-{high_c:g} C"
        if self.safety != SAFETY_OK:
            return f"firmware safety state {self.safety}"
        if self.pwm != 0 and self.heat_cool not in (0, 1):
            return f"invalid direction {self.heat_cool}"
        return None


def _optional_float(text: str) -> Optional[float]:
    """Parse an optional field without turning a blank field into an error."""
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _optional_int(text: str) -> Optional[int]:
    value = _optional_float(text)
    return None if value is None else int(value)


def parse_data_line(line: str) -> Optional[RodSample]:
    """Parse one serial line; return ``None`` for anything that is not a sample.

    Rejecting rather than raising keeps a corrupted or truncated line from
    stopping a run that is already 30 minutes old.
    """
    line = line.strip()
    if not line.startswith(DATA_PREFIX):
        return None

    fields = [field.strip() for field in line.split(",")]
    if len(fields) != len(FIELD_NAMES) + 1:
        return None

    values = dict(zip(FIELD_NAMES, fields[1:]))

    try:
        time_s = float(values["time_s"])
        tec_c = float(values["tec_C"])
        rods_c = tuple(float(values[f"{channel}_C"]) for channel in ROD_CHANNELS)
        pwm = int(float(values["pwm"]))
        heat_cool = int(float(values["heat_cool"]))
        rod_ok = int(float(values["rod_ok"]))
    except (ValueError, KeyError):
        return None

    if not math.isfinite(time_s) or time_s < 0:
        return None
    if not 0 <= pwm <= 255:
        return None
    if heat_cool not in (0, 1):
        return None
    if not 0 <= rod_ok <= len(ROD_CHANNELS):
        return None

    safety = values["safety"].upper()
    if safety not in VALID_SAFETY:
        return None

    return RodSample(
        time_s=time_s,
        tec_c=tec_c,
        rods_c=rods_c,
        pwm=pwm,
        heat_cool=heat_cool,
        heat_pwm=_optional_int(values["heat_pwm"]),
        cool_pwm=_optional_int(values["cool_pwm"]),
        limit_c=_optional_float(values["limit_C"]),
        safety=safety,
        rod_ok=rod_ok,
    )



def parse_lines(text: str) -> list:
    """Parse a block of serial text; skip diagnostics and unparsable lines."""
    samples = []
    for line in text.splitlines():
        sample = parse_data_line(line)
        if sample is not None:
            samples.append(sample)
    return samples


def build_data_line(
    time_s: float,
    tec_c: float,
    rods_c: Sequence[float],
    pwm: int,
    heat_cool: int,
    heat_pwm: int,
    cool_pwm: int,
    limit_c: float,
    safety: str,
    rod_ok: int,
) -> str:
    """Build the exact line the firmware prints. Used by the tests as a mirror.

    ``format(float('nan'), '.2f')`` is ``'nan'``, so an unusable channel is
    written the same way the firmware writes it.
    """
    if len(rods_c) != len(ROD_CHANNELS):
        raise ValueError(f"expected {len(ROD_CHANNELS)} rod channels")
    cells = [f"{time_s:.2f}", f"{tec_c:.2f}"]
    cells += [f"{value:.2f}" for value in rods_c]
    cells += [str(int(pwm)), str(int(heat_cool)), str(int(heat_pwm)),
              str(int(cool_pwm)), f"{limit_c:.2f}", str(safety), str(int(rod_ok))]
    return DATA_PREFIX + ",".join(cells)

