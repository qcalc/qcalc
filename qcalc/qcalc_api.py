# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Narrow public API for restricted user calculators."""

from qcore import Qty, base_units, base_dims, unit_desc, prefixes, \
    uname2lmt as unit2lmt, lmt_title as lmt_desc, str_type, \
    lmt2categ as lmt2cat, lmt2ulist, lmt2qlist, find_unit
from qcore import isMeasureUnit as is_unit, isMeasureQuantity as is_qty, read_unit
from qcore import (
    oqfunc, qchar, qcode, qdate, qdict, qdatetime, qemail, qfl, qfile, qfunc, qhide,
    qhidex, qhtml, qin, qimage, qlist, qpage, qread, qregex, qsel2, qtbl, qtc,
    qtc2, qtext, qtexta, qtexte, qtime, qt, qt2, qtx, quom, quom2, quomx,
    qurl, qvstr,
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


def _df_method(name):
    def call(data, *args, **kwargs):
        built = _pd.DataFrame(data)
        if built.size > _DF_MAX_CELLS:
            raise ValueError(f"DataFrame too large ({built.size} cells > {_DF_MAX_CELLS}).")
        target = getattr(built, name)
        return _to_plain(target(*args, **kwargs) if callable(target) else target)

    call.__name__ = name
    return call


class _Df:
    """Flat 'df.sum(data)' namespace exposed to sandboxed calculators."""


for _name in _DF_METHODS:
    setattr(_Df, _name, staticmethod(_df_method(_name)))
del _name

df = _Df()


def qcol(tbl, col):
    """Extract one column from a qtbl {'columns': [...], 'data': [[...], ...]}
    dict as a plain list. `col` may be a column name or a 0-based index."""
    idx = tbl['columns'].index(col) if isinstance(col, str) else col
    return [row[idx] for row in tbl['data']]


def qrow(tbl, row):
    """Extract one row from a qtbl {'columns': [...], 'data': [[...], ...]}
    dict as a plain list, given its 0-based row index."""
    return list(tbl['data'][row])


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
    "np", "df", "qcol", "qrow",
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
