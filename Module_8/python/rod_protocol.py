"""Fixed Module 8 v1 serial record. Inactive numeric fields use nan.

A legacy Module 7 DATA line is rejected; it cannot enable the new controller.
The exact incoming bytes, including errors/events, are separately saved by the GUI.
"""
import math
from dataclasses import dataclass

CHANNELS = ('tec', 'rod1', 'rod2', 'rod3', 'rod4', 'rod5')
ROD_CHANNELS = CHANNELS[1:]
CHANNEL_FIELDS = ('time_s', 'tec_C') + tuple(f'{c}_C' for c in ROD_CHANNELS)
DATA_PREFIX, DIAGNOSTIC_PREFIX = 'DATA,', '#'
FIELD_NAMES = CHANNEL_FIELDS + (
    'pwm','heat_cool','heat_pwm','cool_pwm','limit_C','safety','rod_ok',
    'run_state','control_mode','step','Ta_C','Tb_C','period_s','setpoint_C',
    'feedforward_pwm','controller_pwm','heating_to_cooling_ratio','signed_pwm','phase_rad',
    'Kp_pwm_per_C','Ki_pwm_per_C_s','pwm_limit','anti_windup','error_C',
    'integral_error_C_s','compensated_pwm','saturated','integration_blocked',
    'rod_base_limit_C','operating_max_C','heartbeat_age_ms','fault_code','time_ms','seq')
TEXT_FIELDS = {'safety','run_state','control_mode','fault_code'}
INT_FIELDS = {'pwm','heat_cool','heat_pwm','cool_pwm','rod_ok','step','signed_pwm',
              'pwm_limit','anti_windup','saturated','integration_blocked','heartbeat_age_ms','time_ms','seq'}

@dataclass(frozen=True)
class RodSample:
    values: dict

    @property
    def time_s(self): return self.values['time_s']
    @property
    def tec_c(self): return self.values['tec_C']
    @property
    def rods_c(self): return tuple(self.values[f'{c}_C'] for c in ROD_CHANNELS)
    @property
    def signed_pwm(self): return self.values['signed_pwm']
    @property
    def rod_ok(self): return self.values['rod_ok']
    @property
    def pwm(self): return self.values['pwm']
    @property
    def safety(self): return self.values['safety']
    @property
    def measurement(self): return tuple(self.values[k] for k in FIELD_NAMES)

    def issue(self):
        v=self.values
        if v['safety']!='OK' or v['run_state']=='FAULT': return v['fault_code']
        if not math.isfinite(self.tec_c) or not 10<=self.tec_c<=45: return 'TEC outside 10–45 C'
        if not math.isfinite(self.rods_c[0]) or self.rods_c[0]>=56: return 'Invalid/over-limit T1 boundary'
        return None


def parse_data_line(line):
    cells=line.strip().split(',')
    if len(cells)!=len(FIELD_NAMES)+1 or cells[0]!='DATA': return None
    try:
        values={}
        for name,text in zip(FIELD_NAMES,cells[1:]):
            if name in TEXT_FIELDS:
                values[name]=text
            else:
                x=float(text)
                if name in INT_FIELDS:
                    if not math.isfinite(x) or x!=int(x): return None
                    x=int(x)
                values[name]=x
        v=values
        if not math.isfinite(v['time_s']) or v['time_s']<0: return None
        if not 0<=v['pwm']<=255 or not -255<=v['signed_pwm']<=255: return None
        if v['heat_cool'] not in (0,1) or not 0<=v['rod_ok']<=5: return None
        if any(v[k] not in (0,1) for k in ('anti_windup','saturated','integration_blocked')): return None
        if v['safety'] not in ('OK','SHUTDOWN') or v['run_state'] not in ('IDLE','RUNNING','DONE','FAULT'): return None
        if v['control_mode'] not in ('OFF','OPEN','P','PI') or not -1<=v['step']<12: return None
        if not 1<=v['pwm_limit']<=255 or min(v['heartbeat_age_ms'],v['time_ms'],v['seq'])<0: return None
        if v['heat_pwm']!=max(v['signed_pwm'],0) or v['cool_pwm']!=max(-v['signed_pwm'],0): return None
        if v['pwm']!=abs(v['signed_pwm']) or v['heat_cool']!=int(v['signed_pwm']>0): return None
        if v['rod_ok']!=sum(math.isfinite(v[f'{c}_C']) for c in ROD_CHANNELS): return None
        if v['run_state']!='RUNNING' and v['signed_pwm']!=0: return None
        if v['run_state']=='RUNNING':
            required=('Ta_C','Tb_C','period_s','setpoint_C','phase_rad','heating_to_cooling_ratio',
                      'Kp_pwm_per_C','Ki_pwm_per_C_s','error_C','integral_error_C_s','compensated_pwm')
            if not all(math.isfinite(v[k]) for k in required): return None
            if v['step']<0 or v['control_mode']=='OFF' or v['period_s']<100: return None
            if not 10<=v['Ta_C']-v['Tb_C']<=v['Ta_C']+v['Tb_C']<=45: return None
            if v['Tb_C']<0 or not 10<=v['setpoint_C']<=45 or not 0<v['heating_to_cooling_ratio']<=20: return None
            if abs(v['signed_pwm'])>v['pwm_limit']: return None
            source='feedforward_pwm' if v['control_mode']=='OPEN' else 'controller_pwm'
            if not math.isfinite(v[source]): return None
        return RodSample(values)
    except (ValueError,TypeError,OverflowError):
        return None


def parse_lines(text):
    return [s for line in text.splitlines() if (s:=parse_data_line(line)) is not None]


def build_data_line(**overrides):
    """Hardware-free fixture, not experimental data."""
    values={k:math.nan for k in FIELD_NAMES}
    values.update(time_s=1.,tec_C=25.,rod1_C=25.,rod2_C=25.,rod3_C=25.,rod4_C=25.,rod5_C=25.,
        pwm=0,heat_cool=0,heat_pwm=0,cool_pwm=0,limit_C=60.,safety='OK',rod_ok=5,
        run_state='IDLE',control_mode='OFF',step=-1,heating_to_cooling_ratio=3.5035,
        signed_pwm=0,phase_rad=0,pwm_limit=96,anti_windup=1,integral_error_C_s=0,
        compensated_pwm=0,saturated=0,integration_blocked=0,rod_base_limit_C=56.,
        operating_max_C=45.,heartbeat_age_ms=0,fault_code='NONE',time_ms=1000,seq=0)
    values.update(overrides)
    return 'DATA,'+','.join(str(values[k]) for k in FIELD_NAMES)
