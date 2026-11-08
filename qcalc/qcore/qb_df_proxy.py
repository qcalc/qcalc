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


def qrecords(tbl, cols=None, skip_blank=True, skip_header=True, strip=True):
    """Return table rows as dictionaries.

    Args:
        tbl: qtbl payload.
        cols: Optional selected columns. Defaults to all columns.
        skip_blank: Skip rows where all selected fields are blank strings.
        skip_header: Skip duplicated header rows present in table data.
        strip: Trim leading/trailing spaces from string cell values.
    """
    df = qdf(tbl)
    selected = list(cols) if cols is not None else list(df.columns)

    for col in selected:
        if col not in df.columns:
            raise KeyError(f"Unknown column: {col}")

    col_values = [df[col] for col in selected]
    rows = []
    for row in zip(*col_values):
        rec = {}
        for col, val in zip(selected, row):
            if strip and isinstance(val, str):
                val = val.strip()
            rec[col] = val

        if skip_blank and all(str(rec[c]).strip() == '' for c in selected):
            continue

        if skip_header and all(str(rec[c]).strip().lower() == str(c).strip().lower() for c in selected):
            continue

        rows.append(rec)
    return rows


def read_table(
    tbl, tbl_name, cols, casts=None, key=None, value=None, unique=True,
    skip_blank=True, skip_header=True, strip=True):
    """Read a qtbl into normalized row dictionaries with optional casting.

    Args:
        tbl: qtbl payload.
        tbl_name: Human-readable table name used in error messages.
        cols: Required column names to read.
        casts: Optional dict {column_name: callable} to cast cell values.
        key: Optional key field name or list/tuple of field names for dict mapping.
        value: Optional value field name or list/tuple of field names for dict mapping.
        unique: Require unique keys when key/value mapping is requested.
        skip_blank: Skip rows where all selected fields are blank strings.
        skip_header: Skip duplicated header rows present in table data.
        strip: Trim leading/trailing spaces from string cell values.
    """
    try:
        rows = qrecords(tbl, cols=cols, skip_blank=skip_blank, skip_header=skip_header, strip=strip)
    except Exception as e:
        raise ValueError(f'{tbl_name}: {e}') from e

    casts = casts or {}
    out = []
    for i, row in enumerate(rows):
        rec = dict(row)
        for col, caster in casts.items():
            if col not in rec:
                raise KeyError(f'{tbl_name}: Unknown cast column: {col}')
            try:
                rec[col] = caster(rec[col])
            except Exception as e:
                raise ValueError(f'{tbl_name}: Invalid value at row {i + 1}, column {col}: {e}') from e
        out.append(rec)
    if key is None and value is None:
        return out
    if key is None or value is None:
        raise ValueError(f'{tbl_name}: Both key and value must be provided for mapping output.')
    try:
        return qkeymap(out, key=key, value=value, unique=unique)
    except Exception as e:
        raise ValueError(f'{tbl_name}: {e}') from e


def qkeymap(tbl_or_rows, key, value, casts=None, unique=True):
    """Build a dictionary map from records.

    Args:
        tbl_or_rows: qtbl payload or list of row dictionaries.
        key: One field name or list/tuple of field names to compose the map key.
        value: One field name or list/tuple of field names to compose the map value.
        casts: Optional dict of {field: callable} applied before mapping.
        unique: Require unique keys; duplicates raise ValueError.
    """
    key_fields = [key] if isinstance(key, str) else list(key)
    value_fields = [value] if isinstance(value, str) else list(value)
    all_fields = key_fields + value_fields

    if is_qtbl(tbl_or_rows):
        rows = qrecords(tbl_or_rows, cols=all_fields)
    else:
        rows = list(tbl_or_rows)

    casts = casts or {}
    out = {}
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TypeError(f'Row {i + 1} must be a dict.')

        rec = {}
        for field in all_fields:
            if field not in row:
                raise KeyError(f'Row {i + 1} missing field: {field}')
            raw = row[field]
            caster = casts.get(field)
            rec[field] = caster(raw) if caster else raw

        map_key = rec[key_fields[0]] if len(key_fields) == 1 else tuple(rec[k] for k in key_fields)
        map_val = rec[value_fields[0]] if len(value_fields) == 1 else tuple(rec[v] for v in value_fields)

        if unique and map_key in out:
            raise ValueError(f'Duplicate key: {map_key}')
        out[map_key] = map_val
    return out


