# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import dict2options, StdList


def demo_autofill__info():
    return {
        'schema':
            {
                'select_1': dict2options(StdList.autofill1_list, initial="C3"),
                'select_2': dict2options(StdList.autofill2_list, initial="z")
            },
        'autofill':
            {
                'select_1': dict2options(StdList.autofill1data_list,
                                         fields=['auto_fill_11', 'auto_fill_12', 'auto_fill_13']),
                'select_2': dict2options(StdList.autofill2data_list, fields=['auto_fill_21', 'auto_fill_22'])
            },
    }


def demo_autofill(select_1, auto_fill_11, auto_fill_12, auto_fill_13,
                  select_2, auto_fill_21, auto_fill_22):
    sum1 = auto_fill_11 + auto_fill_12 + auto_fill_13
    sum2 = auto_fill_21 + auto_fill_22
    return sum1 + sum2
