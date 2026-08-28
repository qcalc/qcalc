# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Narrow public API for restricted user calculators."""
import operator

from qcore import Qty, base_units, base_dims, unit_desc, prefixes, \
    uname2lmt as unit2lmt, lmt_title as lmt_desc, str_type, \
    lmt2categ as lmt2cat, lmt2ulist, lmt2qlist, find_unit
from qcore import isMeasureUnit as is_unit, isMeasureQuantity as is_qty, read_unit
from qcore import (
    oqfunc, qchar, qcode, qdate, qdict, qdatetime, qemail, qfl, qfile, qfunc, qhide,
    qhidex, qhtml, qin, qimage, qlist, qpage, qread, qregex, qsel2, qtbl, qtc,
    qtc2, qtext, qtexta, qtexte, qtime, qt, qt2, qtx, quom, quom2, quomx,
    qurl, qvstr, is_str_qty
)

from calc.conflicts import minimum
from qutil import QDateTime, iif
from qcore import qx, qxi
import datetime
import numpy as _np
import pandas as _pd


def _to_plain(value):
    """Convert pandas/numpy result types to plain Python so nothing with extra
    methods (eval/query/to_pickle/ctypes/...) ever escapes to sandboxed code."""
    if isinstance(value, (_pd.Series, _pd.DataFrame)):
        return value.to_dict()
    if isinstance(value, _pd.Index):
        return value.tolist()
    if isinstance(value, _np.ndarray):
        return value.tolist()
    if isinstance(value, _np.generic):
        return value.item()
    return value


class _RestrictedProxy:
    """Generic allowlist proxy (currently used by np). `_allowed` maps a
    permitted attribute name to either True (call/read, convert result to
    plain Python) or a nested allowed-dict (call, wrap result in a new proxy
    exposing only those names). Add entries to _NP_ALLOWED below to expose
    more, one name at a time.
    """

    __slots__ = ('_obj', '_allowed')
    _max_cells = 10_000  # guard against memory-exhaustion via huge frames/arrays

    def __init__(self, obj, allowed):
        self._obj = obj
        self._allowed = allowed

    def __getattr__(self, name):
        if name not in self._allowed:
            raise AttributeError(name)
        spec = self._allowed[name]
        value = getattr(self._obj, name)

        def finalize(result):
            if spec is True:
                return _to_plain(result)
            size = getattr(result, 'size', None)
            if size is not None and size > self._max_cells:
                raise ValueError(f"Result too large ({size} cells > {self._max_cells}).")
            return _RestrictedProxy(result, spec)

        if not callable(value):
            return finalize(value)

        def wrapped(*args, **kwargs):
            return finalize(value(*args, **kwargs))

        return wrapped

    def __getitem__(self, key):
        return _to_plain(self._obj[key])

    def __repr__(self):
        return repr(self._obj)


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

        return _to_plain(target)

    def __getitem__(self, key):
        result = self.__df[key]

        if isinstance(result, _pd.Series):
            return result.tolist()

        if isinstance(result, _pd.DataFrame):
            return {
                "columns": list(result.columns),
                "data": result.to_numpy().tolist(),
            }

        return _to_plain(result)

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
        return _to_plain({
            "columns": list(self.__df.columns),
            "data": self.__df.to_numpy().tolist(),
        })

    def __len__(self):
        return len(self.__df)

def _make_df_method(name):
    def method(self, *args, **kwargs):
        return self._call(name, *args, **kwargs)

    method.__name__ = name
    return method


for _name in _DF_METHODS:
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


def qmul(a, b):
    """Multiply two quantities."""
    return _qbinary(a, b, operator.mul)

def qdiv(a, b):
    """Divide two quantities."""
    return _qbinary(a, b, operator.truediv)

def qsub(a, b):
    """Subtract two quantities."""
    return _qbinary(a, b, operator.sub)

_NP_ALLOWED = dict.fromkeys([
    # Array creation
    'array', 'asarray',  # unsafe: 'zeros', 'ones', 'empty', 'full', 'arange', 'linspace'
    # Mathematical functions
    'sqrt', 'abs', 'sign', 'exp', 'log', 'log10', 'log2', 'power',
    # Trigonometric functions
    'sin', 'cos', 'tan', 'arcsin', 'arccos', 'arctan', 'arctan2',
    'degrees', 'radians',
    # Aggregation / statistics
    'sum', 'prod', 'mean', 'average', 'std', 'var', 'min', 'max',
    'amin', 'amax', 'median',
    # Array / matrix operations
    'dot', 'matmul', 'concatenate', 'stack', 'vstack', 'hstack',
    'reshape', 'transpose', 'ravel', 'flatten', 'where', 'clip',
    # Constants
    'pi', 'e',
], True)

np = _RestrictedProxy(_np, _NP_ALLOWED)

pylib_dict = {
    'QDateTime': QDateTime, 'qdt': QDateTime,
    'datetime': datetime.datetime, 'date': datetime.date, 'time': datetime.time,
    'Qty': Qty, 'q': Qty, 'qx': qx, 'qxi': qxi,
    # 'QGeo': QGeo, 'geo': QGeo,
    # 'QCals': QCals, 'call': QCals.addr, 'UCals': UCals, 'QFav': QFav,
    'minimum': minimum,
}  # specials and conflicts

__calonly__ = [
    "oqfunc", "qchar", "qcode", "qdate", "qdict", "qdatetime", "qemail",
    "qfl", "qfile", "qfunc", "qhide", "qhidex", "qhtml", "qin", "qimage", "qlist", "qpage",
    "qread", "qregex", "qsel2", "qtbl", "qtc", "qtc2", "qtext", "qtexta",
    # | qtable (real pd.DataFrame) deliberately excluded: safe_execute()'s AST check
    # | doesn't block attribute calls like .eval()/.query()/.to_pickle() on it - use qtbl instead
    "qtexte", "qtime", "qt", "qt2", "qtx", "quom", "quom2", "quomx", "qurl", "qvstr",
]

# for eva() and console.
__evaonly__ = [
    "is_qty", "is_unit", "base_units", "base_dims", "unit_desc", "prefixes", "unit2lmt",
    "lmt_desc", "str_type", "read_unit", "lmt2cat", "lmt2ulist", "lmt2qlist", "find_unit",
    "iif",
    "np", "qdf", "qcol", "qrow", "qsum", "qmul", "qdiv", "qsub",
    "qlib", "qtypes",  # qlib(), qtypes() are defined below
]


def qlib():
    names = set(pylib_dict) | set(__evaonly__)
    names |= {f'df.{n}' for n in _DF_METHODS}
    names |= {f'np.{n}' for n in _NP_ALLOWED}
    return sorted(names)

def qtypes():
    return sorted(__calonly__)
# for cal()
__all__ = __calonly__ + __evaonly__
