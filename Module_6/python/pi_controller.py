"""Hardware-independent P/PI arithmetic. Signed PWM: positive heats."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ControlResult:
    time_s: float
    dt_s: float
    error_c: float
    integral_c_s: float
    p_pwm: float
    i_pwm: float
    requested_pwm: float
    clamped_pwm: float
    sent_pwm: int
    saturated: bool
    integration_blocked: bool


class PIController:
    def __init__(self, mode="P", setpoint=30., kp=2., ki=0., pwm_limit=255,
                 anti_windup=True, max_interval=2.):
        self.mode = mode
        self.setpoint = setpoint
        self.kp = kp
        self.ki = ki
        self.pwm_limit = pwm_limit
        self.anti_windup = anti_windup
        self.max_interval = max_interval
        self.reset()
        self.validate_settings()

    def validate_settings(self):
        values = (self.setpoint, self.kp, self.ki, self.pwm_limit, self.max_interval)
        if not all(math.isfinite(x) for x in values):
            raise ValueError("Settings must be finite")
        if self.mode not in ("P", "PI") or not 10 <= self.setpoint <= 45:
            raise ValueError("Choose P/PI and a setpoint from 10 to 45 C")
        if self.kp < 0 or self.ki < 0 or self.max_interval <= 0:
            raise ValueError("Gains must be nonnegative; sample timeout must be positive")
        if not 1 <= self.pwm_limit <= 255 or int(self.pwm_limit) != self.pwm_limit:
            raise ValueError("PWM limit must be an integer from 1 to 255")

    def reset(self):
        self.integral = 0.
        self.previous_time = None

    def step(self, time_s, temperature_c):
        self.validate_settings()
        if not math.isfinite(time_s) or time_s < 0:
            raise ValueError("Invalid Arduino measurement time")
        if not math.isfinite(temperature_c) or not 10 <= temperature_c <= 45:
            raise ValueError("Temperature is outside the 10-45 C operating range")
        dt = 0. if self.previous_time is None else time_s-self.previous_time
        if self.previous_time is not None and not 0 < dt <= self.max_interval:
            raise ValueError("Duplicate/reversed Arduino time or measurement gap > 2 s")
        error = self.setpoint-temperature_c
        p_term = self.kp*error
        ki = self.ki if self.mode == "PI" else 0.
        proposed_q = self.integral+error*dt if self.mode == "PI" else 0.
        proposed_command = p_term+ki*proposed_q
        if not all(math.isfinite(x) for x in (proposed_q, p_term, proposed_command)):
            raise ValueError("Controller calculation overflow")
        # Freeze only accumulation that would drive farther into saturation.
        # Opposite-sign error is allowed to unwind the stored integral.
        blocked = self.mode == "PI" and self.anti_windup and (
            (proposed_command > self.pwm_limit and error > 0)
            or (proposed_command < -self.pwm_limit and error < 0))
        q = self.integral if blocked else proposed_q
        i_term = ki*q
        requested = p_term+i_term
        clamped = max(-self.pwm_limit, min(self.pwm_limit, requested))
        sent = int(round(clamped))
        result = ControlResult(time_s, dt, error, q, p_term, i_term,
                               requested, clamped, sent,
                               abs(requested) > self.pwm_limit, bool(blocked))
        self.integral = q
        self.previous_time = time_s
        return result
