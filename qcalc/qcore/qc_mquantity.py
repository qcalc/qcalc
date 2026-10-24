# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""A compact quantity implementation for qCalc."""

from __future__ import annotations

import re
import numpy as np
import qconst

from qcore.qc_mbase import _base_names
from qcore.qc_munit import _format_power_expression, isMeasureUnit
from qcore.qc_units import find_unit, _unit_table


class MeasureQuantity:
    """Represents a value paired with a compatible unit."""
    _number = re.compile(qconst.NUMBER_PATTERN)

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
                    raise TypeError('Error (MQ): No number found')
                self.value = float(match.group(0))  # not locale.atof: pattern is ASCII digits only, '.' decimal
                self.unit = find_unit(s[len(match.group(0)):])

    def __str__(self):
        return str(self.value) + ' ' + self.unit.name()

    def __repr__(self):
        return self.__class__.__name__ + '(' + repr(self.value) + ',' + repr(self.unit.name()) + ')'

    def _sum(self, other, sign1, sign2):
        # Units with an offset (degC, degF) are points on a scale; zero-offset units (K, degR)
        # act as intervals when combined with them.
        if not isMeasureQuantity(other):
            raise TypeError('Error (MQ): Incompatible types')
        su, ou = self.unit, other.unit
        if not su.is_compatible(ou):
            raise TypeError('Error (MQ): Incompatible units')

        if su.offset == 0 and ou.offset == 0:  # plain scaled units
            return self.__class__(sign1 * self.value + sign2 * other.value * ou.factor / su.factor, su)

        if ou.offset == 0 and sign1 == 1:  # point +/- interval, e.g. 30 degC + 5 K
            return self.__class__(self.value + sign2 * other.value * ou.factor / su.factor, su)

        if su.offset == 0 and sign2 == 1:  # interval + point, or point - interval (via __rsub__)
            return self.__class__(other.value + sign1 * self.value * su.factor / ou.factor, ou)

        if su.offset != 0 and ou.offset != 0:
            if sign1 == sign2:  # point + point: convert then add, so (a + b) / 2 averaging works
                return self.__class__(sign1 * self.value + sign2 * _convert_value(other.value, ou, su), su)
            # point - point is an interval, returned in the zero-offset base unit
            diff = sign1 * su.to_base(self.value) + sign2 * ou.to_base(other.value)
            return self.__class__(diff, su.base_name)

        raise TypeError('Error (MQ): cannot subtract a point from an interval')

    def __add__(self, other):
        return self._sum(other, 1, 1)

    __radd__ = __add__

    def __sub__(self, other):
        return self._sum(other, 1, -1)

    def __rsub__(self, other):
        return self._sum(other, -1, 1)

    def __cmp__(self, other):
        if not isMeasureQuantity(other):
            raise TypeError('Error (MQ): Incompatible types')
        if not self.unit.is_compatible(other.unit):
            raise TypeError('Error (MQ): Incompatible units')
        a = round(self.unit.to_base(self.value), 12)
        b = round(other.unit.to_base(other.value), 12)
        return (a > b) - (a < b)

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def __le__(self, other):
        return self.__cmp__(other) <= 0

    def __eq__(self, other):
        # equal only when compatible and numerically equal in base units; never raises
        # (unlike ordering, == must return False for incompatible units or non-quantities)
        if not isMeasureQuantity(other):
            return False
        return _base_key(self) == _base_key(other)

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(_base_key(self))

    def __gt__(self, other):
        return self.__cmp__(other) > 0

    def __ge__(self, other):
        return self.__cmp__(other) >= 0

    def __mul__(self, other):
        if not isMeasureQuantity(other):
            return self.__class__(self.value * other, self.unit)
        value = self.value * other.value
        unit = self.unit * other.unit
        if unit.is_dimensionless():  # important
            return value * unit.factor
        return self.__class__(value, unit)

    __rmul__ = __mul__

    def __truediv__(self, other):
        if not isMeasureQuantity(other):
            return self.__class__(self.value / other, self.unit)
        value = self.value / other.value
        unit = self.unit / other.unit
        if unit.is_dimensionless():  # important
            return value * unit.factor
        return self.__class__(value, unit)

    def __rtruediv__(self, other):
        if not isMeasureQuantity(other):
            if self.value is None:
                return self.__class__(None, pow(self.unit, -1))
            return self.__class__(other / self.value, pow(self.unit, -1))
        value = other.value / self.value
        unit = other.unit / self.unit
        if unit.is_dimensionless():  # important
            return value * unit.factor
        return self.__class__(value, unit)

    def __pow__(self, other):
        if isMeasureQuantity(other):
            raise TypeError('Error (MQ): Exponents must be dimensionless')
        return self.__class__(pow(self.value, other), pow(self.unit, other))

    def __rpow__(self, other):
        raise TypeError('Error (MQ): Exponents must be dimensionless')

    def __abs__(self):
        return self.__class__(abs(self.value), self.unit)

    def __pos__(self):
        return self

    def __neg__(self):
        return self.__class__(-self.value, self.unit)

    def __bool__(self):
        # a quantity without a value (e.g. '@ft') is empty, like None
        return self.value is not None and self.value != 0

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
        new_value = self.unit.to_base(self.value)
        terms = []
        for i in range(len(_base_names)):
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


def _base_key(q):
    # identity of a quantity: value in zero-offset base units (rounded) plus dimension powers
    value = None if q.value is None else round(q.unit.to_base(q.value), 12)
    return value, tuple(q.unit.powers)


def _round(x):
    if np.greater(x, 0.):
        return np.floor(x)
    return np.ceil(x)


def _convert_value(value, src_unit, target_unit):
    factor, offset = src_unit.conversion_tuple_to(target_unit)
    return (value + offset) * factor
