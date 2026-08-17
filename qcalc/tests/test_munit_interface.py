# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qcore.qc_mbase import _base_names
from qcore.qc_munit import MeasureUnit, isMeasureUnit


class TestMeasureUnitInterface(unittest.TestCase):
    def _make_length_unit(self, name, factor):
        return MeasureUnit(name, factor, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def _make_time_unit(self, name, factor):
        return MeasureUnit(name, factor, [0, 0, 1, 0, 0, 0, 0, 0, 0, 0])

    def _make_mass_unit(self, name, factor):
        return MeasureUnit(name, factor, [0, 1, 0, 0, 0, 0, 0, 0, 0, 0])

    def test_init_and_name_reporting(self):
        unit = self._make_length_unit("m", 1.0)
        self.assertTrue(isMeasureUnit(unit))
        self.assertEqual(unit.name(), "m")
        self.assertEqual(unit.base_name, "m")
        self.assertEqual(unit.dimension, "L")
        self.assertEqual(unit.factor, 1.0)
        self.assertEqual(unit.powers[0], 1)
        self.assertEqual(unit.category, "Length, Wavelength")

    def test_composition_and_dimension_handling(self):
        meter = self._make_length_unit("m", 1.0)
        second = self._make_time_unit("s", 1.0)
        kilogram = self._make_mass_unit("kg", 1.0)

        velocity = meter / second
        self.assertEqual(velocity.name(), "m/s")
        self.assertEqual(velocity.powers[0], 1)
        self.assertEqual(velocity.powers[2], -1)
        self.assertFalse(velocity.is_dimensionless())

        force = meter * kilogram / (second ** 2)
        self.assertEqual(force.powers[0], 1)
        self.assertEqual(force.powers[1], 1)
        self.assertEqual(force.powers[2], -2)

        unitless = meter / meter
        self.assertTrue(unitless.is_dimensionless())
        self.assertEqual(unitless.name(), "1")

    def test_compatibility_and_conversion_factor(self):
        meter = self._make_length_unit("m", 1.0)
        centimeter = self._make_length_unit("cm", 0.01)
        second = self._make_time_unit("s", 1.0)

        self.assertTrue(meter.is_compatible(centimeter))
        self.assertFalse(meter.is_compatible(second))
        self.assertAlmostEqual(meter.conversion_factor_to(centimeter), 100.0)
        self.assertAlmostEqual(centimeter.conversion_factor_to(meter), 0.01)

    def test_conversion_tuple_and_offset_rules(self):
        meter = self._make_length_unit("m", 1.0)
        centimeter = self._make_length_unit("cm", 0.01)

        factor, offset = meter.conversion_tuple_to(centimeter)
        self.assertAlmostEqual(factor, 100.0)
        self.assertAlmostEqual(offset, 0.0)

        temp_kelvin = MeasureUnit("K", 1.0, [0, 0, 0, 0, 1, 0, 0, 0, 0, 0], offset=0.0)
        temp_celsius = MeasureUnit("degC", 1.0, [0, 0, 0, 0, 1, 0, 0, 0, 0, 0], offset=273.15)

        with self.assertRaises(TypeError):
            _ = temp_celsius * meter

        with self.assertRaises(TypeError):
            _ = temp_celsius / meter

    def test_inverse_and_fractional_exponents(self):
        meter = self._make_length_unit("m", 1.0)
        inverse_meter = meter ** -1
        self.assertEqual(inverse_meter.name(), "1/m")
        self.assertEqual(inverse_meter.powers[0], -1)

        fractional_power = meter ** 0.5
        self.assertEqual(fractional_power.powers[0], 0.5)
        self.assertEqual(fractional_power.factor, 1.0)

    def test_scalar_division_inverts_powers(self):
        mole = MeasureUnit("mol", 1.0, [0, 0, 0, 0, 0, 1, 0, 0, 0, 0])
        reciprocal_mole = 6.022e23 / mole

        self.assertEqual(reciprocal_mole.powers[5], -1)
        self.assertEqual((mole * reciprocal_mole).powers[5], 0)

    def test_base_name_helpers_are_available(self):
        unit = self._make_length_unit("m", 1.0)
        self.assertIn("m", _base_names)
        self.assertEqual(unit.base_name, "m")

    def test_mol_nav(self):
        unit1 = MeasureUnit("mol", 1.0, [0, 0, 0, 0, 0, 1, 0, 0, 0, 0])
        unit2 = MeasureUnit("nav", 6e23, [0, 0, 0, 0, 0, -1, 0, 0, 0, 0])
        x = unit1 * unit2
        self.assertEqual(x.powers, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0])


if __name__ == "__main__":
    unittest.main()
