# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import qsett

qsett.init()

from qcore import Qty, QFormatter, QCurrency
from qutil import QThread


class TestDfFormatter(unittest.TestCase):
    def test_uses_decimal_for_plain_numbers_and_qty_decimal_with_unit_hint(self):
        QThread.set_pref({
            'decimal': 5,
            'qty_decimal': 3,
            'currency_decimal': 2,
            'ignore_decimal_format': False,
            'thousands_separator': False,
        })

        value = 1.23456
        fmt = QFormatter()
        self.assertEqual(fmt.df(value), '1.23456')
        self.assertEqual(fmt.df(value, unit_hint='m'), '1.235 m')
        self.assertEqual(fmt.df(value, unit_hint='m', val_only=True), '1.235')

    def test_formats_qty_strings(self):
        QThread.set_pref({
            'decimal': 5,
            'qty_decimal': 3,
            'currency_decimal': 2,
            'ignore_decimal_format': False,
            'thousands_separator': False,
        })

        fmt = QFormatter()
        self.assertEqual(fmt.df('76.1234 deg'), '76.123 deg')
        self.assertEqual(fmt.df('65.1234 ft', val_only=True), '65.123')

    def test_formats_numeric_strings_with_and_without_unit_hint(self):
        QThread.set_pref({
            'decimal': 5,
            'qty_decimal': 3,
            'currency_decimal': 2,
            'ignore_decimal_format': False,
            'thousands_separator': False,
        })

        fmt = QFormatter()
        self.assertEqual(fmt.df('1.23456'), '1.23456')
        self.assertEqual(fmt.df('1.23456', unit_hint='m'), '1.235 m')

    def test_qformat_q_thousands_separator_override(self):
        QThread.set_pref({
            'decimal': 5,
            'qty_decimal': 3,
            'currency_decimal': 2,
            'ignore_decimal_format': False,
            'thousands_separator': True,
        })

        qty = Qty('1234567.5 kg')
        fmt = QFormatter()
        self.assertEqual(fmt.qty(qty), '1,234,567.5 kg')
        self.assertEqual(fmt.qty(qty, thousands_separator=False), '1234567.5 kg')


class TestCurrencyPreferenceHelpers(unittest.TestCase):
    def test_currency_replacement_uses_preference(self):
        cur = QCurrency('EUR')
        qtystr = '120km/inr'

        self.assertTrue(cur.to_ucur(qtystr, 'INR').endswith('km/EUR'))
        self.assertEqual(cur.to_ucur(Qty(qtystr), 'INR').uom, 'km/EUR')
        self.assertTrue(cur.to_ucur('@ft/BDT', 'bdt').endswith('@ft/EUR'))

        qty = Qty('@bdt/s')
        self.assertEqual(cur.convert(qty.val, qty.uom, 'BDT')[1], 'EUR/s')


if __name__ == '__main__':
    unittest.main()
