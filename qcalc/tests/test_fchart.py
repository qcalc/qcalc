# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import qsett

qsett.init()

from calc.mod_result_chart import QResults


class TestResults2Chart(unittest.TestCase):
    def test_missing_result_is_displayed_in_table_and_preserved_for_chart(self):
        qr = QResults([1.0, None, 3.0], xvals=[0, 1, 2], show='both')
        qr.setup_chart()
        result = qr.objects()

        table = result['table']
        self.assertTrue(math.isnan(table['Result'].iloc[1]))
        self.assertIn('<td>None</td>', table.to_html(na_rep='None', index=False))

        chart_data = QResults.df2chart_data(table, x_column='X')
        chart_values = chart_data['yvalsm'][0]
        self.assertTrue(math.isnan(chart_values.iloc[1]))


if __name__ == '__main__':
    unittest.main()
