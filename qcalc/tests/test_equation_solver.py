# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import math
import sys
import unittest
import importlib.util
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import qsett

qsett.init()

from qcore import Qty


_SOLVER_PATH = Path(__file__).resolve().parents[1] / "calc" / "mod_equation_solver.py"
_SOLVER_SPEC = importlib.util.spec_from_file_location("qcalc_mod_equation_solver", _SOLVER_PATH)
_SOLVER_MODULE = importlib.util.module_from_spec(_SOLVER_SPEC)
assert _SOLVER_SPEC.loader is not None
_SOLVER_SPEC.loader.exec_module(_SOLVER_MODULE)
QEquationSolver = _SOLVER_MODULE.QEquationSolver


class TestEquationSolver(unittest.TestCase):
    def test_scalar_fast_path_auto_mode(self):
        result = QEquationSolver(
            left="2*x + 3",
            right="11",
            values={},
        ).solve()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["mode"], "scalar")
        self.assertEqual(result["unknown"], "x")
        self.assertEqual(result["solution_count"], 1)
        self.assertTrue(math.isclose(result["solutions"][0], 4.0))
        self.assertIsNone(result["unit"])

    def test_log10_expression_is_supported(self):
        result = QEquationSolver(
            left="log10(x)",
            right="2",
            values={},
        ).solve()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["mode"], "scalar")
        self.assertEqual(result["unknown"], "x")
        self.assertTrue(math.isclose(result["solutions"][0], 100.0))

    def test_scalar_with_known_values(self):
        result = QEquationSolver(
            left="a*x",
            right="20",
            unknown="x",
            values={"a": 5},
            method="scalar",
        ).solve()

        self.assertEqual(result["mode"], "scalar")
        self.assertTrue(math.isclose(result["solutions"][0], 4.0))

    def test_qty_auto_mode_infers_quantity(self):
        result = QEquationSolver(
            left="v",
            right="d/t",
            unknown="v",
            values={"d": "120 m", "t": "10 s"},
        ).solve()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["mode"], "qty")
        self.assertIsInstance(result["solutions"][0], Qty)
        self.assertTrue(math.isclose(result["solutions"][0].to("m/s").val, 12.0))

    def test_qty_domain_unit_hint_converts_result(self):
        result = QEquationSolver(
            left="P*V",
            right="n*R*T",
            unknown="P",
            values={"V": "1.5 m^3", "n": "1 mol", "R": "1 Rg", "T": "25 degC"},
            domain={"unit": "kPa"},
        ).solve()

        self.assertEqual(result["mode"], "qty")
        self.assertIsInstance(result["solutions"][0], Qty)
        self.assertEqual(result["unit"], "kPa")
        self.assertEqual(result["solutions"][0].uom, "kPa")

    def test_qty_circle_radius_from_area(self):
        result = QEquationSolver(
            left="area",
            right="pi*radius^2",
            unknown="radius",
            values={"area": "100 ft**2"},
            domain={"unit": "ft"},
        ).solve()

        self.assertEqual(result["mode"], "qty")
        self.assertEqual(result["solution_count"], 2)
        self.assertTrue(all(isinstance(value, Qty) for value in result["solutions"]))
        values_ft = sorted(round(value.to("ft").val, 12) for value in result["solutions"])
        self.assertEqual(values_ft, [-5.641895835478, 5.641895835478])

    def test_inline_quantity_on_equation_side(self):
        with self.assertRaisesRegex(ValueError, "enable units_in_expression"):
            QEquationSolver(
                left="pi*x^2",
                right="12ft^2",
                values={},
                domain={"unit": "ft"},
            ).solve()

        result = QEquationSolver(
            left="pi*x^2",
            right="12ft^2",
            values={},
            domain={"unit": "ft"},
            units_in_expression=True,
        ).solve()
        self.assertEqual(result["unknown"], "x")
        self.assertEqual(result["solution_count"], 2)
        values_ft = sorted(round(value.to("ft").val, 12) for value in result["solutions"])
        self.assertEqual(values_ft, [-1.954410047612, 1.954410047612])

    def test_unknown_inference_requires_uniqueness(self):
        with self.assertRaisesRegex(ValueError, "Could not infer a single unknown symbol"):
            QEquationSolver(
                left="x+y",
                right="10",
                values={},
            ).solve()

    def test_disallow_unknown_inside_values(self):
        with self.assertRaisesRegex(ValueError, "Provide known values only"):
            QEquationSolver(
                left="x+2",
                right="6",
                unknown="x",
                values={"x": 4},
            ).solve()

    def test_unknown_inference_excludes_known_symbols(self):
        result = QEquationSolver(
            left="x + y",
            right="10",
            values={"y": 3},
        ).solve()
        self.assertEqual(result["unknown"], "x")
        self.assertTrue(math.isclose(result["solutions"][0], 7.0))

    def test_imaginary_scalar_solutions_supported(self):
        result = QEquationSolver(
            left="x^2 + 1",
            right="0",
            values={},
            method="scalar",
        ).solve()
        self.assertEqual(result["solution_count"], 2)
        self.assertIn(1j, result["solutions"])
        self.assertIn(-1j, result["solutions"])

    def test_result_unit_requires_quantity_context(self):
        with self.assertRaisesRegex(ValueError, "result_unit requires quantity context"):
            QEquationSolver(
                left="x^2",
                right="9",
                values={},
                domain={"unit": "ft"},
            ).solve()


if __name__ == "__main__":
    unittest.main()
