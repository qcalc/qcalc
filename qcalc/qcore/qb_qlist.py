# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import operator
from .qc_qty import str_to_qty
from .qd_data import str2val

__all__ = ['QList', 'qconvert']


def qconvert(x):
    """Convert one input value into calculator-native runtime value.

    Behavior:
    - Non-string values are returned unchanged.
    - Convert numeric/Qty/date/time-like strings to appropriate types
      (a time string gives ``datetime.time``); other strings are returned stripped
    """
    if not isinstance(x, str):
        return x

    q = str_to_qty(x)
    if q is not None:
        return q

    return str2val(x)


class QList(list):
    """A list of calculator-native values (numbers, quantities, dates, ...).

    Numeric/Qty/date/time-like strings are converted to appropriate types when
    the list is created. Operations return a new ``QList`` and never modify
    the original. Element-wise operations accept another list/tuple of the same
    length or a single value that is applied to every item.

    Example:
        ``QList(['2 m', '30 cm']).sum()``
        ``QList([1, 2]).add(10)``
    """

    def __init__(self, values=()):
        if isinstance(values, (str, bytes, dict)):
            raise TypeError("QList expects a list, tuple or other iterable of values")
        super().__init__(qconvert(x) for x in values)

    def sum(self):
        """Sum the items. Returns ``0`` for an empty list."""
        if not self:
            return 0

        total = self[0]
        for value in self[1:]:
            total = total + value
        return total

    def apply(self, op):
        """Apply a unary function to every item."""
        if not callable(op):
            raise TypeError("apply() expects a callable operator function")
        return QList(op(x) for x in self)

    def binary(self, other, op, reverse=False):
        """Apply ``op(item, other)`` element-wise (``op(other, item)`` if ``reverse``).

        ``other`` is either a list/tuple with the same length or a single value.
        """
        if not callable(op):
            raise TypeError("binary() expects a callable operator function")

        if isinstance(other, (list, tuple)):
            if len(other) != len(self):
                raise ValueError("Operands must have the same length.")
            others = [qconvert(y) for y in other]
        else:
            others = [qconvert(other)] * len(self)

        if reverse:
            return QList(op(y, x) for x, y in zip(self, others))
        return QList(op(x, y) for x, y in zip(self, others))

    def add(self, other):
        """Add a value or a list element-wise."""
        return self.binary(other, operator.add)

    def sub(self, other):
        """Subtract a value or a list element-wise."""
        return self.binary(other, operator.sub)

    def mul(self, other):
        """Multiply by a value or a list element-wise."""
        return self.binary(other, operator.mul)

    def div(self, other):
        """Divide by a value or a list element-wise."""
        return self.binary(other, operator.truediv)
