# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import operator
from .qc_qty import Qty
from .qd_data import str2val

__all__ = ['QList', 'qconvert']


def qconvert(x):
    """Convert recognizable text into a calculator value.

    Numeric, quantity, date, and time text is converted to the corresponding
    value. Other text is returned with surrounding whitespace removed, and
    non-text input is returned unchanged.
    """
    if not isinstance(x, str):
        return x

    q = Qty.parse(x)
    if q is not None:
        return q

    return str2val(x)


class QList(list):
    """Create a list whose items can be used in calculator expressions.

    Numeric, quantity, date, and time strings are converted when the list is
    created. Operations return a new ``QList`` and leave the original unchanged.
    Apply an operation to every item, or supply another list or tuple of the
    same length to combine corresponding items.

    Examples:
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
