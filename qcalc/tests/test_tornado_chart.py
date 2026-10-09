import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import qsett

qsett.init()

from calculators.all.general.chart import tornado_chart


class TestTornadoChart(unittest.TestCase):
    def test_tornado_chart_renders_and_sorts_by_absolute_impact(self):
        result = tornado_chart(
            data={
                'columns': ['Factor', 'Low', 'High'],
                'data': [['Price', 95, 105], ['Volume', 80, 130], ['FX', 98, 102]],
            },
            baseline=100,
            sort_by='absolute',
        )
        chart = result['chart']
        self.assertIsNotNone(chart)

        labels = [tick.get_text() for tick in chart.ax.get_yticklabels()]
        self.assertEqual(labels, ['Volume', 'Price', 'FX'])

    def test_tornado_chart_rejects_non_numeric_low_high(self):
        with self.assertRaisesRegex(ValueError, 'must contain numeric values'):
            tornado_chart(
                data={
                    'columns': ['Factor', 'Low', 'High'],
                    'data': [['Price', 'bad', 105]],
                },
                baseline=100,
            )


if __name__ == '__main__':
    unittest.main()
