"""Synthetic physical/invalid-data checks; no serial and no measured outputs."""
import copy
import importlib.util
import math
from pathlib import Path
import unittest
import csv
import hashlib
import json
import tempfile
from unittest.mock import patch
import numpy as np
spec=importlib.util.spec_from_file_location('angstrom_fit',Path(__file__).parent/'analysis/angstrom_fit.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


class AngstromFitTests(unittest.TestCase):
    def setUp(self):
        self.x=[0,.0254,.0508,.0762,.1016]
        self.geometry={'x_m':self.x,'analysis_length_m':.2715,'diameter_m':.01277}
        self.period=100.;self.kappa=7e-5;self.nu=.003
        w=2*np.pi/self.period
        self.q=math.sqrt((math.hypot(self.nu,w)+self.nu)/(2*self.kappa))
        self.qp=math.sqrt((math.hypot(self.nu,w)-self.nu)/(2*self.kappa))
        rng=np.random.default_rng(7);self.rows=[]
        for t in np.arange(0,600,.5):
            row={'time_s':t,'period_s':100,'step':0,'run_id':1,'plan_sha256':'abc','control_mode':'PI','safety':'OK','run_state':'RUNNING'}
            row['tec_C']=35+5*np.cos(w*t)+rng.normal(0,.001)
            row['setpoint_C']=35+5*np.cos(w*t)
            for i,x in enumerate(self.x,1):
                z=a.finite_response(self.q,self.qp,.2715,x)
                row[f'rod{i}_C']=30+5*float(np.real(z*np.exp(1j*w*t)))+rng.normal(0,.001)
            self.rows.append(row)
        self.plan={'label':'synthetic','period_s':100,'start_s':0,'end_s':600,
            'settling':{'max_mean_change_C':.02,'max_amplitude_change_fraction':.02,'max_phase_change_rad':.02}}

    def test_recover_physical_transport_and_sign_convention(self):
        result=a.analyse_interval(self.rows,self.geometry,self.plan)
        self.assertEqual(result['status'],'candidate')
        self.assertAlmostEqual(result['spatial_fit']['q_per_m'],self.q,delta=.03)
        self.assertAlmostEqual(result['spatial_fit']['q_prime_per_m'],self.qp,delta=.03)
        self.assertAlmostEqual(result['transport']['kappa_m2_s'],self.kappa,delta=1e-7)
        self.assertAlmostEqual(result['transport']['nu_per_s'],self.nu,delta=1e-5)
        self.assertGreater(result['transport']['kappa_se_m2_s'],0)
        self.assertIsNone(result['transport']['k_W_mK'])
        self.assertTrue(result['cycle_stationarity_passed'])

    def test_settling_fails_for_slow_drift(self):
        for r in self.rows:
            for i in range(1,6):r[f'rod{i}_C']+=float(r['time_s'])*.001
        result=a.analyse_interval(self.rows,self.geometry,self.plan)
        self.assertFalse(result['cycle_stationarity_passed'])
        self.assertEqual(result['status'],'diagnostic_only')

    def test_refuse_too_few_cycles_and_missing_map(self):
        p=copy.deepcopy(self.plan);p['end_s']=499
        with self.assertRaisesRegex(ValueError,'five'):a.analyse_interval(self.rows,self.geometry,p)
        with self.assertRaisesRegex(ValueError,'Measure'):a.validate_map({'x_m':None})

    def test_refuse_frequency_change_and_recorded_period_mismatch(self):
        self.rows[-1]['step']=1
        with self.assertRaisesRegex(ValueError,'step'):a.analyse_interval(self.rows,self.geometry,self.plan)
        self.rows[-1]['step']=0;self.rows[-1]['period_s']=150
        with self.assertRaisesRegex(ValueError,'period'):a.analyse_interval(self.rows,self.geometry,self.plan)

    def test_refuse_clock_reset_missing_data_and_large_gap(self):
        rows=copy.deepcopy(self.rows);rows[50]['time_s']=rows[49]['time_s']
        with self.assertRaisesRegex(ValueError,'clock'):a.analyse_interval(rows,self.geometry,self.plan)
        rows=copy.deepcopy(self.rows);rows[50]['rod2_C']='nan'
        with self.assertRaisesRegex(ValueError,'Missing'):a.analyse_interval(rows,self.geometry,self.plan)
        rows=self.rows[:100]+self.rows[130:]
        with self.assertRaisesRegex(ValueError,'gap'):a.analyse_interval(rows,self.geometry,self.plan)

    def test_require_three_sensors_and_reject_missing_t1(self):
        p=copy.deepcopy(self.plan);p['rod_sensors']=[2,3,4]
        with self.assertRaises(ValueError):a.analyse_interval(self.rows,self.geometry,p)
        p['rod_sensors']=[1,2]
        with self.assertRaises(ValueError):a.analyse_interval(self.rows,self.geometry,p)

    def test_material_conversion_preserves_provenance(self):
        p=copy.deepcopy(self.plan);p['material']={'density_kg_m3':2700,'specific_heat_J_kgK':900,'source':'synthetic test constants; not measured'}
        r=a.analyse_interval(self.rows,self.geometry,p)
        self.assertAlmostEqual(r['transport']['k_W_mK'],170.1,delta=.3)
        self.assertAlmostEqual(r['transport']['h_W_m2K'],.003*2700*900*.01277/4,delta=.02)

    def test_negative_loss_is_preserved_and_finite_end_error_is_tested(self):
        r=a.infer(18,25,100)
        self.assertLess(r['nu_per_s'],0);self.assertFalse(r['physical_positive_loss'])
        self.assertAlmostEqual(a.finite_error(25,18,.2715,0),0)
        self.assertLess(a.finite_error(25,18,.2715,.05),.001)
        self.assertGreater(a.finite_error(25,18,.2715,.27),.1)

    def test_phase_wrap_does_not_reverse_lag(self):
        fits=[{'amplitude_C':5*np.exp(-2*x),'phase_rad':float(np.angle(np.exp(1j*(3-8*x))))} for x in [0,.1,.2,.3]]
        r=a.spatial([0,.1,.2,.3],fits)
        self.assertAlmostEqual(r['q_prime_per_m'],8)
        self.assertAlmostEqual(r['q_per_m'],2)

    def test_finite_periodic_fit_recovers_tip_sensitive_response(self):
        xs=[0,.0385,.0895,.1405,.1915];q,qp=12.,10.
        response=a.finite_response(q,qp,.2715,xs)
        fits=[{'amplitude_C':float(abs(z)*5),'phase_rad':float(np.angle(z))} for z in response]
        result=a.fit_finite_periodic(xs,fits,.2715,(10,8))
        self.assertAlmostEqual(result['q_per_m'],q,places=5)
        self.assertAlmostEqual(result['q_prime_per_m'],qp,places=5)
        self.assertGreater(a.finite_error(q,qp,.2715,.1915),.05)

    def test_supplied_geometry_and_material_uncertainties_propagate(self):
        geometry=copy.deepcopy(self.geometry)
        geometry.update(position_uncertainty_m=[0,.0002,.0002,.0002,.0002],analysis_length_standard_uncertainty_m=.0005,diameter_standard_uncertainty_m=.00001)
        plan=copy.deepcopy(self.plan)
        plan.update(period_standard_uncertainty_s=.01,material={'density_kg_m3':2700,'specific_heat_J_kgK':900,'source':'synthetic constants','density_standard_uncertainty_kg_m3':10,'specific_heat_standard_uncertainty_J_kgK':10})
        r=a.analyse_interval(self.rows,geometry,plan);budget=r['uncertainty_budget']
        self.assertTrue(budget['complete_supplied_input_budget'])
        self.assertGreater(budget['kappa_known_components_se_m2_s'],r['transport']['kappa_se_m2_s'])
        self.assertGreater(budget['k_known_components_se_W_mK'],r['transport']['k_fit_se_W_mK'])

    def test_plan_outputs_strict_json_without_changing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);raw=root/'run.csv';mapping=root/'map.json';plan=root/'plan.json'
            rows=[dict(r,event='measurement',seq=i,phase_rad=2*np.pi*float(r['time_s'])/100) for i,r in enumerate(self.rows)]
            with raw.open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            before=raw.read_bytes();mapping.write_text(json.dumps(self.geometry))
            plan.write_text(json.dumps({'raw':'run.csv','sensor_map':'map.json','intervals':[self.plan]}))
            with patch.object(a,'ROOT',root),patch.object(a,'MODULE',root/'Module_8'):
                target,result=a.analyse_plan(plan)
            self.assertEqual(before,raw.read_bytes())
            self.assertFalse(result['production_record_complete'])
            self.assertTrue(result['raw_unchanged'])
            self.assertEqual(result['source_sha256'],hashlib.sha256(before).hexdigest())
            self.assertNotIn('NaN',target.read_text())

    def test_plan_rejects_constant_setpoint_module7_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'run.csv').write_text('event,time_s,tec_C\nmeasurement,0,30\n')
            plan=root/'plan.json';plan.write_text(json.dumps({'raw':'run.csv'}))
            with patch.object(a,'ROOT',root):
                with self.assertRaisesRegex(ValueError,'Module 7'):a.analyse_plan(plan)

if __name__=='__main__':unittest.main(verbosity=2)
