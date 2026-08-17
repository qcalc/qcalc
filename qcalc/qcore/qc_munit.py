# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""A compact unit model used by the qCalc quantity layer."""

from __future__ import annotations
from typing import Dict
from qcore.qc_mbase import _base_categories, _base_names, _conv_names, powers_to_bname_lmt, _prefix_list


def _format_power_expression(items, sort_key=None):
    ordered_items = list(items)
    if sort_key is not None:
        ordered_items = sorted(ordered_items, key=sort_key)

    num_parts = []
    denom_parts = []
    for name, power in ordered_items:
        if power == 0:
            continue
        if power < 0:
            denom_parts.append(_render_power_term(name, -power))
        else:
            num_parts.append(_render_power_term(name, power))

    num = "*".join(num_parts) if num_parts else "1"
    denom = "" if not denom_parts else "/" + "/".join(denom_parts)
    return num + denom


def _render_power_term(name, power):
    if name == "1":
        return "1"
    if power == 1:
        return name
    return f"{name}^{power}"


class MeasureUnit:
    """Represents a unit as a scale factor plus a base-dimension exponent vector."""

    def __init__(self, names, factor, powers, offset=0):
        if names is None:
            self.names: Dict[str, int] = {}
        elif isinstance(names, str):
            self.names = {names: 1}
        else:
            self.names = dict(names)

        self.factor = factor
        self.offset = offset
        self.powers = list(powers)
        # deb@19.08.23: base_name, dimension, base_qty, category
        # ft/s^2, L T-2, 0.3048 m/s^2, Acceleration
        self.base_name, self.dimension = powers_to_bname_lmt(self.powers, _base_names)
        self.conv_name, self.dimension = powers_to_bname_lmt(self.powers, _conv_names)
        self.base_qty = f"{self.factor} {self.base_name}"
        self.category = _base_categories.get(self.dimension, "")

    def __str__(self):
        return f"{self.factor} {self.base_name}"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.factor!r}, {self.name()!r})"

    def __eq__(self, other):
        if not isMeasureUnit(other):
            return NotImplemented
        return self.powers == other.powers and self.factor == other.factor and self.offset == other.offset

    def __lt__(self, other):
        if not isMeasureUnit(other):
            return NotImplemented
        if self.powers != other.powers:
            raise TypeError("Error (MU): Incompatible units")
        return self.factor < other.factor

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        if not isMeasureUnit(other):
            return NotImplemented
        if self.powers != other.powers:
            raise TypeError("Error (MU): Incompatible units")
        return self.factor > other.factor

    def __ge__(self, other):
        return self > other or self == other

    def __mul__(self, other):
        if self.offset != 0 or (isMeasureUnit(other) and other.offset != 0):
            raise TypeError("Error (MU): cannot multiply units with non-zero offset")
        if isMeasureUnit(other):
            return MeasureUnit(
                self._combine_names(other, 1),
                self.factor * other.factor,
                [a + b for a, b in zip(self.powers, other.powers)],
            )
        return MeasureUnit(self.names, self.factor * other, self.powers, self.offset * other)

    __rmul__ = __mul__

    def __truediv__(self, other):
        if self.offset != 0 or (isMeasureUnit(other) and other.offset != 0):
            raise TypeError("Error (MU): cannot divide units with non-zero offset")
        if isMeasureUnit(other):
            return MeasureUnit(
                self._combine_names(other, -1),
                self.factor / other.factor,
                [a - b for a, b in zip(self.powers, other.powers)],
            )
        return MeasureUnit(self.names, self.factor / other, self.powers)

    def __rtruediv__(self, other):
        if self.offset != 0 or (isMeasureUnit(other) and other.offset != 0):
            raise TypeError("Error (MU): cannot divide units with non-zero offset")
        if isMeasureUnit(other):
            return MeasureUnit(
                other._combine_names(self, -1),
                other.factor / self.factor,
                [a - b for a, b in zip(other.powers, self.powers)],
            )
        return MeasureUnit(self._invert_names(other), other / self.factor, [-value for value in self.powers])

    def __pow__(self, other):
        if self.offset != 0:
            raise TypeError("Error (MU): cannot exponentiate units with non-zero offset")
        if isinstance(other, (int, float)):  # deb@11.08.23
            return MeasureUnit(
                self._scale_names(other),
                pow(self.factor, other),
                [value * other for value in self.powers],
            )
        raise TypeError("Error (MU): Only integer and inverse integer exponents allowed")

    def conversion_factor_to(self, other):
        if self.powers != other.powers:
            raise TypeError("Error (MU): Incompatible units")
        if self.offset != other.offset and self.factor != other.factor:
            raise TypeError(
                f"Error (MU): Unit conversion ({self.name()} to {other.name()}) cannot be expressed as a simple multiplicative factor"
            )
        return self.factor / other.factor

    def conversion_tuple_to(self, other):
        if self.powers != other.powers:
            raise TypeError("Error (MU): Incompatible units")
        factor = self.factor / other.factor
        offset = self.offset - (other.offset * other.factor / self.factor)
        return factor, offset

    def is_compatible(self, other):
        return self.powers == other.powers

    def is_dimensionless(self):
        return not any(self.powers)

    def is_angle(self):
        return self.powers[7] == 1 and sum(self.powers) == 1

    def set_name(self, name):
        self.names = {name: 1}

    def name(self):
        return _format_power_expression(
            self.names.items(),
            sort_key=lambda item: self._name_sort_key(item[0]),
        )

    def _name_sort_key(self, unit_name: str):
        if unit_name in _prefix_list:
            return (0, _prefix_list.index(unit_name))
        if unit_name in _base_names:
            return (1, _base_names.index(unit_name))
        return (2, unit_name)

    def _combine_names(self, other, sign):
        merged = dict(self.names)
        for unit_name, power in other.names.items():
            merged[unit_name] = merged.get(unit_name, 0) + sign * power
        return {k: v for k, v in merged.items() if v != 0}

    def _scale_names(self, other):
        if other == 0:
            return {"1": 1}
        return {k: v * other for k, v in self.names.items()}

    def _invert_names(self, other):
        merged = {str(other): 1}
        for unit_name, power in self.names.items():
            merged[unit_name] = merged.get(unit_name, 0) - power
        return {k: v for k, v in merged.items() if v != 0}


def isMeasureUnit(x):
    return hasattr(x, "factor") and hasattr(x, "powers")
