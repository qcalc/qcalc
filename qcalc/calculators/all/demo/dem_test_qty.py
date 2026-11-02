# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import qtexta, qpage, Qty, qtc2, qt2, qtc, qt
import random
from qutil import QThread


def demo_qty__info():
    return {
        'title': 'Testing Quantities',
        'desc': 'Demonstrates handling of various quantity types',
        'schema': {
            'x_qt': {'help_inline': 'Enter a quantity (type qt, depending on global settings it behaves like qt2)'},
            'y_qtc': {
                'help_inline': 'Enter a quantity (type qtc, experimental composite field, depending on global settings it behaves like qtc2)', },
            'z_qt2': {'help_inline': 'Enter a quantity (type qt2, recommended)'},
            't_qtc2': {'help_inline': 'Enter a quantity (type qtc2, experimental composite field)'},
            'x2_qt': {'help_inline': 'Enter a quantity (type qt, depending on global settings it behaves like qt2)'},
            'y2_qtc': {
                'help_inline': 'Enter a quantity (type qtc, experimental composite field, depending on global settings it behaves like qtc2)'},
            'z2_qt2': {'help_inline': 'Enter a quantity (type qt2 recommended)'},
            't2_qtc2': {'help_inline': 'Enter a quantity (type qtc2, experimental composite field)'},
            'x3': {'help_inline': 'Enter a quantity (type qt2 by default, recommended)'},
            'y3': {'help_inline': 'Enter a quantity (type qt2 by default, recommended)'},
        },
    }


def demo_qty(x_qt: qt = '1 m', y_qtc: qtc = '9 kg', z_qt2: qt2 = '5 m', t_qtc2: qtc2 = '3 ft',
             x2_qt: qt = '1 m, 30cm', y2_qtc: qtc = '9 kg,250g', z2_qt2: qt2 = '5 m,25cm', t2_qtc2: qtc2 = '3 ft,6inch',
             x3='1 m', y3='9 kg, 300 g'):
    x = Qty(x_qt)
    y = Qty(y_qtc)
    z = Qty(z_qt2)
    t = Qty(t_qtc2)
    x2 = Qty(x2_qt)
    y2 = Qty(y2_qtc)
    z2 = Qty(z2_qt2)
    t2 = Qty(t2_qtc2)
    x3 = Qty(x3)
    y3 = Qty(y3)
    return x, y, z, t, x2, y2, z2, t2, x3, y3


def demo_text2list__info():
    return {
        'title': 'Convert text to list',
        'desc': 'Convert a block of text into a list of lines'
    }


def demo_text2list(x: qtexta):
    return x.split('\r\n')


def demo_darg__input(_ctx):
    return {
        'x': random.randint(1, 100),
    }


def demo_darg__info():
    return {
        'title': 'Test dynamic input from callback',
        'desc': 'Demonstrates dynamic input generation using a __input hook function'
    }


def demo_darg(x):
    return x


def demo_darg1__info():
    return {
        'title': 'Test dynamic input from argument',
        'desc': 'Demonstrates how a default argument does not get re-evaluated each time the function is called',
        'kins': 'darg'
    }


def demo_darg1(x=random.randint(1, 100)):
    return x
