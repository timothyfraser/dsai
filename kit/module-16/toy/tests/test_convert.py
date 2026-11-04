# test_convert.py
# The tests for convert.py. The agent may read this file, never edit it.
# Course kit, module 16
#
# Run from the toy/ folder:  python3 -m unittest tests.test_convert

import unittest  # for the test runner, in the standard library

from convert import celsius_to_kelvin, kpa_to_psi, psi_to_kpa

class TestConvert(unittest.TestCase):

    def test_psi_to_kpa(self):
        # A car tyre at 32 psi is about 220.6 kPa.
        self.assertAlmostEqual(psi_to_kpa(32), 220.632, places=3)

    def test_kpa_to_psi(self):
        self.assertAlmostEqual(kpa_to_psi(220.632224), 32.0, places=3)

    def test_celsius_to_kelvin(self):
        self.assertAlmostEqual(celsius_to_kelvin(25), 298.15, places=2)

if __name__ == "__main__":
    unittest.main()
