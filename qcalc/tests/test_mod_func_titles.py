# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import unittest

from qutil import fid2names, insert_implicit_multiply, title_to_variable, variable_to_title


class TestModFuncTitles(unittest.TestCase):
    def test_variable_to_title_roundtrip_cases(self):
        self.assertEqual(variable_to_title('gold__rq_uom'), 'Gold Uom')
        self.assertEqual(variable_to_title('gold__rq'), 'Gold')
        self.assertEqual(variable_to_title('count__ri'), 'Count')
        self.assertEqual(variable_to_title('age__rf'), 'Age')
        self.assertEqual(variable_to_title('name__r'), 'Name')
        self.assertEqual(variable_to_title('func_xyz--parameter_1'), 'Func Xyz: Parameter 1')

    def test_title_to_variable_roundtrip_cases(self):
        self.assertEqual(title_to_variable('Gold', '__rq'), 'gold__rq')
        self.assertEqual(title_to_variable('Gold', '__rq') + '_uom', 'gold__rq_uom')
        self.assertEqual(title_to_variable('Interest Rate', '__rf'), 'interest_rate__rf')
        self.assertEqual(title_to_variable('Func Xyz: Parameter 1'), 'func_xyz--parameter_1')

    def test_fid2names_examples(self):
        self.assertEqual(fid2names('abc-def'), ('def', 'abc'))
        self.assertEqual(fid2names('abc'), ('all', 'abc'))

    def test_insert_implicit_multiply_smoke_examples(self):
        tests = {
            '3.5m': '3.5*m',
            '5 to ft': '5 to ft',
            '3.5*m as yd, ft, inch': '3.5*m as yd, ft, inch',
            "bmi(weight='60kg')": "bmi(weight='60kg')",
            '3e5': '3e5',
            '0x1A': '0x1A',
            '1_000': '1_000',
            'x=2ft': 'x=2*ft',
            '3.5m/s to ft/s': '3.5*m/s to ft/s',
            '5kg+2g': '5*kg+2*g',
            'x=1': 'x=1',
            '3.5 m': '3.5 *m',
            '2(3+4)': '2(3+4)',
            '3j': '3j',
            'x==1': 'x==1',
            '5 in inch': '5 in inch',
            '3.5*m/s': '3.5*m/s',
        }

        for expr, expected in tests.items():
            self.assertEqual(insert_implicit_multiply(expr), expected)


if __name__ == '__main__':
    unittest.main()