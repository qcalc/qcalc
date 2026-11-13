# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qcore import Qty, UnitRegistry, load_qty
from qutil import to_python_expr


class TestHigherLevelCalculatorSmoke(unittest.TestCase):
    def test_public_qty_api_and_conversion(self):
        q = Qty("2 m")
        self.assertEqual(q.uom, "m")
        self.assertAlmostEqual(q.val, 2.0)

        converted = q.to("cm")
        self.assertIsInstance(converted, Qty)
        self.assertAlmostEqual(converted.val, 200.0)
        self.assertEqual(converted.uom, "cm")

        total = Qty("1 m") + Qty("50 cm")
        self.assertIsInstance(total, Qty)
        self.assertAlmostEqual(total.val, 1.5)
        self.assertEqual(total.uom, "m")

    def test_parsing_and_string_helpers(self):
        qty_str, ln = Qty.compose("1ft, 6 inch")
        self.assertGreaterEqual(ln, 2)
        self.assertTrue(Qty.is_valid(qty_str))
        self.assertTrue(UnitRegistry.is_uom("ft/s"))
        self.assertTrue(UnitRegistry.is_named("ft"))
        self.assertFalse(UnitRegistry.is_named("ft/s"))

        kind, _, ln2 = Qty.kind("1ft, 6 inch")
        self.assertEqual(kind, "qty")
        self.assertGreaterEqual(ln2, 1)

    def test_read_unit_and_json_round_trip(self):
        info = UnitRegistry.read("kg*ft/s^2/m^3")
        self.assertIn("Read as", info)
        self.assertIn("Write as", info)
        self.assertIn("Dimension", info)
        self.assertTrue(bool(info["Dimension"]))

        payload = Qty("12.3456 ft").roundoff(2).to_json()
        loaded = load_qty(payload)
        self.assertIsInstance(loaded, Qty)
        self.assertAlmostEqual(loaded.val, 12.35)
        self.assertEqual(loaded.uom, "ft")

    def test_unit_registry_and_expression_preprocessor(self):
        unit = UnitRegistry.find("deg")
        self.assertTrue(unit is not None)
        self.assertEqual(to_python_expr("m/s"), "m/s")
        self.assertEqual(to_python_expr("1*km"), "1*km")

    def test_failed_unit_lookup_does_not_mutate_registry(self):
        before = UnitRegistry.table.copy()

        with self.assertRaises(NameError):
            UnitRegistry.find("definitely_not_a_unit")

        self.assertEqual(UnitRegistry.table, before)


if __name__ == "__main__":
    unittest.main()
