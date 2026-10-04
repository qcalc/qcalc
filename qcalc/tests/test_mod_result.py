# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import sys
import os
import time
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import qsett
import qconst

qsett.init()

from calc.mod_result import df2normalized
from qcore import Qty
from qutil import QThread


class TestDf2UnitNormalized(unittest.TestCase):
    def test_converts_qty_column_and_appends_unit_to_header(self):
        df = pd.DataFrame({
            'Length': [Qty('2 m'), Qty('3 m'), None],
            'Label': ['A', 'B', 'C'],
        })

        out = df2normalized(df)
        length_col = f'Length {qconst.TBL_UOM_SEP} m'

        self.assertIn(length_col, out.columns)
        self.assertNotIn('Length', out.columns)
        self.assertEqual(out[length_col].iloc[0], 2.0)
        self.assertEqual(out[length_col].iloc[1], 3.0)
        self.assertTrue(pd.isna(out[length_col].iloc[2]))
        self.assertEqual(out['Label'].tolist(), ['A', 'B', 'C'])

    def test_accepts_qtable_dict_input(self):
        table = {
            'columns': ['Force'],
            'data': [[Qty('10 N')], [Qty('20 N')]],
        }

        out = df2normalized(table)
        force_col = f'Force {qconst.TBL_UOM_SEP} N'

        self.assertIsInstance(out, pd.DataFrame)
        self.assertEqual(list(out.columns), [force_col])
        self.assertEqual(out[force_col].tolist(), [10.0, 20.0])

    def test_ignores_non_convertible_columns_without_error(self):
        df = pd.DataFrame({
            'QtyOk': [Qty('5 kg'), None, Qty('6 kg')],
            'MixedType': [Qty('1 m'), 'bad-data', Qty('3 m')],
            'MixedUnits': [Qty('1 m'), Qty('100 cm'), None],
        })

        out = df2normalized(df)
        qty_col = f'QtyOk {qconst.TBL_UOM_SEP} kg'

        self.assertIn(qty_col, out.columns)
        self.assertEqual(out[qty_col].iloc[0], 5.0)
        self.assertTrue(pd.isna(out[qty_col].iloc[1]))
        self.assertEqual(out[qty_col].iloc[2], 6.0)

        self.assertIn('MixedType', out.columns)
        self.assertIsInstance(out['MixedType'].iloc[0], Qty)

        self.assertIn('MixedUnits', out.columns)
        self.assertIsInstance(out['MixedUnits'].iloc[0], Qty)

    def test_converts_qty_strings_and_qty_objects_in_same_column(self):
        df = pd.DataFrame({
            'Distance': [Qty('1 m'), '2 m', None, '3 m'],
        })

        out = df2normalized(df)
        dist_col = f'Distance {qconst.TBL_UOM_SEP} m'

        self.assertEqual(list(out.columns), [dist_col])
        self.assertEqual(out[dist_col].iloc[0], 1.0)
        self.assertEqual(out[dist_col].iloc[1], 2.0)
        self.assertTrue(pd.isna(out[dist_col].iloc[2]))
        self.assertEqual(out[dist_col].iloc[3], 3.0)

    def test_can_format_after_normalization_using_header_unit_context(self):
        QThread.set_pref({
            'decimal': 5,
            'qty_decimal': 3,
            'currency_decimal': 2,
            'ignore_decimal_format': False,
            'thousands_separator': False,
        })

        df = pd.DataFrame({
            'Distance': [Qty('1.23456 m')],
            'RawValue': [1.23456],
        })

        out = df2normalized(df, do_format=True)
        dist_col = f'Distance {qconst.TBL_UOM_SEP} m'

        self.assertEqual(out[dist_col].iloc[0], '1.235')
        self.assertEqual(out['RawValue'].iloc[0], '1.23456')

    def test_do_format_formats_qty_strings_in_non_convertible_object_column(self):
        QThread.set_pref({
            'decimal': 5,
            'qty_decimal': 3,
            'currency_decimal': 2,
            'ignore_decimal_format': False,
            'thousands_separator': False,
        })

        df = pd.DataFrame({
            'Param3': ['76.1234 deg', '', '65.1234 ft'],
        })
        out = df2normalized(df, do_format=True)

        self.assertEqual(list(out.columns), ['Param3'])
        self.assertEqual(out['Param3'].tolist(), ['76.123 deg', '', '65.123 ft'])

    @unittest.skipUnless(
        os.getenv('QCALC_RUN_BENCHMARKS') == '1',
        'Set QCALC_RUN_BENCHMARKS=1 to run benchmark tests.',
    )
    def test_benchmark_df2normalized_vs_baseline(self):
        from qcore import as_qtable, Qty, is_str_qty

        def baseline_df2normalized(df):
            local_df = as_qtable(df)
            normalized_df = local_df.copy()
            rename_map = {}

            for col in normalized_df.columns:
                col_unit = ''
                can_convert = True
                has_qty = False

                def _to_qty(value):
                    if isinstance(value, Qty):
                        return value
                    if isinstance(value, str) and is_str_qty(value.strip()):
                        return Qty(value.strip())
                    return None

                for value in normalized_df[col].tolist():
                    if value is None:
                        continue

                    qty_value = _to_qty(value)
                    if qty_value is not None:
                        has_qty = True
                        value_unit = str(qty_value.uom).strip()
                        if value_unit:
                            if col_unit == '':
                                col_unit = value_unit
                            elif value_unit != col_unit:
                                can_convert = False
                                break
                    else:
                        can_convert = False
                        break

                if not (can_convert and has_qty):
                    continue

                values = []
                for value in normalized_df[col].tolist():
                    if value is None:
                        values.append(None)
                    else:
                        qty_value = _to_qty(value)
                        values.append(qty_value.val if qty_value is not None else value)

                normalized_df[col] = values
                if col_unit:
                    col_name = str(col)
                    suffix = f'{qconst.TBL_UOM_SEP} {col_unit}'
                    if not col_name.strip().endswith(suffix):
                        rename_map[col] = f'{col_name} {suffix}'

            if rename_map:
                normalized_df = normalized_df.rename(columns=rename_map)

            return normalized_df

        rows = 20000
        df = pd.DataFrame({
            'Distance': [f'{i % 7 + 1} m' for i in range(rows)],
            'Mass': [Qty('2 kg') if i % 3 else None for i in range(rows)],
            'Label': [f'row-{i}' for i in range(rows)],
            'Value': [float(i) for i in range(rows)],
        })

        expected = baseline_df2normalized(df)
        actual = df2normalized(df)
        pd.testing.assert_frame_equal(actual, expected)

        def _bench(fn, arg, loops=5):
            durations = []
            for _ in range(2):  # warmup
                _ = fn(arg)
            for _ in range(loops):
                t0 = time.perf_counter()
                _ = fn(arg)
                durations.append(time.perf_counter() - t0)
            durations.sort()
            return durations[len(durations) // 2], durations

        base_median, base_all = _bench(baseline_df2normalized, df)
        new_median, new_all = _bench(df2normalized, df)
        speedup = (base_median / new_median) if new_median > 0 else float('inf')

        print(
            f'Benchmark df2normalized (rows={rows})\\n'
            f'baseline median: {base_median:.6f}s runs={base_all}\\n'
            f'optimized median: {new_median:.6f}s runs={new_all}\\n'
            f'speedup: {speedup:.2f}x'
        )


if __name__ == '__main__':
    unittest.main()
