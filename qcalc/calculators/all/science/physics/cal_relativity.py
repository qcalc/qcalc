# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, SmartCalc


def emc2__info():
    return {
        'title': "Einstein's Theory of Special relativity",
    }


def emc2(mass='1g', energy='@MWh'):
    muom = Qty(mass).uom
    euom = Qty(energy).uom
    c = SmartRelativity(mass=mass, energy=energy)
    n = len(c.params)
    if n != 1:
        raise Exception(f"Error (EM): Expected 1 parameter but received {n}")
    return {'Energy': c.energy.to(euom), 'Mass': c.mass.to(muom)}


class SmartRelativity(SmartCalc):
    def inferred(self):
        c = Qty('1c')
        c2 = c * c
        return {
            "energy": {
                "mass":
                    lambda: self.mass * c2,
            },
            "mass": {
                "energy":
                    lambda: self.energy / c2,
            },
        }
