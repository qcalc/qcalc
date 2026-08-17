# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty


def gold__info():
    return {
        'title': 'Duplicate Gold Calculator Check'
    }


def gold(weight='5 gm', price='79 UNC/gm'):
    total = Qty(weight, 'gm') * Qty(price, 'UNC/gm')
    return {'Total Price': Qty(total, 'UNC')}
#
# def gold(weight=5, price=79):
#     total = weight * price
#     return {'Total Price': total}
