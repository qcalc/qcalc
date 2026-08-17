# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty


def gravitational_force__info():
    return {
        'title': 'Calculate Gravitational Force between Two Masses'
    }


def gravitational_force(mass1='5.972e24 kg', mass2='7.348e22 kg', distance='384.4e6 m'):
    # m1: mass of the first object in kg
    # m2: mass of the second object in kg
    # r: distance between the centers of the two masses in meters
    m1 = Qty(mass1)
    m2 = Qty(mass2)
    r = Qty(distance)
    G = Qty('1 Gv')  # 6.67430e-11  # Gravitational constant in m^3 kg^-1 s^-2
    F = G * (m1 * m2) / r ** 2
    return {'Force': F.to('N')}
