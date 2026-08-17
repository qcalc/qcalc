# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qcore.qc_mquantity import MeasureQuantity
from qcore.qc_munit import MeasureUnit


class TestMeasureQuantityExamples(unittest.TestCase):
    def test_example_usage_flow(self):
        p = MeasureQuantity
        distance1 = p('10 m')
        distance2 = p('10 km')
        total = distance1 + distance2

        self.assertEqual(total.unit.name(), 'm')
        self.assertAlmostEqual(total.value, 10010.0)
        self.assertAlmostEqual(total.to('km').value, 10.01)
        self.assertEqual(total.to('km').unit.name(), 'km')
        self.assertAlmostEqual(total.value, 10010.0)
        self.assertEqual(total.unit.name(), 'm')

        base_total = total.in_base_units()
        self.assertEqual(base_total.unit.name(), 'm')
        self.assertAlmostEqual(base_total.value, 10010.0)

    def test_time_split_example(self):
        t = MeasureQuantity(314159.0, 's')
        parts = t.in_units_of('d', 'h', 'min', 's')
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0].unit.name(), 'd')
        self.assertEqual(parts[1].unit.name(), 'h')
        self.assertEqual(parts[2].unit.name(), 'min')
        self.assertEqual(parts[3].unit.name(), 's')

    def test_unit_name_uses_canonical_base_unit_order(self):
        unit = MeasureUnit({'m': 2, 'kg': 1, 's': -2, 'mol': -1}, 1.0, [2, 1, -2, 0, 0, -1, 0, 0, 0, 0])
        self.assertEqual(unit.name(), 'm^2*kg/s^2/mol')

    def test_in_base_units_uses_canonical_base_unit_order(self):
        qty = MeasureQuantity(1.0, MeasureUnit({'m': 2, 'kg': 1, 's': -2, 'mol': -1}, 1.0, [2, 1, -2, 0, 0, -1, 0, 0, 0, 0]))
        self.assertEqual(qty.in_base_units().unit.name(), 'm^2*kg/s^2/mol')

    def test_constant_and_temperature_examples(self):
        energy = MeasureQuantity('2.7 Hartree*Nav')
        converted = energy.to('kcal/mol')
        self.assertAlmostEqual(converted.value, 1694.2755804235, places=9)
        self.assertEqual(converted.unit.name(), 'kcal/mol')

        energy = MeasureQuantity('2.7 Hartree*Nav')
        e_bu = energy.in_base_units()
        self.assertEqual(str(e_bu), '7088849.028491924 m^2*kg/s^2/mol')

        base_energy = energy.in_base_units()
        self.assertIn('m', base_energy.unit.name())
        self.assertIn('kg', base_energy.unit.name())
        self.assertIn('s', base_energy.unit.name())

        freeze = MeasureQuantity('0 degC').to('degF')
        self.assertAlmostEqual(freeze.value, 32.0, places=0)
        self.assertEqual(freeze.unit.name(), 'degF')


if __name__ == "__main__":
    unittest.main()
