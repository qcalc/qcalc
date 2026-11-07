# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import dict2options, StdJson


def demo_autofill__info():
    return {
        'schema':
            {
                'select_1': dict2options(StdJson.autofill1, initial="C3"),
                'select_2': dict2options(StdJson.autofill2, initial="z")
            },
        'autofill':
            {
                'select_1': dict2options(StdJson.autofill1data,
                                         fields=['auto_fill_11', 'auto_fill_12', 'auto_fill_13']),
                'select_2': dict2options(StdJson.autofill2data, fields=['auto_fill_21', 'auto_fill_22'])
            },
    }


def demo_autofill(select_1, auto_fill_11, auto_fill_12, auto_fill_13,
                  select_2, auto_fill_21, auto_fill_22):
    sum1 = auto_fill_11 + auto_fill_12 + auto_fill_13
    sum2 = auto_fill_21 + auto_fill_22
    return sum1 + sum2
