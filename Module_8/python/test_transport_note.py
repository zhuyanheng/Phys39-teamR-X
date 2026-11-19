"""Synthetic checks for the offline transport conversion; no hardware, no measured output."""
import importlib.util
import math
from pathlib import Path
import unittest

import numpy as np

spec = importlib.util.spec_from_file_location(
    "transport_note", Path(__file__).parent / "analysis/transport_note.py")
tn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tn)


def forward(kappa, nu, period):
    """Invert the inversion: build q, q' from kappa, nu, omega."""
    w = 2 * math.pi / period
    a = nu / kappa
    b = w / (2 * kappa)
    s = math.hypot(a, 2 * b)
    return math.sqrt((s + a) / 2), math.sqrt((s - a) / 2)


class TransportNoteTests(unittest.TestCase):
    def test_cycle_transport_round_trip(self):
        kappa, nu, period = 6.8e-5, 1.5e-3, 400
        q, qp = forward(kappa, nu, period)
        k2, n2, m2 = tn.cycle_transport(q, qp, period)
        self.assertAlmostEqual(k2, kappa, delta=1e-12)
        self.assertAlmostEqual(n2, nu, delta=1e-15)
        self.assertGreater(m2, 0)

    def test_negative_loss_is_reported_as_none(self):
        # q' > q cannot describe a passive lateral loss.
        kappa, nu, m2 = tn.cycle_transport(1.0, 1.2, 100)
        self.assertIsNone(nu)
        self.assertLess(m2, 0)

    def test_material_conversion(self):
        k, h = tn.material_conversion(6.8e-5, 1.5e-3)
        rho = tn.MATERIAL["density_kg_m3"]
        c = tn.MATERIAL["specific_heat_J_kgK"]
        self.assertAlmostEqual(k, rho * c * 6.8e-5, places=9)
        self.assertAlmostEqual(h, 1.5e-3 * rho * c * tn.DIAMETER_M / 4, places=9)

    def test_cosh_fit_recovers_known_parameters(self):
        x = np.array([0.0, 0.0385, 0.0895, 0.1405, 0.1915])
        length, mu, a0, tinf = 0.2715, 1.60, 32.0, 25.0
        xi = x / length
        means = tinf + (a0 - tinf) * np.cosh(mu * (1 - xi)) / math.cosh(mu)
        fit = tn.cosh_fit(x, means, length)
        self.assertAlmostEqual(fit["mu_mL"], mu, delta=0.01)
        self.assertAlmostEqual(fit["ambient_C_fitted"], tinf, delta=0.1)
        self.assertLess(fit["rms_residual_C"], 1e-6)
        self.assertAlmostEqual(fit["m_per_m"], mu / length, places=9)

    def test_harmonic_recovers_known_sinusoid(self):
        period, amp, phase = 100.0, 0.8, -0.7
        t = np.arange(0, 5 * period, 0.5)
        y = 30 + amp * np.cos(2 * math.pi * t / period + phase)
        fit = tn.harmonic(t, y, period)
        self.assertAlmostEqual(fit["amplitude"], amp, places=9)
        self.assertAlmostEqual(fit["phase_rad"], phase, places=9)
        self.assertLess(fit["rms_residual"], 1e-9)


if __name__ == "__main__":
    unittest.main()
