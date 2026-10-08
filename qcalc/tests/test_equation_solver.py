# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import math
import sys
import unittest
import importlib.util
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qcore import Qty


_SOLVER_PATH = Path(__file__).resolve().parents[1] / "calc" / "mod_equation_solver.py"
_SOLVER_SPEC = importlib.util.spec_from_file_location("qcalc_mod_equation_solver", _SOLVER_PATH)
_SOLVER_MODULE = importlib.util.module_from_spec(_SOLVER_SPEC)
assert _SOLVER_SPEC.loader is not None
_SOLVER_SPEC.loader.exec_module(_SOLVER_MODULE)
solve_equation = _SOLVER_MODULE.solve_equation


class TestEquationSolver(unittest.TestCase):
    def test_scalar_fast_path_auto_mode(self):
        result = solve_equation(
            left="2*x + 3",
            right="11",
            values={},
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["mode"], "scalar")
        self.assertEqual(result["unknown"], "x")
        self.assertEqual(result["solution_count"], 1)
        self.assertTrue(math.isclose(result["solutions"][0], 4.0))
        self.assertIsNone(result["unit"])

    def test_scalar_with_known_values(self):
        result = solve_equation(
            left="a*x",
            right="20",
            unknown="x",
            values={"a": 5},
            method="scalar",
        )

        self.assertEqual(result["mode"], "scalar")
        self.assertTrue(math.isclose(result["solutions"][0], 4.0))

    def test_qty_auto_mode_infers_quantity(self):
        result = solve_equation(
            left="v",
            right="d/t",
            unknown="v",
            values={"d": "120 m", "t": "10 s"},
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["mode"], "qty")
        self.assertIsInstance(result["solutions"][0], Qty)
        self.assertTrue(math.isclose(result["solutions"][0].to("m/s").val, 12.0))

    def test_qty_domain_unit_hint_converts_result(self):
        result = solve_equation(
            left="P*V",
            right="n*R*T",
            unknown="P",
            values={"V": "1.5 m^3", "n": "1 mol", "R": "1 Rg", "T": "25 degC"},
            domain={"unit": "kPa"},
        )

        self.assertEqual(result["mode"], "qty")
        self.assertIsInstance(result["solutions"][0], Qty)
        self.assertEqual(result["unit"], "kPa")
        self.assertEqual(result["solutions"][0].uom, "kPa")

    def test_qty_circle_radius_from_area(self):
        result = solve_equation(
            left="area",
            right="pi*radius^2",
            unknown="radius",
            values={"area": "100 ft**2"},
            domain={"unit": "ft"},
        )

        self.assertEqual(result["mode"], "qty")
        self.assertEqual(result["solution_count"], 2)
        self.assertTrue(all(isinstance(value, Qty) for value in result["solutions"]))
        values_ft = sorted(round(value.to("ft").val, 12) for value in result["solutions"])
        self.assertEqual(values_ft, [-5.641895835478, 5.641895835478])

    def test_inline_quantity_on_equation_side(self):
        with self.assertRaisesRegex(ValueError, "enable units_in_expression"):
            solve_equation(
                left="pi*x^2",
                right="12ft^2",
                values={},
                domain={"unit": "ft"},
            )

        result = solve_equation(
            left="pi*x^2",
            right="12ft^2",
            values={},
            domain={"unit": "ft"},
            units_in_expression=True,
        )
        self.assertEqual(result["unknown"], "x")
        self.assertEqual(result["solution_count"], 2)
        values_ft = sorted(round(value.to("ft").val, 12) for value in result["solutions"])
        self.assertEqual(values_ft, [-1.954410047612, 1.954410047612])

    def test_unknown_inference_requires_uniqueness(self):
        with self.assertRaisesRegex(ValueError, "Could not infer a single unknown symbol"):
            solve_equation(
                left="x+y",
                right="10",
                values={},
            )

    def test_disallow_unknown_inside_values(self):
        with self.assertRaisesRegex(ValueError, "Provide known values only"):
            solve_equation(
                left="x+2",
                right="6",
                unknown="x",
                values={"x": 4},
            )

    def test_unknown_inference_excludes_known_symbols(self):
        result = solve_equation(
            left="x + y",
            right="10",
            values={"y": 3},
        )
        self.assertEqual(result["unknown"], "x")
        self.assertTrue(math.isclose(result["solutions"][0], 7.0))

    def test_imaginary_scalar_solutions_supported(self):
        result = solve_equation(
            left="x^2 + 1",
            right="0",
            values={},
            method="scalar",
        )
        self.assertEqual(result["solution_count"], 2)
        self.assertIn(1j, result["solutions"])
        self.assertIn(-1j, result["solutions"])

    def test_result_unit_requires_quantity_context(self):
        with self.assertRaisesRegex(ValueError, "result_unit requires quantity context"):
            solve_equation(
                left="x^2",
                right="9",
                values={},
                domain={"unit": "ft"},
            )


if __name__ == "__main__":
    unittest.main()
