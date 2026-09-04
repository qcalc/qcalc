# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore.qc_qty import Qty, is_str_qty
from qcore.qc_mquantity import isMeasureQuantity as is_qty
import operator
import pandas as _pd
from .mod_autil import to_plain

# df.<name>(data, ...) builds a DataFrame internally and always returns a
# plain-Python result (see _to_plain) -- no DataFrame-like object is ever
# handed back to sandboxed code, so there's no object to restrict methods on.
_DF_MAX_CELLS = 10_000  # guard against memory-exhaustion via huge frames

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
)


def qdf_names():
    return {f'qdf.{n}' for n in _DF_METHODS}


class _Df:
    """
    Safe DataFrame facade.

    A pandas DataFrame is created once and kept entirely inside
    this object. Sandboxed code only receives plain-Python results.
    """

    def __init__(self, data, columns=None):
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


def qdf(tbl):
    """
    Create a safe DataFrame-like object from a qtbl dictionary.

    The pandas DataFrame remains internal and is never returned
    directly to sandboxed code.
    """

    if not isinstance(tbl, dict):
        raise TypeError("qdf() expects a qtbl dictionary")

    if "columns" not in tbl or "data" not in tbl:
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


def qcol(tbl, col):
    """
    Extract one column from a qtbl dictionary as a plain list.

    `col` may be a column name or a 0-based column index.
    """
    idx = tbl['columns'].index(col) if isinstance(col, str) else col
    return [row[idx] for row in tbl['data']]


def qrow(tbl, row):
    """
    Extract one row from a qtbl dictionary as a plain list,
    given its 0-based row index.
    """
    return list(tbl['data'][row])


def qsum(values):
    """Return the sum of quantity values."""
    values = list(values)

    if not values:
        return 0

    total = values[0]

    for value in values[1:]:
        total += Qty(value) if is_qty(value) else value

    return total


def _qbinary(a, b, op):
    """Apply a binary operation element-wise to two values or sequences."""

    def convert(x):
        return Qty(x) if is_str_qty(x) else x

    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            raise ValueError("Operands must have the same length.")
        return [
            op(convert(x), convert(y))
            for x, y in zip(a, b)
        ]

    if isinstance(a, (list, tuple)):
        b = convert(b)
        return [op(convert(x), b) for x in a]

    if isinstance(b, (list, tuple)):
        a = convert(a)
        return [op(a, convert(y)) for y in b]

    return op(convert(a), convert(b))


def qadd(a, b):
    """Subtract two quantities."""
    return _qbinary(a, b, operator.add)


def qsub(a, b):
    """Subtract two quantities."""
    return _qbinary(a, b, operator.sub)


def qmul(a, b):
    """Multiply two quantities."""
    return _qbinary(a, b, operator.mul)


def qdiv(a, b):
    """Divide two quantities."""
    return _qbinary(a, b, operator.truediv)
