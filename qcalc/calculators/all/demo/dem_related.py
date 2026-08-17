# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import list2options, StdList


def demo_related__info():
    return {
        'xschema':
            {
                'country': list2options(StdList.related1_list, initial="Canada"),
            },
        'related':
            {
                'r1': list2options(
                    StdList.related1data_list,
                    fields={
                        'country': '',
                        'state': '',
                        'city': '',
                        'zip_code': ''
                    },
                ),
            },
        # 'template': 'v4.21'
    }


def demo_related(country='Germany', state='Bavaria', city='Munich', zip_code='80333'):
    return f"Selection: {country}, {state}, {city}, {zip_code}"


def demo_autofill__info():
    return {
        'schema':
            {
                'select_1': list2options(StdList.autofill1_list, initial="C3"),
                'select_2': list2options(StdList.autofill2_list, initial="z")
            },
        'autofill':
            {
                'select_1': list2options(StdList.autofill1data_list,
                                         fields=['auto_fill_11', 'auto_fill_12', 'auto_fill_13']),
                'select_2': list2options(StdList.autofill2data_list, fields=['auto_fill_21', 'auto_fill_22'])
            },
        # 'template': 'v4.21'
    }


def demo_autofill(select_1, auto_fill_11, auto_fill_12, auto_fill_13,
             select_2, auto_fill_21, auto_fill_22):
    sum1 = auto_fill_11 + auto_fill_12 + auto_fill_13
    sum2 = auto_fill_21 + auto_fill_22
    return sum1 + sum2


def demo_anyof__info():
    return {
        'title': 'Testing AnyOf',
        'anyof':
            {
                '1': {'fields': ['x', 'y', 'z']},
                '2': {'fields': ['a', 'b']}
            },
        'showhide':
            {
                'x': {'fields': ['c'], 'callback': '@==100'}
            },
        # 'template': 'v4.21',
    }


def demo_anyof(x: int, y: int, z: int, a: int, b: int, c: int):
    return x, y, z, a, b, c
