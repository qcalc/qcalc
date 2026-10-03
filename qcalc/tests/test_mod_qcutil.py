# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import qsett
qsett.init()

from qcore import df_formatter
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
        self.assertEqual(df_formatter(value), '1.23456')
        self.assertEqual(df_formatter(value, unit_hint='m'), '1.235 m')
        self.assertEqual(df_formatter(value, unit_hint='m', val_only=True), '1.235')

    def test_formats_qty_strings(self):
        QThread.set_pref({
            'decimal': 5,
            'qty_decimal': 3,
            'currency_decimal': 2,
            'ignore_decimal_format': False,
            'thousands_separator': False,
        })

        self.assertEqual(df_formatter('76.1234 deg'), '76.123 deg')
        self.assertEqual(df_formatter('65.1234 ft', val_only=True), '65.123')

    def test_formats_numeric_strings_with_and_without_unit_hint(self):
        QThread.set_pref({
            'decimal': 5,
            'qty_decimal': 3,
            'currency_decimal': 2,
            'ignore_decimal_format': False,
            'thousands_separator': False,
        })

        self.assertEqual(df_formatter('1.23456'), '1.23456')
        self.assertEqual(df_formatter('1.23456', unit_hint='m'), '1.235 m')


if __name__ == '__main__':
    unittest.main()
