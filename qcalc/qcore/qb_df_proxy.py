# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qconst
from .qf_anno import is_qtbl
import pandas as _pd
from qcore.mod_autil import to_plain

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
