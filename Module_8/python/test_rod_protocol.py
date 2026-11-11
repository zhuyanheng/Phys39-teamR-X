import math
import unittest
from angstrom_plan import preset
from native_test_support import firmware
from rod_protocol import FIELD_NAMES,V1_FIELD_NAMES,build_data_line,parse_data_line,parse_lines

class ProtocolTests(unittest.TestCase):
    def test_actual_firmware_header_matches_parser(self):
        header=next(x for x in firmware([]) if x.startswith('#DATA,'))
        self.assertEqual(header,'#DATA,'+','.join(FIELD_NAMES))
        self.assertEqual(len(FIELD_NAMES),len(set(FIELD_NAMES)))

    def test_round_trip_and_all_channels(self):
        sample=parse_data_line(build_data_line(rod2_C=26.2))
        self.assertEqual(sample.rods_c,(25.,26.2,25.,25.,25.))
        self.assertEqual(len(sample.measurement),len(FIELD_NAMES))

    def test_saved_v1_temperature_records_remain_readable(self):
        line=','.join(build_data_line().split(',')[:len(V1_FIELD_NAMES)+1])
        sample=parse_data_line(line);self.assertIsNotNone(sample)
        self.assertTrue(math.isnan(sample.values['Ua_pwm']))

    def test_raw_record_uses_pwm_parameters_and_no_temperature_target(self):
        raw=dict(run_state='RUNNING',control_mode='RAW_ZERO',step=0,period_s=100,
            Ua_pwm=0,Ub_pwm=100,pwm_limit=100,controller_pwm=-100,compensated_pwm=-100,
            pwm=100,signed_pwm=-100,cool_pwm=100,phase_rad=3*math.pi/2)
        self.assertIsNotNone(parse_data_line(build_data_line(**raw)))
        for changes in ({'setpoint_C':35},{'compensated_pwm':-200},{'Ub_pwm':101},
                {'control_mode':'RAW_POS'},{'integration_blocked':1},{'saturated':1}):
            self.assertIsNone(parse_data_line(build_data_line(**{**raw,**changes})))
        truncated=','.join(build_data_line(**raw).split(',')[:len(V1_FIELD_NAMES)+1])
        self.assertIsNone(parse_data_line(truncated))

    def test_rejects_legacy_truncated_and_noninteger_records(self):
        for line in ('DATA,1,25,25,25,25,25,25,0,0,0,0,60,OK,5',
                     build_data_line(seq=1.5),build_data_line(pwm=float('inf')),
                     build_data_line().rsplit(',',1)[0]):
            self.assertIsNone(parse_data_line(line))

    def test_bad_bridge_or_counts_rejected(self):
        for values in ({'signed_pwm':10},{'heat_pwm':10,'cool_pwm':10},
                       {'heat_cool':1},{'rod_ok':4},{'pwm_limit':256}):
            self.assertIsNone(parse_data_line(build_data_line(**values)))

    def test_nan_downstream_is_recorded_but_t1_is_required_for_start(self):
        downstream=parse_data_line(build_data_line(rod5_C=math.nan,rod_ok=4))
        self.assertIsNotNone(downstream);self.assertIsNone(downstream.issue())
        boundary=parse_data_line(build_data_line(rod1_C=math.nan,rod_ok=4))
        self.assertIn('T1',boundary.issue())

    def test_running_requires_parameters_and_off_records_require_zero(self):
        self.assertIsNone(parse_data_line(build_data_line(run_state='RUNNING')))
        self.assertIsNone(parse_data_line(build_data_line(run_state='DONE',signed_pwm=10,pwm=10,heat_pwm=10,heat_cool=1)))
        self.assertIsNone(parse_data_line(build_data_line(safety='ERROR')))

    def test_parse_lines_skips_diagnostics(self):
        samples=parse_lines('#ACK,HELLO\n'+build_data_line()+'\ngarbage\n')
        self.assertEqual(len(samples),1)

    def test_firmware_feedback_record_has_raw_and_compensated_pwm(self):
        p=preset('single')
        lines=firmware(p.commands()+['PING','START','@T 1500 40 30'])
        sample=parse_data_line(next(s for s in lines if s.startswith('DATA,')))
        self.assertIsNotNone(sample)
        self.assertLess(sample.values['controller_pwm'],0)
        self.assertAlmostEqual(sample.values['compensated_pwm'],sample.values['controller_pwm']*p.ratio,places=2)
        self.assertEqual(sample.signed_pwm,-p.pwm_limit)
        self.assertEqual(sample.values['integration_blocked'],1)

if __name__=='__main__':unittest.main()
