# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from calc.mod_cutil import furl_from_json, fxpr_from_json

"""
furl_from_json() builds URL paths from scalar inputs
furl_from_json() skips empty values and appends ---/
furl_from_json() returns empty string for complex URL input types (like table)
furl_from_json() returns empty string for overlong scalar strings

fxpr_from_json() builds expression strings and omits None args
fxpr_from_json() handles nested qfunc-style flattened keys (f--@, f--p)
fxpr_from_json() returns empty string for complex expression input types (like codeedit)
fxpr_from_json() returns empty string for overlong scalar strings
"""
class TestFurlFromJson(unittest.TestCase):
    def test_builds_url_for_scalar_inputs(self):
        json_data = {
            "a": 10,
            "b": "2/3",
            "flag": True,
        }
        json_data_type = {
            "a": "number",
            "b": "text",
            "flag": "checkbox",
        }

        result = furl_from_json("demo_func", json_data, json_data_type)

        self.assertEqual(result, "/calc/demo_func/a/10/b/2!3/flag/True/")

    def test_skips_empty_and_marks_with_trailing_sentinel(self):
        json_data = {
            "a": "ok",
            "b": "",
            "c": None,
        }
        json_data_type = {
            "a": "text",
            "b": "text",
            "c": "text",
        }

        result = furl_from_json("demo_func", json_data, json_data_type)

        self.assertEqual(result, "/calc/demo_func/a/ok/---/")

    def test_returns_empty_for_complex_url_field_type(self):
        json_data = {
            "a": "ok",
            "table": "ignored",
        }
        json_data_type = {
            "a": "text",
            "table": "table",
        }

        result = furl_from_json("demo_func", json_data, json_data_type)

        self.assertEqual(result, "")

    def test_returns_empty_for_very_long_scalar_string(self):
        json_data = {
            "a": "x" * 512,
        }
        json_data_type = {
            "a": "text",
        }

        result = furl_from_json("demo_func", json_data, json_data_type)

        self.assertEqual(result, "")


class TestFxprFromJson(unittest.TestCase):
    def test_builds_expression_and_keeps_none_values(self):
        json_data = {
            "a": "2/3",
            "b": 11,
            "skip": None,
        }
        json_data_type = {
            "a": "text",
            "b": "number",
            "skip": "text",
        }

        result = fxpr_from_json("myfunc", json_data, json_data_type)

        self.assertEqual(result, "myfunc(a='2!3', b=11, skip=None)")

    def test_keeps_none_and_empty_defaults_in_expression(self):
        json_data = {
            "none_default": None,
            "empty_default": "",
        }
        json_data_type = {
            "none_default": "text",
            "empty_default": "text",
        }

        result = fxpr_from_json("myfunc", json_data, json_data_type)

        self.assertEqual(result, "myfunc(none_default=None, empty_default='')")

    def test_supports_nested_qfunc_from_flattened_keys(self):
        json_data = {
            "x": 7,
            "f--@": "inner",
            "f--p": "3/4",
        }
        json_data_type = {
            "x": "number",
            "f--@": "qfunc",
            "f--p": "text",
        }

        result = fxpr_from_json("outer", json_data, json_data_type)

        self.assertEqual(result, "outer(x=7, f=inner(p='3!4'))")

    def test_complex_expression_type_keeps_function_call_like_string(self):
        json_data = {
            "code": "print(1)",
        }
        json_data_type = {
            "code": "codeedit",
        }

        result = fxpr_from_json("myfunc", json_data, json_data_type)

        self.assertEqual(result, "")

    def test_returns_empty_for_overlong_scalar_value(self):
        json_data = {
            "a": "x" * 512,
        }
        json_data_type = {
            "a": "text",
        }

        result = fxpr_from_json("myfunc", json_data, json_data_type)

        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
