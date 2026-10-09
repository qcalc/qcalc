import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import qsett

qsett.init()

from calculators.all.analytics import sensitivity


class TestSensitivity(unittest.TestCase):
    def test_sensitivity_ranks_stronger_driver_higher(self):
        result = sensitivity(
            variation_target='v',
            xpr='3*x + y',
            inputs={
                'columns': ['Variable', 'Distribution', 'Param 1', 'Param 2', 'Param 3'],
                'data': [['x', 'normal', 0, 1, ''], ['y', 'normal', 0, 1, '']],
            },
            method='both',
            trials=600,
            random_seed=7,
            show='table',
        )

        table = result['table']
        self.assertEqual(table.iloc[0]['Variable'], 'x')
        self.assertGreater(float(table.iloc[0]['SRC Abs']), float(table.iloc[1]['SRC Abs']))
        self.assertGreater(float(table.iloc[0]['PRCC Abs']), float(table.iloc[1]['PRCC Abs']))

    def test_sensitivity_requires_target_column_for_multi_output(self):
        with self.assertRaisesRegex(Exception, 'specify target_column'):
            sensitivity(
                variation_target='v',
                xpr="{'A': x, 'B': y}",
                inputs={
                    'columns': ['Variable', 'Distribution', 'Param 1', 'Param 2', 'Param 3'],
                    'data': [['x', 'normal', 0, 1, ''], ['y', 'normal', 0, 1, '']],
                },
                method='src',
                trials=120,
                random_seed=2,
                show='table',
            )

    def test_sensitivity_uses_selected_target_column(self):
        result = sensitivity(
            variation_target='v',
            xpr="{'Revenue': 2*x + y, 'Cost': x - y}",
            target_column='Cost',
            inputs={
                'columns': ['Variable', 'Distribution', 'Param 1', 'Param 2', 'Param 3'],
                'data': [['x', 'normal', 0, 1, ''], ['y', 'normal', 0, 1, '']],
            },
            method='src',
            trials=300,
            random_seed=11,
            show='table',
        )

        summary = dict(result['Summary']['data'])
        self.assertEqual(summary['Target'], 'cost')
        self.assertEqual(summary['Method'], 'SRC')


if __name__ == '__main__':
    unittest.main()
