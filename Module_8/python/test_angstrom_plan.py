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
        for kind in ('comparison','single','rehearsal'):
            p=preset(kind)
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'plan.json';p.save(path);self.assertEqual(Plan.load(path).digest(),p.digest())
            self.assertEqual(p.commands()[-1],f'COMMIT {len(p.steps)} {len(p.calibration)}')
        self.assertEqual(len(preset().steps),4)

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
