# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from math import pi


def _number_or_none(value):
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def demo_anyof_tabbed__info():
    return {
        'title': 'Tabbed Anyof Demo',
        'interactive': True,
        'layout': 'tb',
        'input_columns': 1,
        'input_blocks': [
            {
                'column': 1,
                'tabs': [
                    {
                        'title': 'Circle Size',
                        'fields': [
                            'radius',
                        ],
                    },
                    {
                        'title': 'Diameter / Notes',
                        'fields': [
                            'diameter',
                            'note',
                        ],
                    },
                ],
            },
        ],
        'anyof': {
            'circle_size': {
                'fields': ['radius', 'diameter'],
            },
        },
        'schema': {
            'radius': {
                'type': 'float',
                'help_text': 'Enter radius; this clears diameter.',
            },
            'diameter': {
                'type': 'float',
                'help_text': 'Enter diameter; this clears radius.',
            },
            'note': {
                'type': 'qtexta',
                'help_text': 'Optional note kept in a separate tab.',
            },
        },
    }


def demo_anyof_tabbed(radius='', diameter='', note=''):
    radius_value = _number_or_none(radius)
    diameter_value = _number_or_none(diameter)

    if radius_value is not None:
        area = pi * radius_value * radius_value
        return {
            'source': 'radius',
            'radius': radius_value,
            'diameter': diameter_value,
            'area': area,
            'note': note,
        }

    if diameter_value is not None:
        area = pi * (diameter_value / 2.0) ** 2
        return {
            'source': 'diameter',
            'radius': radius_value,
            'diameter': diameter_value,
            'area': area,
            'note': note,
        }

    return {
        'source': 'none',
        'radius': radius_value,
        'diameter': diameter_value,
        'area': None,
        'note': note,
    }