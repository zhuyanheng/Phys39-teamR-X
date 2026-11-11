"""Validated experiment plans and measured temperature-to-PWM lookup tables.

No serial or GUI imports. Plans are bounded identically to angstrom_core.h.
"""
from dataclasses import asdict, dataclass
import csv
import hashlib
import json
import math
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1]
FIRMWARE_ID = 'module_08_angstrom_v2'
BAUD = 115200
MIN_C, MAX_C, BASE_LIMIT_C = 10., 45., 56.
MAX_STEPS = MAX_POINTS = 12
TEMPERATURE_MODES = ('OPEN', 'P', 'PI')
RAW_MODES = ('RAW_ZERO', 'RAW_POS')
MODES = TEMPERATURE_MODES + RAW_MODES

@dataclass(frozen=True)
class Step:
    duration_s: float
    Ta_C: float
    Tb_C: float
    period_s: float
    mode: str
    Kp: float
    Ki: float
    Ua_pwm: float = 0.
    Ub_pwm: float = 0.

    def validate(self):
        vals = (self.duration_s, self.Ta_C, self.Tb_C, self.period_s, self.Kp, self.Ki, self.Ua_pwm, self.Ub_pwm)
        if not all(math.isfinite(v) for v in vals):
            raise ValueError('Every schedule value must be finite')
        if self.mode not in MODES or not 1 <= self.duration_s <= 86400:
            raise ValueError('Choose OPEN/P/PI/RAW_ZERO/RAW_POS and duration 1–86400 s')
        if self.mode in RAW_MODES:
            if any(v != 0 for v in (self.Ta_C, self.Tb_C, self.Kp, self.Ki)):
                raise ValueError('Raw PWM uses Ua/Ub; inactive temperature/gain fields must be zero')
            if self.Ub_pwm <= 0 or abs(self.Ua_pwm)+self.Ub_pwm > 255:
                raise ValueError('Raw PWM needs Ub > 0 and |Ua| + Ub <= 255')
            if self.mode == 'RAW_ZERO' and self.Ua_pwm != 0:
                raise ValueError('RAW_ZERO requires Ua = 0')
            if self.mode == 'RAW_POS' and self.Ua_pwm <= self.Ub_pwm:
                raise ValueError('RAW_POS requires Ua > Ub > 0')
        elif self.Tb_C < 0 or self.Ta_C-self.Tb_C < MIN_C or self.Ta_C+self.Tb_C > MAX_C:
            raise ValueError('Entire waveform must stay within the existing 10–45 C operating range')
        elif self.Ua_pwm != 0 or self.Ub_pwm != 0:
            raise ValueError('Temperature modes do not use Ua/Ub PWM parameters')
        if not 100 <= self.period_s <= 86400:
            raise ValueError('Period must be at least 100 s (also during rehearsal)')
        if not 0 <= self.Kp <= 1000 or not 0 <= self.Ki <= 100:
            raise ValueError('Kp must be 0–1000 and Ki 0–100')


def reference_calibration(path=None):
    """Use the measured signed-PWM steady-state table, without extrapolation.

    Supports the earlier direction/pwm/steady_temperature_C table or a two-column
    temperature_C,signed_pwm table. Duplicate zero-command baseline rows must agree.
    """
    path = Path(path or MODULE / 'data/reference/module_04_steady_state.csv')
    with path.open(newline='', encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    points = []
    for row in rows:
        if 'temperature_C' in row:
            t, pwm = float(row['temperature_C']), float(row['signed_pwm'])
        else:
            t = float(row['steady_temperature_C'])
            direction = row['direction'].upper()
            if direction not in ('HEAT', 'COOL'):
                raise ValueError('Calibration direction must be HEAT or COOL')
            pwm = float(row['pwm']) * (1 if direction == 'HEAT' else -1)
        if (t, pwm) not in points:
            points.append((t, pwm))
    points.sort()
    validate_points(points)
    source = {'source': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'qualification': 'Measured static curve; Module 4 settling audit remains applicable. Revalidate with the rod attached.'}
    slopes = []
    for sign in (1, -1):
        branch = [(u, t) for t, u in points if sign*u >= 0]
        if len(branch) < 2:
            break
        mean_u = sum(u for u, t in branch)/len(branch)
        mean_t = sum(t for u, t in branch)/len(branch)
        denominator = sum((u-mean_u)**2 for u, t in branch)
        if not denominator:
            break
        slopes.append(sum((u-mean_u)*(t-mean_t) for u, t in branch)/denominator)
    if len(slopes) == 2 and min(slopes) > 0:
        source.update(chi_heat_C_per_pwm=slopes[0], chi_cool_C_per_pwm=slopes[1],
                      heating_to_cooling_ratio=slopes[0]/slopes[1])
    return points, source


def validate_points(points):
    if not 2 <= len(points) <= MAX_POINTS:
        raise ValueError('Calibration needs 2–12 unique points')
    previous = None
    for t, pwm in points:
        if not math.isfinite(t) or not math.isfinite(pwm) or abs(pwm) > 255:
            raise ValueError('Invalid calibration temperature or PWM')
        if previous and (t <= previous[0] or pwm <= previous[1]):
            raise ValueError('Calibration temperature and signed PWM must both strictly increase')
        previous = (t, pwm)


def inverse_pwm(temperature, points):
    validate_points(points)
    if not math.isfinite(temperature) or not points[0][0] <= temperature <= points[-1][0]:
        raise ValueError('Requested temperature is outside measured calibration; extrapolation is disabled')
    for (ta, ua), (tb, ub) in zip(points, points[1:]):
        if temperature <= tb:
            return ua+(ub-ua)*(temperature-ta)/(tb-ta)
    raise ValueError('Unusable calibration')


@dataclass
class Plan:
    steps: list
    ratio: float
    pwm_limit: int
    anti_windup: bool
    calibration: list
    metadata: dict

    def validate(self):
        if not 1 <= len(self.steps) <= MAX_STEPS:
            raise ValueError('Schedule needs 1–12 steps')
        if not math.isfinite(self.ratio) or not 0 < self.ratio <= 20:
            raise ValueError('Heating/cooling ratio must be greater than 0 and at most 20')
        if isinstance(self.pwm_limit, bool) or int(self.pwm_limit) != self.pwm_limit or not 1 <= self.pwm_limit <= 255:
            raise ValueError('PWM limit must be an integer from 1 to 255')
        if not isinstance(self.anti_windup, bool):
            raise ValueError('anti_windup must be boolean')
        if self.calibration:
            validate_points(self.calibration)
        if sum(s.duration_s for s in self.steps) > 86400:
            raise ValueError('Total schedule duration cannot exceed 24 hours')
        for step in self.steps:
            step.validate()
            if step.mode in RAW_MODES and abs(step.Ua_pwm)+step.Ub_pwm > self.pwm_limit:
                raise ValueError('Raw PWM peak exceeds the PWM limit; choose a limit that preserves the requested waveform')
            if step.mode == 'OPEN':
                inverse_pwm(step.Ta_C-step.Tb_C, self.calibration)
                inverse_pwm(step.Ta_C+step.Tb_C, self.calibration)
        if not isinstance(self.metadata, dict):
            raise ValueError('Plan metadata must be an object')
        return self

    def document(self):
        self.validate()
        return {'schema': 'module_08_plan_v2', 'firmware': FIRMWARE_ID,
                'ratio': self.ratio, 'pwm_limit': self.pwm_limit, 'anti_windup': self.anti_windup,
                'calibration': [list(p) for p in self.calibration],
                'steps': [asdict(s) for s in self.steps], 'metadata': self.metadata}

    def digest(self):
        return hashlib.sha256(json.dumps(self.document(), sort_keys=True, allow_nan=False).encode()).hexdigest()

    def commands(self):
        self.validate()
        commands = ['STOP', 'CLEAR', f'CONFIG {self.ratio:.9g} {self.pwm_limit} {int(self.anti_windup)}']
        commands += [f'CAL {t:.9g} {u:.9g}' for t, u in self.calibration]
        for s in self.steps:
            command=f'STEP {s.duration_s:.9g} {s.Ta_C:.9g} {s.Tb_C:.9g} {s.period_s:.9g} {s.mode} {s.Kp:.9g} {s.Ki:.9g}'
            if s.mode in RAW_MODES:
                command+=f' {s.Ua_pwm:.9g} {s.Ub_pwm:.9g}'
            commands.append(command)
        commands.append(f'COMMIT {len(self.steps)} {len(self.calibration)}')
        if any(len(c.encode()) >= 143 for c in commands):
            raise ValueError('Command exceeds firmware buffer')
        return commands

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text())
        legacy=(data.get('schema'),data.get('firmware')) == ('module_08_plan_v1','module_08_angstrom_v1')
        current=(data.get('schema'),data.get('firmware')) == ('module_08_plan_v2',FIRMWARE_ID)
        if not (legacy or current):
            raise ValueError('Unsupported plan/firmware version')
        if legacy and any(s['mode'] not in TEMPERATURE_MODES for s in data['steps']):
            raise ValueError('Raw PWM modes require a v2 plan')
        return cls([Step(**s) for s in data['steps']], data['ratio'], data['pwm_limit'],
                   data['anti_windup'], [tuple(p) for p in data['calibration']], data['metadata']).validate()

    def save(self, path):
        Path(path).write_text(json.dumps(self.document(), indent=2, allow_nan=False)+'\n')


def preset(kind='comparison'):
    # Lower-amplitude planning defaults preserve the earlier 10–45 C range.
    # They are not measured gains or a guarantee of adequate settling.
    if kind in ('raw_zero', 'raw_positive'):
        zero=kind=='raw_zero'
        return Plan([Step(900,0,0,100,'RAW_ZERO' if zero else 'RAW_POS',0,0,0 if zero else 32,100 if zero else 5)],
            1.,100,False,[],{'purpose':kind,'ambient_C':None,'ambient_method':'not yet recorded',
            'settling_criterion':'Compare complete-cycle mean, amplitude and phase; select settled cycles from measured noise and repeatability.',
            'settings_status':'Planning diagnostic; preserve 10–45 C TEC protection and physical cutoff.',
            'drive_equation':'u = Ua_pwm + Ub_pwm*sin(phase_rad); no feedback, lookup or cooling multiplier',
            'duration_note':'Duration is a planning budget, not proof of settling. Keep the full raw record.',
            'positive_only_note':'Ua=32, Ub=5 is a measured-static-curve starting estimate near 40 C, not a guaranteed temperature.' if not zero else '',
            'start_note':'Begin zero-centered diagnostics near measured room temperature. Record room temperature independently.'}).validate()
    points, source = reference_calibration()
    if kind == 'rehearsal':
        steps = [Step(5, 35, 2, p, 'PI', 50, .3) for p in (100, 150, 240)]
    elif kind == 'single':
        steps = [Step(1800, 35, 5, 100, 'PI', 50, .3)]
    elif kind == 'comparison':
        steps = [Step(1800, 35, 5, 100, mode, 50, .3) for mode in TEMPERATURE_MODES]
        steps += [Step(1800, 35, 5, 150, 'PI', 50, .3)]
    else:
        raise ValueError('Unknown preset')
    return Plan(steps, source['heating_to_cooling_ratio'], 96, True, points,
        {'purpose': kind, 'calibration': source, 'ratio_source': 'Module 4 provisional measured ratio; revalidate',
         'ambient_C': None, 'ambient_method': 'not yet recorded',
         'settling_criterion': 'not yet specified; fixed duration does not certify settling',
         'settings_status': 'planning defaults; tune on the actual apparatus'}).validate()
