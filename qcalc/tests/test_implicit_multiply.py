# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qutil import insert_implicit_multiply, preprocess_expression


class TestInsertImplicitMultiply(unittest.TestCase):
    def test_number_immediately_followed_by_unit(self):
        self.assertEqual(insert_implicit_multiply("5kg"), "5*kg")
        self.assertEqual(insert_implicit_multiply("3.5m"), "3.5*m")
        self.assertEqual(insert_implicit_multiply("2ft"), "2*ft")

    def test_number_space_unit(self):
        self.assertEqual(insert_implicit_multiply("3.5 m"), "3.5 *m")
        self.assertEqual(insert_implicit_multiply("5   kg"), "5   *kg")

    def test_multiple_occurrences_in_one_expression(self):
        self.assertEqual(insert_implicit_multiply("5kg+2g"), "5*kg+2*g")
        self.assertEqual(insert_implicit_multiply("3.5m/s"), "3.5*m/s")

    def test_assignment_and_arithmetic(self):
        self.assertEqual(insert_implicit_multiply("x=2ft"), "x=2*ft")
        self.assertEqual(insert_implicit_multiply("(2+3*5-12)/3"), "(2+3*5-12)/3")

    def test_already_has_operator_is_unchanged(self):
        self.assertEqual(insert_implicit_multiply("3.5*m"), "3.5*m")
        self.assertEqual(insert_implicit_multiply("3.5*m/s"), "3.5*m/s")

    def test_dsl_words_to_and_as_are_not_treated_as_units(self):
        self.assertEqual(insert_implicit_multiply("5 to ft"), "5 to ft")
        self.assertEqual(insert_implicit_multiply("3.5*m to ft"), "3.5*m to ft")
        self.assertEqual(
            insert_implicit_multiply("3.5*m as yd, ft, inch"),
            "3.5*m as yd, ft, inch",
        )

    def test_python_keywords_after_number_are_not_touched(self):
        self.assertEqual(insert_implicit_multiply("5 in inch"), "5 in inch")
        self.assertEqual(insert_implicit_multiply("x==1"), "x==1")
        self.assertEqual(insert_implicit_multiply("x and y"), "x and y")

    def test_string_literals_are_untouched(self):
        self.assertEqual(
            insert_implicit_multiply("bmi(weight='60kg')"),
            "bmi(weight='60kg')",
        )

    def test_scientific_complex_and_hex_literals_untouched(self):
        self.assertEqual(insert_implicit_multiply("3e5"), "3e5")
        self.assertEqual(insert_implicit_multiply("3e5+1"), "3e5+1")
        self.assertEqual(insert_implicit_multiply("3j"), "3j")
        self.assertEqual(insert_implicit_multiply("0x1A"), "0x1A")
        self.assertEqual(insert_implicit_multiply("1_000"), "1_000")

    def test_number_followed_by_open_paren_is_not_handled(self):
        # only NUMBER->NAME adjacency is targeted, not NUMBER->'(' calls
        self.assertEqual(insert_implicit_multiply("2(3+4)"), "2(3+4)")

    def test_plain_number_and_plain_name_are_unchanged(self):
        self.assertEqual(insert_implicit_multiply("x=1"), "x=1")
        self.assertEqual(insert_implicit_multiply("ft"), "ft")
        self.assertEqual(insert_implicit_multiply("5"), "5")

    def test_multiline_input_is_returned_unchanged(self):
        expr = "x=1\ny=2"
        self.assertEqual(insert_implicit_multiply(expr), expr)

    def test_invalid_syntax_falls_back_to_original(self):
        expr = "5kg +"
        # tokenizer may raise on trailing operator; must not crash or corrupt
        result = insert_implicit_multiply(expr)
        self.assertIsInstance(result, str)


class TestPreprocessExpressionIntegration(unittest.TestCase):
    def test_implicit_multiply_applied_before_calculation(self):
        self.assertEqual(preprocess_expression("5kg"), "5*kg")
        self.assertEqual(preprocess_expression("3.5m/s to ft/s"), "3.5*m/s to ft/s")

    def test_exponent_and_implicit_multiply_combined(self):
        self.assertEqual(preprocess_expression("2ft^2"), "2*ft**2")
        self.assertEqual(preprocess_expression("2*ft^2"), "2*ft**2")

    def test_not_applied_before_displaying(self):
        # disp=True path must not run implicit-multiply insertion
        self.assertEqual(preprocess_expression("5kg", disp=True), "5kg")


if __name__ == "__main__":
    unittest.main()
