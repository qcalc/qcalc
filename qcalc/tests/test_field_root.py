# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.


import unittest

import qsett  # noqa: F401  # ensures Django settings are configured
from calc.templatetags.qfilter import field_root
from qconst import TOK_INDEX_SEP, TOK_PART, TOK_PART_UOM, TOK_UOM

qsett.init()


def test_field_root_tok_uom_part_and_part_uom_suffixes():
    base = "gold_weight_india"

    assert field_root(base) == base
    assert field_root(f"{base}{TOK_UOM}") == base
    assert field_root(f"{base}{TOK_PART}") == base
    assert field_root(f"{base}{TOK_PART_UOM}") == base


def test_field_root_indexed_part_and_part_uom_suffixes():
    base = "gold_weight_india"

    assert field_root(f"{base}{TOK_INDEX_SEP}1{TOK_PART}") == base
    assert field_root(f"{base}{TOK_INDEX_SEP}1{TOK_PART_UOM}") == base
    assert field_root(f"{base}{TOK_INDEX_SEP}2{TOK_PART}") == base
    assert field_root(f"{base}{TOK_INDEX_SEP}2{TOK_PART_UOM}") == base
    assert field_root(f"{base}{TOK_INDEX_SEP}9{TOK_PART}") == base
    assert field_root(f"{base}{TOK_INDEX_SEP}9{TOK_PART_UOM}") == base


def test_field_root_qdict_and_qlist_contracts():
    assert field_root("x--A") == "x"
    assert field_root(f"x{TOK_INDEX_SEP}1") == "x"


def test_field_root_falsy_values_passthrough():
    assert field_root("") == ""
    assert field_root(None) is None


def test_field_root_gold_weight_india_regression_exact_names():
    expected_root = "gold_weight_india"
    names = [
        "gold_weight_india",
        "gold_weight_india_part_uom",
        f"gold_weight_india{TOK_INDEX_SEP}2_part",
        f"gold_weight_india{TOK_INDEX_SEP}2_part_uom",
        f"gold_weight_india{TOK_INDEX_SEP}3_part",
        f"gold_weight_india{TOK_INDEX_SEP}3_part_uom",
        f"gold_weight_india{TOK_INDEX_SEP}4_part",
        f"gold_weight_india{TOK_INDEX_SEP}4_part_uom",
    ]

    for name in names:
        assert field_root(name) == expected_root


def test_field_root_multi_digit_and_alphanumeric_part_index():
    assert field_root(f"ratio") == "ratio"
    assert field_root(f"ratio{TOK_INDEX_SEP}cement{TOK_PART}") == "ratio"
    assert field_root(f"ratio{TOK_INDEX_SEP}gravel{TOK_PART}") == "ratio"


def test_field_root_qdict_key_wins_over_suffix():
    assert field_root("x--A") == "x"
    assert field_root("x--A--B") == "x"
    assert field_root(f"x--A{TOK_UOM}") == "x"
    assert field_root(f"x--A{TOK_INDEX_SEP}1") == "x"


def test_field_root_only_strips_trailing_suffix():
    assert field_root(f"a{TOK_UOM}_b") == f"a{TOK_UOM}_b"
    assert field_root(f"a{TOK_PART}_b") == f"a{TOK_PART}_b"
    assert field_root(f"a{TOK_PART_UOM}_b") == f"a{TOK_PART_UOM}_b"
    assert field_root(f"a{TOK_INDEX_SEP}1_b") == f"a{TOK_INDEX_SEP}1_b"


def test_field_root_names_that_merely_resemble_suffixes_are_unchanged():
    for name in ("part", "uom", "weight_party", "volume_uomx", "x_parts", "x_par", "x_1"):
        assert field_root(name) == name


def test_field_root_is_idempotent():
    names = [
        "x",
        f"x{TOK_UOM}",
        f"x{TOK_PART_UOM}",
        f"x{TOK_INDEX_SEP}2{TOK_PART_UOM}",
        f"x{TOK_INDEX_SEP}1",
        "x--A",
    ]

    for name in names:
        root = field_root(name)
        assert field_root(root) == root





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
        self.assertEqual(field_root('x' + TOK_INDEX_SEP + '1' + TOK_PART), 'x')
        self.assertEqual(field_root('x' + TOK_INDEX_SEP + '2' + TOK_PART), 'x')

    def test_indexed_tok_part_uom_suffix(self):
        self.assertEqual(field_root('x' + TOK_INDEX_SEP + '1' + TOK_PART_UOM), 'x')
        self.assertEqual(field_root('x' + TOK_INDEX_SEP + '2' + TOK_PART_UOM), 'x')

    def test_gold_weight_india_field_family(self):
        self.assertEqual(field_root('gold_weight_india'), 'gold_weight_india')
        self.assertEqual(field_root('gold_weight_india' + TOK_PART_UOM), 'gold_weight_india')
        self.assertEqual(field_root('gold_weight_india' + TOK_INDEX_SEP + '2' + TOK_PART), 'gold_weight_india')
        self.assertEqual(field_root('gold_weight_india' + TOK_INDEX_SEP + '2' + TOK_PART_UOM), 'gold_weight_india')

    def test_qdict_name_contract(self):
        self.assertEqual(field_root('x--A'), 'x')

    def test_qlist_name_contract(self):
        self.assertEqual(field_root('x' + TOK_INDEX_SEP + '1'), 'x')
        self.assertEqual(field_root('x' + TOK_INDEX_SEP + '20'), 'x')

    def test_empty_values(self):
        self.assertEqual(field_root(''), '')
        self.assertIsNone(field_root(None))


if __name__ == '__main__':
    unittest.main()
