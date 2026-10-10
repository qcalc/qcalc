# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import dict2options, StdList


def demo_autofill2_tabbed__info():
    return {
        'title': 'Tabbed Autofill Demo 2',
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
                            'select_1',
                            'select_2',
                        ],
                    },
                    {
                        'title': 'Autofilled Values',
                        'fields': [
                            'auto_fill_11',
                            'auto_fill_12',
                            'auto_fill_13',
                            'auto_fill_21',
                            'auto_fill_22',
                        ],
                    },
                ],
            },
        ],
        'schema': {
            'select_1': dict2options(StdList.autofill1_list, initial='C3'),
            'select_2': dict2options(StdList.autofill2_list, initial='z'),
        },
        'autofill': {
            'select_1': dict2options(
                StdList.autofill1data_list,
                fields=['auto_fill_11', 'auto_fill_12', 'auto_fill_13'],
            ),
            'select_2': dict2options(
                StdList.autofill2data_list,
                fields=['auto_fill_21', 'auto_fill_22'],
            ),
        },
    }


def demo_autofill2_tabbed(
    select_1,
    auto_fill_11,
    auto_fill_12,
    auto_fill_13,
    select_2,
    auto_fill_21,
    auto_fill_22,
):
    sum1 = auto_fill_11 + auto_fill_12 + auto_fill_13
    sum2 = auto_fill_21 + auto_fill_22
    return {
        'select_1': select_1,
        'select_2': select_2,
        'sum1': sum1,
        'sum2': sum2,
        'total': sum1 + sum2,
    }
