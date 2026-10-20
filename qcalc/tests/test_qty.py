# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qcore import *
from qcore import _base_names

class TestQtyBasics(unittest.TestCase):
    def test_1(self):
        x1 = Qty('1 ft')
        self.assertTrue(isMeasureQuantity(x1))
        x2 = Qty('None ft')
        self.assertTrue(isMeasureQuantity(x2))
        x3 = Qty('@ft')
        self.assertTrue(isMeasureQuantity(x3))
        self.assertEqual(unit2lmt('ft/s'), 'LT-1')
        self.assertFalse(is_str_qty('ft'))
        self.assertTrue(is_str_uom('ft'))
        self.assertTrue(is_str_named_uom('ft'))
        self.assertFalse(is_str_named_uom('ft/s'))
        self.assertFalse(isMeasureQuantity('1ft, 6inch'))
        self.assertTrue(is_str_qty(compose_qty('1ft, 6 inch')[0]))
        y1 = Qty('1 m')
        y2 = Qty('1 s')
        y3 = y1 / y2
        self.assertEqual(y3, Qty('1m/s'))
        self.assertEqual(dim_to_bname('LT-1', _base_names), 'm/s')
        self.assertEqual(y3 * y2, y1)
        # dimensionless testing
        rate = Qty('9 pct/yr')
        period = Qty('60 mo')
        interest = rate*period # dimensionless
        self.assertFalse(isMeasureQuantity(interest))
        self.assertEqual(interest,0.45)

    def test_2(self):
        x1 = Qty('12 ft/s')
        self.assertEqual(120 / x1, Qty('10 s/ft'))
        self.assertEqual(x1.in_units_of('yd/s', 'inch/s')[1].val, 0)
        self.assertEqual(pow(x1, 2).val, 144)
        x1 = x1.to('inch/s')
        self.assertEqual(x1.val, 144)
        self.assertEqual(x1.in_base_units().uom, 'm/s')

    def test_3(self):
        self.assertTrue(len(lmt2ulist('L')) > 0)
        ulist_subset = lmt2ulist('L', subset=True)
        self.assertTrue(len(ulist_subset) > 0)
        self.assertTrue(set([u[0] for u in ulist_subset]).issubset(
            {'mm', 'cm', 'm', 'km', 'inch', 'ft', 'yd', 'mi', 'nmi'}))
        ulist_area_with_default = lmt2ulist('L2', subset=True, default_uname='decimal')
        self.assertTrue(len(ulist_area_with_default) > 0)
        self.assertEqual(ulist_area_with_default[0][0], 'decimal')
        ulist_currency_with_default = lmt2ulist('C', subset=True, default_uname='USD')
        self.assertTrue(len(ulist_currency_with_default) > 0)
        self.assertEqual(ulist_currency_with_default[0][0], 'usd')
        self.assertTrue(len(lmt2catalog('L')) > 0)
        self.assertEqual(lmt_desc('L'), 'Length, Wavelength')
        # self.assertTrue(len(search_qty_result('area')) >= 2)
        # self.assertTrue(uname2ulist('kg') >= 2)
        self.assertEqual(Qty('1 yd','ft').val,3)
        self.assertEqual(Qty(1, 'yd','ft').val,3)
        self.assertEqual(Qty('1 yd').val,1)
        self.assertEqual(Qty('1 ft').val,1)

    def test_4(self):
        # test Gas Constant = BotzmanConstant * AvogadroConstant
        r = Qty('1 k_b') * Qty('1 nav')
        bolt_avo=r.to('m^2*kg/s^2/K/mol')
        gas_c = Qty('1 rg').to('m^2*kg/s^2/K/mol')
        print(bolt_avo, gas_c)
        self.assertTrue(abs(bolt_avo.val-gas_c.val)<1e-6)

    def test_qty_is_hashable_by_base_value_and_dimension(self):
        quantities = {Qty('1 m'), Qty('100 cm'), Qty('5 ft'), Qty('60 inch')}
        self.assertEqual(Qty('5 ft'), Qty('60 inch'))
        self.assertFalse(Qty('5 ft') != Qty('60 inch'))
        self.assertEqual(len(quantities), 2)


if __name__ == '__main__':
    unittest.main()
    # coverage run --source=qcore -m unittest qtest/test_qty.py
    # coverage report -m
    # coverage report
