# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
import pandas as pd

import qconst
from qcore.qc_qty import Qty, str_to_qty
from qcore.mod_anno import is_qtbl
import operator
import pandas as _pd
from .mod_autil import to_plain
from qutil import css2values

# df.<name>(data, ...) builds a DataFrame internally and always returns a
# plain-Python result (see _to_plain) -- no DataFrame-like object is ever
# handed back to sandboxed code, so there's no object to restrict methods on.
_DF_MAX_CELLS = qconst.TABLE_MAX_CELLS  # guard against memory-exhaustion via huge frames
_DF_MAX_COLS = qconst.TABLE_MAX_COLS

# DataFrame methods/properties exposed to sandboxed code.
_DF_METHODS = (
    # Aggregation / statistics
    'sum', 'mean', 'median', 'min', 'max',
    'std', 'var', 'count', 'prod',

    # Shape / structure
    'shape', 'size', 'ndim',

    # Selection / inspection
    'head', 'tail',
    'columns', 'index',

    # Missing values
    'isna', 'notna',

    # Basic descriptive statistics
    'describe',

    # Sorting / filtering
    'sort_values', 'sort_index',

    # Data conversion
    'to_numpy',

    # 'apply' is unsafe
)


def qdf_names():
    """Return the set of safe ``qdf.<method>`` names exposed to calculators."""
    return {f'qdf.{n}' for n in _DF_METHODS}


class _Df:
    """Safe DataFrame facade used by :func:`qdf`.

    A pandas DataFrame is created and kept internal. Public operations always
    return plain Python values so DataFrame objects/method surfaces are never
    exposed directly to sandboxed calculator code.
    """

    def __init__(self, data, columns=None):

        if len(columns) > _DF_MAX_COLS:
            raise ValueError(
                f"DataFrame too large "
                f"({len(columns)} columns > {_DF_MAX_COLS})."
            )

        built = _pd.DataFrame(data, columns=columns)

        if built.size > _DF_MAX_CELLS:
            raise ValueError(
                f"DataFrame too large "
                f"({built.size} cells > {_DF_MAX_CELLS})."
            )

        self.__df = built

    def _call(self, name, *args, **kwargs):
        target = getattr(self.__df, name)

        if callable(target):
            target = target(*args, **kwargs)

        return to_plain(target)

    def _col_values(self, col):
        if isinstance(col, str):
            if col not in self.__df.columns:
                raise KeyError(f"Unknown column: {col}")
            return self.__df[col].tolist()

        if isinstance(col, int):
            if col < 0 or col >= len(self.__df.columns):
                raise IndexError(f"Column index out of range: {col}")
            return self.__df.iloc[:, col].tolist()

        raise TypeError("Column selector must be a column name (str) or index (int)")

    def __getitem__(self, key):
        result = self.__df[key]

        if isinstance(result, _pd.Series):
            return result.tolist()

        if isinstance(result, _pd.DataFrame):
            return {
                "columns": list(result.columns),
                "data": result.to_numpy().tolist(),
            }

        return to_plain(result)

    def __setitem__(self, key, value):
        new_df = self.__df.copy()
        new_df[key] = value

        if new_df.size > _DF_MAX_CELLS:
            raise ValueError(
                f"DataFrame too large "
                f"({new_df.size} cells > {_DF_MAX_CELLS})."
            )

        self.__df = new_df

    def unary(self, col, op):
        if not callable(op):
            raise TypeError("unary() expects a callable operator function")
        return qapply(self._col_values(col), op)

    def binary(self, col1, col2, op):
        if not callable(op):
            raise TypeError("binary() expects a callable operator function")
        return qbinary(self._col_values(col1), self._col_values(col2), op)

    def binop(self, col, values, op):
        if not callable(op):
            raise TypeError("binop() expects a callable operator function")
        return qbinary(self._col_values(col), values, op)

    def to_dict(self):
        return to_plain({
            "columns": list(self.__df.columns),
            "data": self.__df.to_numpy().tolist(),
        })

    def __len__(self):
        return len(self.__df)

    @property
    def columns(self):
        return self._call('columns')

    @property
    def index(self):
        return self._call('index')


def _make_df_method(name):
    def method(self, *args, **kwargs):
        return self._call(name, *args, **kwargs)

    method.__name__ = name
    return method


# 'columns'/'index' are properties above so they read the same way as on a
# pd.DataFrame (no callable-vs-attribute distinction for callers to check).
for _name in _DF_METHODS:
    if _name not in ('columns', 'index'):
        setattr(_Df, _name, _make_df_method(_name))

del _name


def qdf_demo_data():
    return {'columns': ['Name', 'Salary', 'Dob', 'Height'],
            'data': [
                ['Dave', 50000, '1985-07-15', '5.5 ft'],
                ['Mia', 62000, '1990-11-03', '5.4 ft'],
                ['Liam', 71000, '1988-02-21', '6.0 ft'],
                ['Zara', 54000, '1993-09-12', '5.7 ft'],
            ]}


def qdf(tbl):
    """Create a safe DataFrame-like wrapper from a qtbl dictionary.

    Args:
        tbl: qtbl payload with ``'columns'`` and ``'data'`` keys.

    Returns:
        A restricted/safe DataFrame-like API.

    Raises:
        TypeError: If input or qtbl shape members have invalid types.
        ValueError: If qtbl schema is invalid or column names are not unique.
    """
    if not isinstance(tbl, dict):
        raise TypeError("qdf() expects a qtbl dictionary")

    if not is_qtbl(tbl):
        raise ValueError(
            "qdf() expects a qtbl with 'columns' and 'data'"
        )

    columns = tbl["columns"]
    data = tbl["data"]

    if not isinstance(columns, list):
        raise TypeError("qtbl 'columns' must be a list")

    if not isinstance(data, list):
        raise TypeError("qtbl 'data' must be a list")

    if len(set(columns)) != len(columns):
        raise ValueError("qtbl column names must be unique")

    return _Df(data, columns)


def qcol(tbl, col: str | int):
    """Extract one column from qtbl as a plain list.

    Args:
        tbl: qtbl payload.
        col: Column name or 0-based column index.
    """
    idx = tbl['columns'].index(col) if isinstance(col, str) else col
    return [row[idx] for row in tbl['data']]


def qrow(tbl, row: str | int):
    """Extract one row from qtbl as a plain list by 0-based row index."""
    return list(tbl['data'][row])


def qsum(values):
    """Sum values after per-item conversion to calculator-native runtime values.
    Convert numeric/Qty/date/time-like strings to appropriate types before summing.
    Returns ``0`` for empty input.
    """
    values = list(values)

    if not values:
        return 0

    total = qconvert(values[0])

    for value in values[1:]:
        total += qconvert(value)

    return total


def qapply(values, op):
    """Apply a unary operation to converted calculator-native runtime values.

    Convert numeric/Qty/date/time-like strings to appropriate types before
    applying ``op``.
    """
    if not callable(op):
        raise TypeError("qapply() expects a callable operator function")

    if isinstance(values, (list, tuple)):
        return [op(qconvert(x)) for x in values]
    return op(qconvert(values))


def qto_values(a):
    """Convert one value or a sequence to calculator-native runtime values.
    Convert numeric/Qty/date/time-like strings to appropriate types"""
    if isinstance(a, (list, tuple)):
        return [qconvert(x) for x in a]
    return qconvert(a)


def qconvert(x):
    """Convert one input value into calculator-native runtime value.

    Behavior:
    - Non-string values are returned unchanged.
    - Convert numeric/Qty/date/time-like strings to appropriate types
    """
    if not isinstance(x, str):
        return x

    q = str_to_qty(x)
    if q is not None:
        return q

    val, data_type = css2values(x)
    return val[0]


def qbinary(a, b, op):
    """Apply a binary operation element-wise to two values or sequences."""

    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            raise ValueError("Operands must have the same length.")
        return [
            op(qconvert(x), qconvert(y))
            for x, y in zip(a, b)
        ]

    if isinstance(a, (list, tuple)):
        b = qconvert(b)
        return [op(qconvert(x), b) for x in a]

    if isinstance(b, (list, tuple)):
        a = qconvert(a)
        return [op(a, qconvert(y)) for y in b]

    return op(qconvert(a), qconvert(b))


def qadd(a, b):
    """Add two values/quantities or two sequences element-wise.
    Internally convert numeric/Qty/date/time-like strings to appropriate types before performing addition."""
    return qbinary(a, b, operator.add)


def qsub(a, b):
    """Subtract values/quantities or subtract sequences element-wise.
    Internally convert numeric/Qty/date/time-like strings to appropriate types before performing subtraction."""
    return qbinary(a, b, operator.sub)


def qmul(a, b):
    """Multiply values/quantities or multiply sequences element-wise.
    Internally convert numeric/Qty/date/time-like strings to appropriate types before performing multiplication."""
    return qbinary(a, b, operator.mul)


def qdiv(a, b):
    """Divide values/quantities or divide sequences element-wise.
    Internally convert numeric/Qty/date/time-like strings to appropriate types before performing division."""
    return qbinary(a, b, operator.truediv)
