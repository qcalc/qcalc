# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Minimal subset of qCalc units by category.

Source: qcore.qc_units
Goal: keep a compact but representative unit vocabulary for calculators.
"""

from qcore.qc_units import _unit_info

# Compact dictionary keyed by LMT/dimension strings (same style as _unit_tree keys).
# This allows direct filtering by unit.dimension and lmt2ulist(lmt)-style flows.
_units_subset = {
    "0": ["unit", "ea", "pair", "dozen", "pct", "ppm"],  # unitless
    "T": ["s", "sec", "min", "h", "hr", "d", "wk", "mo", "yr", "manhr", "manday", "manmo", "manyr"],  # time and labour
    "L": ["mm", "cm", "m", "km", "inch", "ft", "yd", "mi", "nmi"],  # length
    "L2": ["m2", "sqft", "sqyd", "ha", "acre", "km2"],  # area
    "L3": ["ml", "L", "m3", "floz", "cup", "qt", "us_gal", "gal"],  # volume
    "M": ["kg", "g", "tonne", "lb", "oz", "us_ton", "uk_ton"],  # mass
    "LT-2": ["mps2", "fps2", "g0"],  # acceleration
    "LMT-2": ["N", "kN", "lbf", "kgf"],  # force
    "L2MT-2": ["J", "kJ", "cal", "kcal", "Btu", "Wh", "kWh"],  # energy
    "L2MT-3": ["W", "kW", "MW", "hp"],  # power
    "L-1MT-2": ["Pa", "kPa", "MPa", "bar", "atm", "psi", "torr", "mmHg"],  # pressure
    "P": ["rad", "deg", "rev"],  # angle
    "Θ": ["K", "degC", "degF", "degR"],  # temperature
    "C": ["USD", "EUR", "GBP", "INR", "CNY", "CAD", "AUD", "JPY"],  # currency
    "N": ["mol"],  # amount of substance
    "J": ["cd"],  # luminous intensity
    "S": ["sr"],  # solid angle
    "I": ["A"],  # electric current
    "TI": ["Clm"],  # electric charge
    "L2MT-3I-1": ["V"],  # electric potential
    "L2MT-3I-2": ["ohm"],  # resistance
    "L-2M-1T4I2": ["F"],  # capacitance
    "L2MT-2I-2": ["Hn"],  # inductance
    "L2MT-2I-1": ["Wb"],  # magnetic flux
    "MT-2I-1": ["Ts"],  # magnetic flux density
    "L-2M-1T3I2": ["Si"],  # conductance
}

# Normalized view for fast membership checks during dropdown filtering.
UNITS_SUBSET = {
    lmt.upper(): tuple(units)
    for lmt, units in _units_subset.items()
}


def _normalized_keys(units):
    keys = []
    seen = set()
    for uname in units:
        key = uname.lower()
        if key not in seen:
            keys.append(key)
            seen.add(key)
    return tuple(keys)


UNITS_SUBSET_KEYS = {
    lmt: _normalized_keys(units)
    for lmt, units in UNITS_SUBSET.items()
}
