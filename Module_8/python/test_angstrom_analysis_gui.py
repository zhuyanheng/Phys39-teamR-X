"""Offline viewer smoke test using only synthetic temporary data."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import angstrom_analysis_gui as view
import test_angstrom_fit as fixtures

class AnalysisGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=view.QApplication.instance() or view.QApplication([])
    def test_viewer_opens_without_hardware_or_outputs(self):
        import serial
        from serial.tools import list_ports
        with patch.object(serial,'Serial',side_effect=AssertionError('Hardware forbidden')),patch.object(list_ports,'comports',side_effect=AssertionError('Discovery forbidden')):
            w=view.AnalysisWindow()
            try:
                self.assertIsNone(w.result)
                self.assertIn('template',w.summary.toPlainText())
                w.show();self.app.processEvents()
            finally:w.close()
    def test_synthetic_result_loads_spatial_curves(self):
        case=fixtures.AngstromFitTests();case.setUp()
        result=view.fit.analyse_interval(case.rows,case.geometry,case.plan)
        w=view.AnalysisWindow()
        try:
            w.load_result({'kind':'measured_periodic_analysis','source':'/private/tmp/no_measured_source.csv','intervals':[result]})
            self.assertEqual(w.selector.count(),1)
            self.assertIn('kappa',w.summary.toPlainText())
            self.assertEqual(len(w.amplitude.listDataItems()),2)
        finally:w.close()

if __name__=='__main__':unittest.main()
