# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from math import pi
from qcore import SmartCalc


def circle__info():
    return {
        'title': 'Calculate Area, Circumference, Diameter and Radius of a Circle',
        'calc/images': {'bottom': ['calc/images/circle.jpg']},
        'anyof':
            {
                "1": {'fields': ['radius', 'dia', 'circumference', 'area']}
            },
    }


def circle(radius='10ft', dia='@ft', circumference='@ft', area='@ft**2'):
    """
    Calculate Area, Circumference, Diameter and Radius of a Circle.
    Enter any one parameter.
    """
    c = SmartCircle(radius=radius, dia=dia, circumference=circumference, area=area)
    n = len(c.params)
    if n != 1:
        raise Exception(f"Error (CIR): Expected 1 parameter but received {n}")
    return {'Radius': c.radius, 'Dia': c.dia,
            'Circumference': c.circumference, 'Area': c.area}


class SmartCircle(SmartCalc):

    def inferred(self):
        return {
            "radius": {
                "dia": lambda: self.dia / 2,
                "circumference": lambda: self.circumference / (2 * pi),
                "area": lambda: pow(self.area / pi, 0.5),
            },
            "dia": {
                "radius": lambda: self.radius * 2,
            },
            "circumference": {
                "radius": lambda: 2 * pi * self.radius,
            },
            "area": {
                "radius": lambda: pi * self.radius ** 2,
            },
        }
