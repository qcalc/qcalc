# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import math
import sys
import unittest
from datetime import date
from pathlib import Path

import matplotlib.dates as mdates
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import qsett

qsett.init()

from calc.mod_result_chart import QResults


class TestResults2Chart(unittest.TestCase):
    def test_missing_result_is_displayed_in_table_and_preserved_for_chart(self):
        qr = QResults([1.0, None, 3.0], show='both')
        qr.setup_chart()
        result = qr.objects()

        table = result['table']
        self.assertTrue(math.isnan(table['Result'].iloc[1]))
        self.assertIn('<td>None</td>', table.to_html(na_rep='None', index=False))

        chart_data = QResults.df2chart_data(table)
        chart_values = chart_data['yvalsm'][0]
        self.assertTrue(math.isnan(chart_values.iloc[1]))

    def test_df2chart_data_includes_date_series(self):
        table = pd.DataFrame({
            'X': ['V1', 'V2', 'V3'],
            'Result': [date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 4)],
        })

        chart_data = QResults.df2chart_data(table, x_column='X')
        self.assertEqual(chart_data['ylabels'], ['Result'])
        self.assertEqual(
            list(chart_data['yvalsm'][0]),
            [date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 4)],
        )

    def test_df2chart_renders_bar_chart_when_all_series_are_dates(self):
        table = pd.DataFrame({
            'X': ['V1', 'V2', 'V3'],
            'Result': [date(2026, 1, 2), date(2026, 1, 3), date(2026, 1, 4)],
        })

        chart = QResults.df2chart(table, x_column='X', chart_type='bars')
        self.assertIsNotNone(chart)
        self.assertIsInstance(chart.ax.yaxis.get_major_formatter(), mdates.DateFormatter)


if __name__ == '__main__':
    unittest.main()
