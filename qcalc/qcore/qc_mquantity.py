# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""A compact quantity implementation for qCalc."""

from __future__ import annotations

import re
from locale import atof
import numpy as np

from qcore.qc_mbase import _base_names
from qcore.qc_munit import _format_power_expression, isMeasureUnit
from qcore.qc_units import find_unit, _unit_table


class MeasureQuantity:
    """Represents a value paired with a compatible unit."""
    _number = re.compile(r"[+-]?[0-9]+(\.[0-9]*)?([eE][+-]?[0-9]+)?")

    def __init__(self, *args):
        if len(args) == 2:
            self.value = args[0]
            if isMeasureUnit(args[1]):
                self.unit = args[1]
            else:
                self.unit = find_unit(args[1])
        elif len(args) == 1 and not isinstance(args[0], str):  # deb@17.11.23, Qty
            self.value = args[0].value
            self.unit = args[0].unit
        else:  # 'value unit' string
            s = args[0].strip()
            if s[0] == '@':  # deb@11.08.23, # is not suitable in API call
                self.value = None
                self.unit = find_unit(s[1:])
            elif s[0:5] == 'None ':  # deb@11.08.23
                self.value = None
                self.unit = find_unit(s[5:])
            else:
                match = self._number.match(s)
                if match is None:
                    raise TypeError('Error (PQ): No number found')
                self.value = atof(match.group(0))
                self.unit = find_unit(s[len(match.group(0)):])

    def __str__(self):
        return str(self.value) + ' ' + self.unit.name()

    def __repr__(self):
        return self.__class__.__name__ + '(' + repr(self.value) + ',' + repr(self.unit.name()) + ')'

    def _sum(self, other, sign1, sign2):
        if not isMeasureQuantity(other):
            raise TypeError('Error (PQ): Incompatible types')
        new_value = sign1 * self.value + sign2 * other.value * other.unit.conversion_factor_to(self.unit)
        return self.__class__(new_value, self.unit)

    def __add__(self, other):
        return self._sum(other, 1, 1)

    __radd__ = __add__

    def __sub__(self, other):
        return self._sum(other, 1, -1)

    def __rsub__(self, other):
        return self._sum(other, -1, 1)

    def __cmp__(self, other):
        diff = self._sum(other, 1, -1)
        return (diff.value > 0) - (diff.value < 0)

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __mul__(self, other):
        if not isMeasureQuantity(other):
            return self.__class__(self.value * other, self.unit)
        value = self.value * other.value
        unit = self.unit * other.unit
        if unit.is_dimensionless(): # important
            return value * unit.factor
        return self.__class__(value, unit)

    __rmul__ = __mul__

    def __truediv__(self, other):
        if not isMeasureQuantity(other):
            return self.__class__(self.value / other, self.unit)
        value = self.value / other.value
        unit = self.unit / other.unit
        if unit.is_dimensionless(): # important
            return value * unit.factor
        return self.__class__(value, unit)

    def __rtruediv__(self, other):
        if not isMeasureQuantity(other):
            if self.value is None:
                return self.__class__(None, pow(self.unit, -1))
            return self.__class__(other / self.value, pow(self.unit, -1))
        value = other.value / self.value
        unit = other.unit / self.unit
        if unit.is_dimensionless(): # important
            return value * unit.factor
        return self.__class__(value, unit)

    def __pow__(self, other):
        if isMeasureQuantity(other):
            raise TypeError('Error (PQ): Exponents must be dimensionless')
        return self.__class__(pow(self.value, other), pow(self.unit, other))

    def __rpow__(self, other):
        raise TypeError('Error (PQ): Exponents must be dimensionless')

    def __abs__(self):
        return self.__class__(abs(self.value), self.unit)

    def __pos__(self):
        return self

    def __neg__(self):
        return self.__class__(-self.value, self.unit)

    def __bool__(self):
        return self.value != 0

    def to(self, unit):
        if isinstance(unit, str):  # deb@04.04.24
            unit = find_unit(unit)
        if self.value is not None:  # deb@13.10.23, 04.04.24
            value = _convert_value(self.value, self.unit, unit)
        else:
            value = None
        return self.__class__(value, unit)  # deb@04.04.24

    def in_units_of(self, *units):
        units = list(map(find_unit, units))
        if len(units) == 1:
            unit = units[0]
            value = _convert_value(self.value, self.unit, unit)
            return self.__class__(value, unit)

        units.sort()
        result = []
        value = self.value
        unit = self.unit
        for i in range(len(units) - 1, -1, -1):
            value = value * unit.conversion_factor_to(units[i])
            if i == 0:
                rounded = value
            else:
                rounded = _round(value)
            result.append(self.__class__(rounded, units[i]))
            value = value - rounded
            unit = units[i]
        return tuple(result)

    def in_base_units(self):
        new_value = self.value * self.unit.factor
        terms = []
        for i in range(9):
            unit = _base_names[i]
            power = self.unit.powers[i]
            if power != 0:
                terms.append((unit, power))

        formatted = _format_power_expression(terms)
        return self.__class__(new_value, formatted)

    def is_compatible(self, unit):
        unit = find_unit(unit)
        return self.unit.is_compatible(unit)

    def sqrt(self):
        return pow(self, 0.5)

    def sin(self):
        if self.unit.is_angle():
            return np.sin(self.value * self.unit.conversion_factor_to(_unit_table['rad']))
        raise TypeError('Error (MQ): Argument of sin must be an angle')

    def cos(self):
        if self.unit.is_angle():
            return np.cos(self.value * self.unit.conversion_factor_to(_unit_table['rad']))
        raise TypeError('Error (MQ): Argument of cos must be an angle')

    def tan(self):
        if self.unit.is_angle():
            return np.tan(self.value * self.unit.conversion_factor_to(_unit_table['rad']))
        raise TypeError('Error (MQ): Argument of tan must be an angle')


def isMeasureQuantity(x):
    return hasattr(x, 'value') and hasattr(x, 'unit')


def _round(x):
    if np.greater(x, 0.):
        return np.floor(x)
    return np.ceil(x)


def _convert_value(value, src_unit, target_unit):
    factor, offset = src_unit.conversion_tuple_to(target_unit)
    return (value + offset) * factor
