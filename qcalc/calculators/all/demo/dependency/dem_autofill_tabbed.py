# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import list2options, StdList


def demo_autofill_tabbed__info():
    return {
        'title': 'Tabbed Autofill Demo',
        'interactive': True,
        'layout': 'tb',
        'input_columns': 1,
        'input_blocks': [
            {
                'column': 1,
                'tabs': [
                    {
                        'title': 'Selectors',
                        'fields': [
                            'brand_choice',
                            'mode_choice',
                        ],
                    },
                    {
                        'title': 'Autofilled Values',
                        'fields': [
                            'coverage_low',
                            'coverage_mid',
                            'coverage_high',
                            'option_x',
                            'option_y',
                        ],
                    },
                ],
            },
        ],
        'schema': {
            'brand_choice': list2options(StdList.autofill1_list, initial='C3'),
            'mode_choice': list2options(StdList.autofill2_list, initial='z'),
        },
        'autofill': {
            'brand_choice': list2options(
                StdList.autofill1data_list,
                fields=['coverage_low', 'coverage_mid', 'coverage_high'],
            ),
            'mode_choice': list2options(
                StdList.autofill2data_list,
                fields=['option_x', 'option_y'],
            ),
        },
    }


def demo_autofill_tabbed(
    brand_choice,
    coverage_low,
    coverage_mid,
    coverage_high,
    mode_choice,
    option_x,
    option_y,
):
    sum1 = coverage_low + coverage_mid + coverage_high
    sum2 = option_x + option_y
    return {
        'brand_choice': brand_choice,
        'mode_choice': mode_choice,
        'sum1': sum1,
        'sum2': sum2,
        'total': sum1 + sum2,
    }
