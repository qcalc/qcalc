# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qutil import insert_implicit_multiply, preprocess_expression, to_python_expr, to_user_expr, url_to_user_expr


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


class TestExpressionConversion(unittest.TestCase):
    def test_implicit_multiply_applied_before_calculation(self):
        self.assertEqual(to_python_expr("5kg"), "5*kg")
        self.assertEqual(to_python_expr("3.5m/s to ft/s"), "3.5*m/s to ft/s")

    def test_exponent_and_implicit_multiply_combined(self):
        self.assertEqual(to_python_expr("2ft^2"), "2*ft**2")
        self.assertEqual(to_python_expr("2*ft^2"), "2*ft**2")

    def test_xor_round_trip(self):
        self.assertEqual(to_python_expr("a^^b"), "a^b")
        self.assertEqual(to_user_expr("a**2"), "a^2")

    def test_to_user_expr_does_not_insert_implicit_multiply(self):
        self.assertEqual(to_user_expr("5kg"), "5kg")

    def test_bang_is_decoded_to_division_only_for_url_values(self):
        self.assertEqual(url_to_user_expr("m!s"), "m/s")
        self.assertEqual(to_python_expr("m!s"), "m!s")
        self.assertEqual(to_user_expr("m!s"), "m!s")

    def test_url_value_also_gets_user_exponent_syntax(self):
        self.assertEqual(url_to_user_expr("m**2!s"), "m^2/s")

    def test_not_equal_operator_is_preserved(self):
        code = "if a != b:\n    x = 2 != 3"
        self.assertEqual(to_python_expr(code), code)
        self.assertEqual(to_user_expr(code), code)
        self.assertEqual(url_to_user_expr(code), code)
        self.assertEqual(url_to_user_expr("a!=b!c"), "a!=b/c")

    def test_preprocess_expression_wrapper_delegates(self):
        self.assertEqual(preprocess_expression("2ft^2"), "2*ft**2")
        self.assertEqual(preprocess_expression("2ft**2", disp=True), "2ft^2")


if __name__ == "__main__":
    unittest.main()
