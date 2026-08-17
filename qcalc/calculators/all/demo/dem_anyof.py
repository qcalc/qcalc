# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, qfunc


def demo_any__info():
    return {
        'title': 'Anyof Testing',
        'anyof': {'1': {'fields': ['x', 'y', 'z']}},
    }


def demo_any(x='1 ft, 6inch', y='50 kg, 250g, 100 mg', z=120.50, t=12):
    '''any of x,y,z'''
    return x, y, z, t


def demo_any2__info():
    return {
        'title': 'Calling Anyof'
    }


def demo_any2(any: qfunc = demo_any):
    '''any of any--x,any--y,any--z'''
    return any
