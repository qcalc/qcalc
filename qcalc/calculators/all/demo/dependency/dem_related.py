# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import dict2options, StdList


def demo_related__info():
    return {
        'title': 'Demonstrating related metadata',
        # 'schema': {
        #     'country': {'type': 'choice', 'choices': ['Canada', 'USA']},
        # },
        'related': {
            'address': {
                'fields': {'country': 'Canada', 'province': 'Ontario', 'city': 'Toronto'},
                'relation': {
                    'Canada': {
                        'Ontario': ['Toronto', 'Ottawa'],
                        'Quebec': ['Montreal', 'Quebec City'],
                    },
                    'USA': {'California': ['Los Angeles', 'San Diego']},
                },
            },
        },
    }


def demo_related(country, province, city):
    return f'Selection: {country}, {province}, {city}'


def demo_related2__info():
    return {
        'related':
            {
                'r1': dict2options(
                    StdList.related1data_list,
                    fields={
                        'country': '',
                        'state': '',
                        'city': '',
                        'zip_code': ''
                    },
                ),
            },
    }


def demo_related2(country='Germany', state='Bavaria', city='Munich', zip_code='80333'):
    return f"Selection: {country}, {state}, {city}, {zip_code}"
