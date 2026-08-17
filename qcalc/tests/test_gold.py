# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import unittest
import qsett
from calculators.all.others.cal_others import gold
qsett.init()

class TestGoldFunction(unittest.TestCase):

    def test_gold_calculation(self):
        result = gold(gold_weight_intl='20.0 g', gold_price='80.0 UNC/g', making_charge_pct=6)
        print(result)
        self.assertEqual(result["gold_weight"].val, 20.0)
        self.assertEqual(result["gold_value"].val, 1600.0)
        self.assertEqual(result["vat_on_gold"].val, 80.0)
        self.assertEqual(result["making_charge"].val, 96.0)
        self.assertEqual(result["grand_total"].val, 1776.0)

    def test_gold_calculation_with_different_currency(self):
        result = gold(gold_weight_intl='15.0 g', gold_price='75.0 EUR/g', making_charge_pct=5)
        print(result)
        self.assertEqual(result["gold_weight"].val, 15.0)
        self.assertEqual(result["gold_value"].val, 1125.0)
        self.assertEqual(result["vat_on_gold"].val, 56.25)
        self.assertEqual(result["making_charge"].val, 56.25)
        self.assertEqual(result["grand_total"].val, 1237.50)


if __name__ == '__main__':
    unittest.main()
