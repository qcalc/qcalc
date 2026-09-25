# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qsett

from calc.templatetags.qfilter import field_root
from qconst import TOK_PART, TOK_PART_UOM, TOK_UOM


qsett.init()


def test_field_root_tok_uom_part_and_part_uom_suffixes():
    base = "gold_weight_india"

    assert field_root(base) == base
    assert field_root(f"{base}{TOK_UOM}") == base
    assert field_root(f"{base}{TOK_PART}") == base
    assert field_root(f"{base}{TOK_PART_UOM}") == base


def test_field_root_indexed_part_and_part_uom_suffixes():
    base = "gold_weight_india"

    assert field_root(f"{base}_1{TOK_PART}") == base
    assert field_root(f"{base}_1{TOK_PART_UOM}") == base
    assert field_root(f"{base}_2{TOK_PART}") == base
    assert field_root(f"{base}_2{TOK_PART_UOM}") == base
    assert field_root(f"{base}_9{TOK_PART}") == base
    assert field_root(f"{base}_9{TOK_PART_UOM}") == base


def test_field_root_qdict_and_qlist_contracts():
    assert field_root("x--A") == "x"
    assert field_root("x_1") == "x"


def test_field_root_falsy_values_passthrough():
    assert field_root("") == ""
    assert field_root(None) is None


def test_field_root_gold_weight_india_regression_exact_names():
    expected_root = "gold_weight_india"
    names = [
        "gold_weight_india",
        "gold_weight_india_part_uom",
        "gold_weight_india_2_part",
        "gold_weight_india_2_part_uom",
        "gold_weight_india_3_part",
        "gold_weight_india_3_part_uom",
        "gold_weight_india_4_part",
        "gold_weight_india_4_part_uom",
    ]

    for name in names:
        assert field_root(name) == expected_root


# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import unittest

import qsett  # noqa: F401  # ensures Django settings are configured
from calc.templatetags.qfilter import field_root
from qconst import TOK_PART, TOK_PART_UOM, TOK_UOM


class TestFieldRoot(unittest.TestCase):

    def test_base_name_is_unchanged(self):
        self.assertEqual(field_root('x'), 'x')

    def test_tok_uom_suffix(self):
        self.assertEqual(field_root('x' + TOK_UOM), 'x')

    def test_tok_part_suffix(self):
        self.assertEqual(field_root('x' + TOK_PART), 'x')

    def test_tok_part_uom_suffix(self):
        self.assertEqual(field_root('x' + TOK_PART_UOM), 'x')

    def test_indexed_tok_part_suffix(self):
        self.assertEqual(field_root('x_1' + TOK_PART), 'x')
        self.assertEqual(field_root('x_2' + TOK_PART), 'x')

    def test_indexed_tok_part_uom_suffix(self):
        self.assertEqual(field_root('x_1' + TOK_PART_UOM), 'x')
        self.assertEqual(field_root('x_2' + TOK_PART_UOM), 'x')

    def test_gold_weight_india_field_family(self):
        self.assertEqual(field_root('gold_weight_india'), 'gold_weight_india')
        self.assertEqual(field_root('gold_weight_india' + TOK_PART_UOM), 'gold_weight_india')
        self.assertEqual(field_root('gold_weight_india_2' + TOK_PART), 'gold_weight_india')
        self.assertEqual(field_root('gold_weight_india_2' + TOK_PART_UOM), 'gold_weight_india')

    def test_qdict_name_contract(self):
        self.assertEqual(field_root('x--A'), 'x')

    def test_qlist_name_contract(self):
        self.assertEqual(field_root('x_1'), 'x')
        self.assertEqual(field_root('x_20'), 'x')

    def test_empty_values(self):
        self.assertEqual(field_root(''), '')
        self.assertIsNone(field_root(None))


if __name__ == '__main__':
    unittest.main()
