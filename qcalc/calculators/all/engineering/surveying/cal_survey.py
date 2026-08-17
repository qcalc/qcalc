# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, quom2


def rectland__info():
    return {'title': 'Rectangular Land Area'}


def rectland(length='3 ch, 20 link', width='1 ch, 10 link', area_unit: quom2 = 'decimal'):
    length = Qty(length, 'ft')
    width = Qty(width, 'ft')
    area = length * width
    area = area.to(area_unit)
    return {
        'Length': length,
        'Width': width,
        'Area': area
    }
