# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import qtexta, qpage, Qty, qtc2, qt2, qtc, qt
import random
from qutil import QThread


def demo_qt0__info():
    return {
        'schema': {
            'x': {'help_text': 'Enter a quantity for x'},
            'y': {'help_text': 'Enter a quantity for y'},
        },
    }


def demo_qt0(x='1 m', y='5 m, 15 cm'):
    x = Qty(x)
    y = Qty(y)
    return x + y


def demo_qt1__info():
    return {
        'schema': {
            'x': {'help_text': 'Enter a quantity x(qt)'},
        },
    }


def demo_qt1(x: qt = '1 m', y: qt = '5 m, 15 cm'):
    x = Qty(x)
    y = Qty(y)
    return x + y

def demo_qt2__info():
    return {
        'schema': {
            'x': {'help_text': 'Enter a quantity x(qtc2)'},
        },
    }

def demo_qt2(x: qtc2 = '1 m', y: qtc2 = '5 m, 15 cm'):
    x = Qty(x)
    y = Qty(y)
    return x + y


def demo_qty__info():
    return {
        'schema': {
            'x': {'help_text': 'Enter a quantity x(qtc2)'},
            'y': {'help_text': 'Enter a quantity y(qt2)'},
            'z': {'help_text': 'Enter a quantity z(qtc2)'},
            't': {'help_text': 'Enter a quantity t(qtc)'},
            'w': {'help_text': 'Enter a quantity w(qt)'},
            'xyz': {'help_text': 'Enter a quantity xyz'},
        },
    }


def demo_qty(x: qtc2 = '1 m', y: qt2 = '9 kg', z: qtc2 = '5 m, 15 cm',
         t: qtc = '3 ft', w: qt = '2 kg, 30 g', xyz='5 ft'):
    x = Qty(x)
    y = Qty(y)
    z = Qty(z)
    t = Qty(t)
    w = Qty(w)
    return x, y, z, t, w


def demo_texta__info():
    return {}


def demo_texta(x: qtexta):
    return x.split('\r\n')


def demo_cur__info():
    return {}


def demo_cur(x='100 INR'):
    return Qty(x)


def demo_label__info():
    return {}


def demo_label(text: qtexta):
    return qpage(text)


def demo_darg__input(_kwargs):
    return {
        'x': random.randint(1, 100),
    }


def demo_darg__info():
    return {
        'title': 'Test dynamic input from callback'
    }


def demo_darg(x):
    return x


def demo_darg1__info():
    return {
        'title': 'Test dynamic input from argument'
    }


def demo_darg1(x=random.randint(1, 100)):
    return x


def demo_tpref__info():
    return {
        'title': 'Test User Preferences from Thread Local Storage'
    }


def demo_tpref():
    return QThread.get_prefs()
