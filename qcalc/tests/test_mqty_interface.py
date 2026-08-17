# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qcore.qc_mquantity import MeasureQuantity, isMeasureQuantity


class TestMeasureQuantityInterface(unittest.TestCase):
    def test_constructor_and_placeholders(self):
        q = MeasureQuantity("1.5 m")
        self.assertTrue(isMeasureQuantity(q))
        self.assertAlmostEqual(q.value, 1.5)
        self.assertEqual(q.unit.name(), "m")

        q_none = MeasureQuantity("None ft")
        self.assertIsNone(q_none.value)
        self.assertEqual(q_none.unit.name(), "ft")

        q_at = MeasureQuantity("@ft")
        self.assertIsNone(q_at.value)
        self.assertEqual(q_at.unit.name(), "ft")

    def test_arithmetic_and_comparison(self):
        q1 = MeasureQuantity("1 m")
        q2 = MeasureQuantity("100 cm")
        q3 = MeasureQuantity("2 m")

        self.assertTrue(q1 == q2)
        self.assertTrue(q1 <= q2)
        self.assertTrue(q3 > q1)

        s = q1 + q2
        self.assertAlmostEqual(s.value, 2.0)
        self.assertEqual(s.unit.name(), "m")

        d = q3 - q1
        self.assertAlmostEqual(d.value, 1.0)
        self.assertEqual(d.unit.name(), "m")

    def test_unit_conversion_and_split_output(self):
        q = MeasureQuantity("314159 s")
        out = q.in_units_of("d", "h", "min", "s")
        self.assertEqual(len(out), 4)
        self.assertTrue(all(isMeasureQuantity(x) for x in out))

        km = MeasureQuantity("1000 m").to("km")
        self.assertAlmostEqual(km.value, 1.0)
        self.assertEqual(km.unit.name(), "km")

    def test_errors_for_incompatible_operations(self):
        with self.assertRaises(TypeError):
            _ = MeasureQuantity("1 m") + MeasureQuantity("1 s")

        with self.assertRaises(TypeError):
            _ = MeasureQuantity("1 m").to("s")

        with self.assertRaises(TypeError):
            _ = pow(MeasureQuantity("2 m"), MeasureQuantity("2 m"))

    def test_trig_requires_angle(self):
        angle = MeasureQuantity("180 deg")
        self.assertAlmostEqual(angle.sin(), 0.0, places=12)

        with self.assertRaises(TypeError):
            _ = MeasureQuantity("1 m").sin()


if __name__ == "__main__":
    unittest.main()
