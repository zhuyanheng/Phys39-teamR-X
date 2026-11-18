"""Independent closed-form, convergence and export checks for S18.3 simulation."""
from dataclasses import replace
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).parent/'simulation'))
from periodic_model import Setup,Simulation,equal_chi_solution,MODULE,SOURCE


class PeriodicSimulationTests(unittest.TestCase):
    def run_case(self,s):
        run=Simulation(s);run.advance(run.step_count);return run

    def test_copied_module6_solver_unchanged(self):
        original=MODULE.parent/'Module_6/python/Lab_6_7_modeling_tec_v3.py'
        self.assertEqual(original.read_bytes(),SOURCE.read_bytes())

    def test_equal_susceptibility_startup_matches_complete_analytical_solution(self):
        s=Setup(chi_c_C_per_pwm=.46,period_s=300,duration_s=600)
        run=self.run_case(s);t,T,u=run.arrays();exact=equal_chi_solution(s,t)
        self.assertAlmostEqual(exact[0],s.initial_C)
        self.assertLess(np.max(abs(T-exact)),.01)
        fine=self.run_case(replace(s,dt_s=.025));tt,TT,_=fine.arrays()
        self.assertLess(np.max(abs(TT-equal_chi_solution(fine.setup,tt))),.55*np.max(abs(T-exact)))

    def test_asymmetric_fundamental_and_dc_against_fourier_prediction(self):
        s=Setup(period_s=200,duration_s=2000);run=self.run_case(s);m=run.metrics()
        w=2*math.pi/s.period_s
        expected_B=(s.chi_h_C_per_pwm+s.chi_c_C_per_pwm)/2*s.ub_pwm/math.hypot(1,w*s.thermal_time_constant_s)
        self.assertAlmostEqual(m['mean_minus_room_C'],(s.chi_h_C_per_pwm-s.chi_c_C_per_pwm)*s.ub_pwm/math.pi,delta=.003)
        self.assertAlmostEqual(m['fundamental_amplitude_C'],expected_B,delta=.005)
        self.assertAlmostEqual(m['phase_lag_deg'],math.degrees(math.atan(w*s.thermal_time_constant_s)),delta=.1)
        self.assertEqual(m['selected_saturated_samples'],0)

    def test_arbitrary_H_normalization_does_not_change_temperature(self):
        s=Setup(duration_s=20);a=self.run_case(s);b=self.run_case(replace(s,normalization_H_W_per_K=3.7))
        np.testing.assert_allclose(a.arrays(),b.arrays(),atol=1e-12)

    def test_rejects_clipped_or_invalid_setup(self):
        for s in (Setup(ub_pwm=300),Setup(period_s=50),Setup(dt_s=2),Setup(ambient_C=math.nan)):
            with self.assertRaises(ValueError):s.validate()

    def test_export_preserves_startup_and_labels_simulation(self):
        run=self.run_case(Setup(duration_s=500))
        with tempfile.TemporaryDirectory() as tmp:
            csv_path,meta,fig=run.export(Path(tmp)/'data',Path(tmp)/'figures')
            with csv_path.open() as stream:rows=list(csv.DictReader(stream))
            self.assertEqual(len(rows),run.step_count+1);self.assertEqual(float(rows[0]['time_s']),0.)
            info=json.loads(meta.read_text());self.assertEqual(info['kind'],'mathematical_simulation_not_measurement')
            self.assertEqual(info['csv_sha256'],hashlib.sha256(csv_path.read_bytes()).hexdigest())
            self.assertTrue(fig.exists());self.assertTrue(fig.with_suffix('.pdf').exists())


if __name__=='__main__':unittest.main()
