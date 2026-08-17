# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import unittest
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qcore import (
    Qty,
    find_unit,
    compose_qty,
    isMeasureQuantity,
    isMeasureUnit,
    is_str_named_uom,
    is_str_qty,
    is_str_uom,
    load_qty,
    read_unit,
    str_type,
)
from qcore.qc_mquantity import MeasureQuantity
from qcore.qc_qty import compose_qty2, str_to_named_uom, str_to_uom


GOLDEN_PATH = Path(__file__).resolve().parent / "golden_qty_snapshot.json"
UPDATE_GOLDEN = os.environ.get("QCALC_UPDATE_GOLDEN", "0") == "1"


def _round_float(x, digits=12):
    if x is None:
        return None
    if isinstance(x, float):
        y = round(x, digits)
        return 0.0 if y == -0.0 else y
    return x


def _serialize_qty_obj(q):
    return {
        "val": _round_float(q.val),
        "uom": q.uom,
    }


def _compute_golden_snapshot():
    qty_cases = [
        {"id": "simple_length", "input": "1 ft", "to_units": ["inch", "m"]},
        {"id": "simple_speed", "input": "12 ft/s", "to_units": ["yd/s", "inch/s", "m/s"]},
        {"id": "multipart_length", "input": "1ft, 6 inch", "to_units": ["ft", "inch", "m"]},
        {"id": "placeholder_none", "input": "None ft", "to_units": ["inch", "m"]},
        {"id": "placeholder_at", "input": "@ft", "to_units": ["inch", "m"]},
        {"id": "temp_f32", "input": "32 degF", "to_units": ["degC", "K"]},
        {"id": "temp_c100", "input": "100 degC", "to_units": ["degF", "K"]},
        {"id": "time_split", "input": "314159 s", "to_units": ["d", "h", "min", "s"]},
    ]

    read_unit_cases = [
        "kg*ft/s^2/m^3",
        "ft/s",
        "degf",
    ]

    out = {
        "schema": "qcalc-qty-golden-v1",
        "qty_cases": [],
        "read_unit_cases": [],
    }

    for case in qty_cases:
        raw = case["input"]
        kind, str_type_value, str_type_ln = str_type(raw)
        composed, compose_ln = compose_qty(raw)
        composed2, compose2_ln = compose_qty2(raw)

        entry = {
            "id": case["id"],
            "input": raw,
            "str_type": {
                "kind": kind,
                "value": str_type_value,
                "ln": str_type_ln,
            },
            "compose_qty": {
                "value": composed,
                "ln": compose_ln,
            },
            "compose_qty2": {
                "value": composed2,
                "ln": compose2_ln,
            },
            "to_units": {},
        }

        if kind == "qty":
            q = Qty(str_type_value)
            entry["qty"] = _serialize_qty_obj(q)
            for unit in case["to_units"]:
                entry["to_units"][unit] = _serialize_qty_obj(q.to(unit))
        else:
            entry["qty"] = None

        out["qty_cases"].append(entry)

    for sunit in read_unit_cases:
        info = read_unit(sunit)
        out["read_unit_cases"].append(
            {
                "input": sunit,
                "Read as": info["Read as"],
                "Write as": info["Write as"],
                "Category": info["Category"],
                "Dimension": info["Dimension"],
                "Quantity": info["Quantity"],
            }
        )

    return out


def _load_golden_snapshot():
    if not GOLDEN_PATH.exists():
        return None
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def _save_golden_snapshot(snapshot):
    GOLDEN_PATH.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class TestMeasureQuantityCompatibility(unittest.TestCase):
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

    def test_unit_conversion_and_mixed_units_output(self):
        q = MeasureQuantity("314159 s")
        out = q.in_units_of("d", "h", "min", "s")
        self.assertEqual(len(out), 4)
        self.assertTrue(all(isMeasureQuantity(x) for x in out))

        sec_sum = sum(x.to("s").value for x in out)
        self.assertAlmostEqual(sec_sum, q.value)

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


class TestQtyCompatibility(unittest.TestCase):
    def test_qty_constructor_variants(self):
        unit_yd = find_unit("yd")

        q_a = Qty(1, "yd")
        q_b = Qty(1, unit_yd)
        q_c = Qty("1 yd")
        q_d = Qty(1, "yd", "ft")
        q_e = Qty(1, unit_yd, "ft")
        q_f = Qty("1 yd", "ft")
        q_g = Qty(Qty("1 yd"))
        q_h = Qty(Qty("1 yd"), "ft")

        self.assertEqual(q_a.uom, "yd")
        self.assertEqual(q_b.uom, "yd")
        self.assertEqual(q_c.uom, "yd")

        self.assertAlmostEqual(q_d.val, 3.0)
        self.assertAlmostEqual(q_e.val, 3.0)
        self.assertAlmostEqual(q_f.val, 3.0)
        self.assertAlmostEqual(q_h.val, 3.0)

        self.assertAlmostEqual(q_g.val, 1.0)
        self.assertEqual(q_g.uom, "yd")

    def test_qty_type_preservation_and_conversion_helpers(self):
        speed = Qty("12 ft/s")

        # Qty inherits arithmetic from MeasureQuantity and should keep Qty type.
        total = Qty("1 m") + Qty("50 cm")
        self.assertIsInstance(total, Qty)
        self.assertAlmostEqual(total.val, 1.5)
        self.assertEqual(total.uom, "m")

        self.assertEqual((120 / speed).uom, "s/ft")
        self.assertAlmostEqual((120 / speed).val, 10.0)

        conv = speed.to("inch/s")
        self.assertIsInstance(conv, Qty)
        self.assertAlmostEqual(conv.val, 144.0)
        self.assertEqual(conv.uom, "inch/s")

        out = speed.to_units("yd/s, inch/s")
        self.assertEqual(len(out), 2)
        self.assertTrue(all(isinstance(x, Qty) for x in out))
        self.assertAlmostEqual(out[0].val, 4.0)
        self.assertAlmostEqual(out[1].val, 144.0)

        self.assertIsInstance(speed.si(), Qty)
        self.assertIsInstance(speed.mks(), Qty)
        self.assertIsInstance(speed.fps(), Qty)
        self.assertIsInstance(speed.cgs(), Qty)

    def test_qty_json_and_none_value_workflow(self):
        q = Qty("12.3456 ft").roundoff(2)
        self.assertAlmostEqual(q.val, 12.35)

        j = q.to_json()
        back = load_qty(j)
        self.assertIsInstance(back, Qty)
        self.assertEqual(back.uom, q.uom)
        self.assertAlmostEqual(back.val, q.val)

        q_none = Qty("@ft")
        self.assertIsNone(q_none.val)
        q_none.nzq()
        self.assertEqual(q_none.val, 0.0)

    def test_string_parsers_and_classifiers(self):
        self.assertTrue(isMeasureUnit(find_unit("ft")))
        self.assertTrue(is_str_uom("ft/s"))
        self.assertTrue(is_str_named_uom("ft"))
        self.assertFalse(is_str_named_uom("ft/s"))

        self.assertIsNotNone(str_to_uom("ft/s"))
        self.assertIsNotNone(str_to_named_uom("ft"))

        qty_str, ln = compose_qty("1ft, 6 inch")
        self.assertGreaterEqual(ln, 2)
        self.assertTrue(is_str_qty(qty_str))

        qty_str2, ln2 = compose_qty2("1ft, 6 inch")
        self.assertGreaterEqual(ln2, 2)
        self.assertTrue(is_str_qty(qty_str2))

        kind, _, ln3 = str_type("1ft, 6 inch")
        self.assertEqual(kind, "qty")
        self.assertGreaterEqual(ln3, 1)

        kind_u, _, _ = str_type("ft")
        self.assertEqual(kind_u, "uom")

        kind_t, _, _ = str_type("this is plain text")
        self.assertEqual(kind_t, "text")

    def test_read_unit_shape_and_content(self):
        result = read_unit("kg*ft/s^2/m^3")
        self.assertIn("Read as", result)
        self.assertIn("Write as", result)
        self.assertIn("Category", result)
        self.assertIn("Dimension", result)
        self.assertIn("Quantity", result)
        self.assertTrue(len(result["Dimension"]) > 0)


class TestQtyGoldenSnapshot(unittest.TestCase):
    def test_golden_snapshot(self):
        actual = _compute_golden_snapshot()

        if UPDATE_GOLDEN:
            _save_golden_snapshot(actual)
            self.skipTest(f"Golden snapshot updated: {GOLDEN_PATH}")

        expected = _load_golden_snapshot()
        if expected is None:
            self.fail(
                "Missing golden snapshot file. Run with QCALC_UPDATE_GOLDEN=1 to create it."
            )

        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
