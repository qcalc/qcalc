# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
from qcore import SmartCalc


def gas_flow__info():
    return {
        'title': 'Compressed Gas Flow Duration',
    }


def gas_flow(cylinder_size='47.0 l', cylinder_pressure='20.0 MPa',
             usage_pressure='0.45 MPa', gas_flow_rate='600 mlpm'):
    qcyl_size = Qty(cylinder_size)
    usage_volume = qcyl_size * Qty(cylinder_pressure) / Qty(usage_pressure)
    usage_duration = usage_volume / Qty(gas_flow_rate)
    return {
        'Usage Volume': usage_volume.to(qcyl_size.uom),
        'Usage Duration': usage_duration.to('h')
    }


def gas_law__info():
    return {
        'title': 'Gas Law - General Gas Equation',
    }


def gas_law(pressure='@kPa', volume='1.5 m^3', substance='1 mol', temperature='25.0 degC'):
    """
    Calculate Pressure, Volume, Amount of Substance and Temperature of an Ideal Gas.
    Enter any THREE parameters, to calculate the FOURTH one.
    """
    puom = Qty(pressure).uom
    vuom = Qty(volume).uom
    suom = Qty(substance).uom
    tuom = Qty(temperature).uom
    c = SmartGas(pressure=pressure, volume=volume, substance=substance, temperature=temperature)
    n = len(c.params)
    if n != 3:
        raise Exception(f"Error (GL): Expected 3 parameters but received {n}")
    return {'Pressure': c.pressure.to(puom), 'Volume': c.volume.to(vuom),
            'Substance': c.substance.to(suom), 'Temperature': c.temperature.to(tuom)}


class SmartGas(SmartCalc):

    def inferred(self):
        Rg = Qty('1 Rg')  # .val
        stdtemp = self.temperature.to('degK')  # .val
        return {
            "pressure": {
                "volume, substance, temperature":
                    lambda: self.substance * Rg * stdtemp / self.volume,
            },
            "volume": {
                "pressure, substance, temperature":
                    lambda: self.substance * Rg * stdtemp / self.pressure,
            },
            "substance": {
                "pressure, volume, temperature":
                    lambda: self.pressure * self.volume / (Rg * stdtemp),
            },
            "temperature": {
                "pressure, volume, substance":
                    lambda: self.pressure * self.volume / (self.substance * Rg),
            },
        }
