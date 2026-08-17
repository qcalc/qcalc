# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calculators.all.others.cal_others import gold
from qcore import qfunc


def demo_exclude__info():
    return {
        'title': 'Test Gold',
        # 'exclude': ['gld--gold_weight_india', 'gld--gold_price']
        # | won't work if the field is part of 'anyof' or 'related'
        'showhide': {
            '__': {'fields': ['gld--gold_weight_intl', 'gld--gold_price']}
        }
    }


def demo_exclude(gld: qfunc = gold):
    return gld
