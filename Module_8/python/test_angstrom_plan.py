import dataclasses
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from angstrom_plan import Plan,Step,preset,inverse_pwm,reference_calibration
from native_test_support import executable,firmware
from rod_protocol import parse_data_line

class PlanTests(unittest.TestCase):
    def test_presets_and_round_trip(self):
        for kind in ('comparison','single','rehearsal','raw_zero','raw_positive'):
            p=preset(kind)
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'plan.json';p.save(path);self.assertEqual(Plan.load(path).digest(),p.digest())
            self.assertEqual(p.commands()[-1],f'COMMIT {len(p.steps)} {len(p.calibration)}')
        self.assertEqual(len(preset().steps),4)

    def test_v1_temperature_configuration_remains_loadable(self):
        p=Plan.load(Path(__file__).resolve().parents[1]/'config/control_open_35C_5C_200s.json')
        self.assertEqual(p.steps[0].mode,'OPEN');self.assertEqual(p.steps[0].Ua_pwm,0)
        self.assertEqual(p.document()['firmware'],'module_08_angstrom_v2')

    def test_raw_requires_correct_polarity_and_unclipped_peak(self):
        for kind,changes in (('raw_zero',{'Ua_pwm':1}),('raw_positive',{'Ua_pwm':5}),
                ('raw_zero',{'Ub_pwm':0}),('raw_zero',{'Ub_pwm':256}),
                ('raw_zero',{'Ub_pwm':float('nan')}),('raw_zero',{'Ta_C':35}),
                ('raw_zero',{'Kp':50}),('raw_zero',{'period_s':99})):
            p=preset(kind);p.steps[0]=dataclasses.replace(p.steps[0],**changes)
            with self.assertRaises(ValueError):p.validate()
        p=preset('raw_zero');p.pwm_limit=96
        with self.assertRaisesRegex(ValueError,'peak'):p.validate()

    def test_raw_firmware_preserves_uncompensated_negative_command(self):
        p=preset('raw_zero');p.ratio=4
        commands=p.commands()+['PING','START']
        for t in range(1500,76501,500):commands.append(f'@T {t} 30 28')
        lines=firmware(commands)
        samples=[parse_data_line(s) for s in lines if s.startswith('DATA,')]
        self.assertTrue(samples);self.assertTrue(all(s is not None for s in samples))
        self.assertEqual(max(s.signed_pwm for s in samples),100)
        self.assertEqual(min(s.signed_pwm for s in samples),-100)
        negative=next(s for s in samples if s.signed_pwm==-100)
        self.assertAlmostEqual(negative.values['controller_pwm'],negative.values['compensated_pwm'])
        self.assertEqual(negative.values['Ua_pwm'],0);self.assertEqual(negative.values['Ub_pwm'],100)

    def test_raw_positive_firmware_never_cools_and_stop_zeroes(self):
        p=preset('raw_positive');commands=p.commands()+['PING','START']
        for t in range(1500,101001,500):commands.append(f'@T {t} 25 25')
        commands+=['STOP','@T 101500 25 25']
        lines=firmware(commands);samples=[parse_data_line(s) for s in lines if s.startswith('DATA,')]
        self.assertTrue(all(s is not None for s in samples))
        self.assertEqual(min(s.signed_pwm for s in samples[:-1]),27)
        self.assertEqual(max(s.signed_pwm for s in samples[:-1]),37)
        self.assertEqual(samples[-1].signed_pwm,0)

    def test_firmware_rejects_raw_clipping_missing_args_and_bad_polarity(self):
        for cap,step in ((96,'STEP 900 0 0 100 RAW_ZERO 0 0 0 100'),
                (100,'STEP 900 0 0 100 RAW_POS 0 0 5 5'),
                (100,'STEP 900 0 0 100 RAW_ZERO 0 0')):
            lines=firmware(['CLEAR',f'CONFIG 4 {cap} 0',step,'COMMIT 1 0','PING','START','@T 1500 25 25'])
            self.assertIn('#ERR,INVALID_PLAN',lines);self.assertIn('#ERR,START_REJECTED',lines)
            s=parse_data_line(next(x for x in lines if x.startswith('DATA,')))
            self.assertIsNotNone(s);self.assertEqual(s.signed_pwm,0)

    def test_reject_short_period_and_out_of_range_waveform(self):
        for replacement in ({'period_s':99},{'Ta_C':40,'Tb_C':16},{'duration_s':0},{'Tb_C':-1},{'Kp':float('nan')},{'mode':'PID'}):
            p=preset('single');p.steps[0]=dataclasses.replace(p.steps[0],**replacement)
            with self.assertRaises(ValueError):p.validate()

    def test_invalid_configuration(self):
        for key,value in (('ratio',0),('ratio',float('nan')),('pwm_limit',256),('pwm_limit',1.5),('anti_windup','yes')):
            p=preset();setattr(p,key,value)
            with self.assertRaises((ValueError,OverflowError)):p.validate()

    def test_no_extrapolation_or_nonmonotonic_calibration(self):
        points,_=reference_calibration()
        for t in (0,50,float('nan')):
            with self.assertRaises(ValueError):inverse_pwm(t,points)
        self.assertAlmostEqual(inverse_pwm(34.62,points),23)
        p=preset();p.calibration=[(20,5),(40,-5)]
        with self.assertRaises(ValueError):p.validate()

    def test_measured_ratio_is_derived_from_both_signed_pwm_branches(self):
        _, source=reference_calibration()
        self.assertAlmostEqual(source['chi_heat_C_per_pwm'],.4954462888)
        self.assertAlmostEqual(source['chi_cool_C_per_pwm'],.1414166667)
        self.assertAlmostEqual(preset().ratio,source['chi_heat_C_per_pwm']/source['chi_cool_C_per_pwm'])

    def test_open_loop_requires_lookup_but_feedback_can_run_without(self):
        p=preset();p.calibration=[]
        with self.assertRaises(ValueError):p.validate()
        p=preset('single');p.calibration=[];p.validate()

    def test_total_duration_and_count(self):
        p=preset();p.steps=[p.steps[0]]*13
        with self.assertRaises(ValueError):p.validate()
        p=preset();p.steps=[dataclasses.replace(p.steps[0],duration_s=86400)]*2
        with self.assertRaises(ValueError):p.validate()

    def test_actual_native_control_core(self):
        result=subprocess.run([str(executable('core_checks'))],check=True,capture_output=True,text=True)
        self.assertIn('passed',result.stdout)

    def test_firmware_accepts_python_plan_and_emits_parseable_run(self):
        lines=firmware(preset().commands()+['PING','START','@T 1500 25 25'])
        self.assertIn('#ACK,COMMIT',lines);self.assertIn('#ACK,START',lines)
        samples=[parse_data_line(s) for s in lines if s.startswith('DATA,')]
        self.assertEqual(len(samples),1);self.assertIsNotNone(samples[0])
        self.assertEqual(samples[0].values['control_mode'],'OPEN')
        self.assertEqual(samples[0].values['run_state'],'RUNNING')

    def test_firmware_independently_rejects_unsafe_waveform(self):
        lines=firmware(['CLEAR','CONFIG 3.5 96 1','STEP 1000 40 16 100 PI 50 .3','COMMIT 1 0','PING','START','@T 1500 25 25'])
        self.assertIn('#ERR,INVALID_PLAN',lines);self.assertIn('#ERR,START_REJECTED',lines)
        sample=parse_data_line(next(x for x in lines if x.startswith('DATA,')))
        self.assertEqual(sample.signed_pwm,0)

    def test_firmware_link_timeout_and_overflow_zero_both_directions(self):
        for tail in (['@T 1500 25 25 2001'],['@OVERFLOW']):
            lines=firmware(preset().commands()+['PING','START']+tail)
            sample=parse_data_line(next(x for x in lines if x.startswith('DATA,')))
            self.assertEqual(sample.values['run_state'],'FAULT');self.assertEqual(sample.signed_pwm,0)

    def test_rehearsal_has_two_transitions_and_finishes_off(self):
        commands=preset('rehearsal').commands()+['PING','START']
        for t in range(1500,16500,500):commands+=['PING',f'@SCAN {t}']
        lines=firmware(commands)
        transitions=[x for x in lines if x.startswith('#EVENT,STEP,')]
        self.assertEqual(len(transitions),3) # Initial step plus two frequency changes.
        self.assertTrue(any(x.startswith('#EVENT,DONE,') for x in lines))
        final=parse_data_line([x for x in lines if x.startswith('DATA,')][-1])
        self.assertEqual(final.values['run_state'],'DONE');self.assertEqual(final.signed_pwm,0)

if __name__=='__main__':unittest.main()
