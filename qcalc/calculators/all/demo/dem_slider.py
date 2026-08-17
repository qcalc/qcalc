# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import qurl


def demo_jqval__info():
    return {
        'title': 'Slider Input Testing',
        'schema': {
            'x': {'type': 'range', 'attrs': {'step': '1', 'min': '1', 'max': '10'}},
            'y': {'attrs': {'min': '1', 'max': '10'}},
            'z': {'attrs': {'minlength': 3, 'required': 'required'}}
        }
    }


def demo_jqval(x=5, y=10, z='', u: qurl = '', l='3ft'):
    return x, y


def demo_jqval22__info():
    ji = demo_jqval__info()
    # ji['template'] = 'v4.22'
    return ji


def demo_jqval22(x=5, y=10, z='', u: qurl = '', l='3ft'):
    return x, y
