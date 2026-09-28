# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha


def demo_related_tabbed__info():
    return {
        'title': 'Tabbed Related Demo',
        'interactive': True,
        'layout': 'tb',
        'input_columns': 1,
        'input_blocks': [
            {
                'column': 1,
                'tabs': [
                    {
                        'title': 'Country / Province',
                        'fields': [
                            'country',
                            'province',
                        ],
                    },
                    {
                        'title': 'City / Zip',
                        'fields': [
                            'city',
                            'zip_code',
                        ],
                    },
                ],
            },
        ],
        'related': {
            'address': {
                'fields': {
                    'country': 'Canada',
                    'province': 'Ontario',
                    'city': 'Toronto',
                    'zip_code': 'M5H',
                },
                'relation': {
                    'Canada': {
                        'Ontario': {
                            'Toronto': ['M5H', 'M5J'],
                            'Ottawa': ['K1A', 'K1P'],
                        },
                        'Quebec': {
                            'Montreal': ['H1A', 'H2A'],
                            'Quebec City': ['G1A', 'G2A'],
                        },
                    },
                    'USA': {
                        'California': {
                            'Los Angeles': ['90001', '90002'],
                            'San Diego': ['92101', '92102'],
                        },
                        'New York': {
                            'New York': ['10001', '10002'],
                            'Buffalo': ['14201', '14202'],
                        },
                    },
                },
            },
        },
    }


def demo_related_tabbed(country='Canada', province='Ontario', city='Toronto', zip_code='M5H'):
    return f'Selection: {country}, {province}, {city}, {zip_code}'