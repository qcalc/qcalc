# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import io

import pandas as pd

import qconst
from qutil.mod_url import fetch_url
from .qc_qty import Qty, str_to_qty
from .qf_anno import as_qtable
from .mod_qcutil import df_formatter


def df2qtbl(df):
    """Convert a DataFrame to a qtbl dictionary. Used by backend code to expose DataFrames as qtbls."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df2qdf() expects a DataFrame")
    return ({"columns": list(df.columns), "data": df.to_numpy().tolist()})


def resize_df(df: pd.DataFrame, nrow: int, ncol: int, keep_last_ncol: int = 0) -> pd.DataFrame:
    max_cols = qconst.TABLE_MAX_COLS
    max_cells = qconst.TABLE_MAX_CELLS
    to_be_ncol = max(min(int(ncol), max_cols), 1)
    to_be_nrow = max(min(int(nrow), int(max_cells / to_be_ncol)), 1)
    as_is_nrow = len(df)
    as_is_ncol = len(df.columns) - keep_last_ncol
    add_row = 0
    add_col = 0

    if to_be_nrow > 0:
        add_row = to_be_nrow - as_is_nrow

    if to_be_ncol > 0:
        add_col = to_be_ncol - as_is_ncol

    if add_row > 0:
        # add row
        # https://stackoverflow.com/questions/41764226/append-empty-rows-to-dataframe-in-pandas
        new_row_idx = [r for r in range(as_is_nrow, as_is_nrow + add_row)]
        df = df.reindex(df.index.union(new_row_idx))
        # new cells default to NaN, which na_rep='None' would render as the
        # literal text "None"; blank them out (object dtype avoids a pandas
        # cast warning/error when writing '' into a numeric column)
        df = df.astype(object)
        df.loc[new_row_idx] = df.loc[new_row_idx].fillna('')
    elif add_row < 0:
        # del row
        df = df.drop([r for r in range(as_is_nrow + add_row, as_is_nrow)])

    if add_col > 0:
        # add col
        # https://stackoverflow.com/questions/30926670/add-multiple-empty-columns-to-pandas-dataframe
        cols = [f'C{c}' for c in range(as_is_ncol + 1, as_is_ncol + add_col + 1)]
        df = pd.concat([df, pd.DataFrame(columns=cols)])
        # same as above: keep resized columns blank instead of showing "None"
        df[cols] = df[cols].fillna('')
    elif add_col < 0:
        # del col
        cols = df.columns[[c for c in range(as_is_ncol + add_col, as_is_ncol)]]
        df = df.drop(columns=cols)

    return df


DELIMITER_ALIASES = {
    'tab': '\t', '\\t': '\t',
    'space': ' ', '\\s': ' ',
    'whitespace': r'\s+', '\\ws': r'\s+',
}


def csv2df(buff_or_url, delimiter=',', quoting='1'):
    "Unsecured version of csv2qtbl"
    if quoting == '9':  # remove anyway
        quoting = '1'
        anyway = True
    else:
        anyway = False

    delimiter = DELIMITER_ALIASES.get(delimiter, delimiter)

    if isinstance(buff_or_url, str) and buff_or_url.strip().lower().startswith(('http://', 'https://')):
        # pandas would fetch with urllib's default User-Agent (blocked by Cloudflare) and skip the SSRF/size guards
        buff_or_url = io.BytesIO(fetch_url(buff_or_url.strip()).content)

    if buff_or_url:
        # a regex delimiter (e.g. r'\s+' for "whitespace") needs the python engine
        engine = 'python' if len(delimiter) > 1 else 'c'
        df = pd.read_csv(
            buff_or_url, delimiter=delimiter, quotechar='"', quoting=int(quoting), thousands=',', engine=engine)
        df = df.astype(object)
        df.fillna('', inplace=True)
        # example url: https://raw.githubusercontent.com/npradaschnor/Pima-Indians-Diabetes-Dataset/master/diabetes.csv
    else:
        raise Exception(f'Error (CD): Not a valid CSV format')

    if anyway:
        # claenup qoutes
        # https://stackoverflow.com/questions/72043503/python-pandas-read-csv-quote-issue-impossible-to-separate-data
        df.columns = df.columns.str.replace('"', '')
        for i, col in enumerate(df.columns):
            try:
                df.iloc[:, i] = df.iloc[:, i].str.replace('"', '')
            except:
                pass
    return df


def csv2qtbl(buff_or_url, delimiter=',', quoting='1'):
    """Read CSV input/url and return qtbl ``{'columns': ..., 'data': ...}``."""
    df = csv2df(buff_or_url, delimiter=delimiter, quoting=int(quoting))
    return df2qtbl(df)


def validated_col(cols: list, idx: int, cname: str = '') -> str:
    c = cols[idx] if cname == '' else cname
    if c in cols:
        return c
    else:
        raise Exception(f"Column [{c}] not found in the table")


def cell_count(value) -> int:
    if isinstance(value, pd.DataFrame):
        return value.size

    if isinstance(value, dict) and 'data' in value and 'columns' in value:
        data_rows = value.get('data', [])
        if isinstance(data_rows, list):
            cell_count = 0
            for row in data_rows:
                if isinstance(row, list):
                    cell_count += len(row)
                elif row is not None:
                    cell_count += 1
            return cell_count

    return 0


def df2normalized(df, do_format: bool = False) -> pd.DataFrame:
    """Return an Excel-friendly DataFrame with Qty units moved into headers.

    Each Qty-valued column is converted to its scalar qty values, and the
    column title is renamed as "<column> | <unit>".
    If do_format=True, every cell is string-formatted for UI rendering and
    unitized columns use quantity-aware precision.
    """
    df = as_qtable(df)
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df

    obj_cols = df.select_dtypes(include=['object', 'string']).columns
    if len(obj_cols) == 0 and not do_format:
        return df

    normalized_df = df.copy()
    rename_map = {}

    for col in obj_cols:
        col_unit = ''
        can_convert = True
        has_qty = False
        col_values = normalized_df[col].tolist()
        qty_values = [None] * len(col_values)

        def _to_qty(value):
            if isinstance(value, Qty):
                return value
            if isinstance(value, str):
                return str_to_qty(value.strip())
            return None

        # pre-check all values: convert only when the whole non-empty column is Qty
        # or qty string, and all qty values share one common unit.
        for i, value in enumerate(col_values):
            if value is None:
                continue

            qty_value = _to_qty(value)
            if qty_value is not None:
                qty_values[i] = qty_value
                has_qty = True
                value_unit = str(qty_value.uom).strip()
                if value_unit:
                    if col_unit == '':
                        col_unit = value_unit
                    elif value_unit != col_unit:
                        can_convert = False
                        break
            else:
                can_convert = False
                break

        if not (can_convert and has_qty):
            if do_format:
                normalized_df[col] = normalized_df[col].map(df_formatter)
            continue

        if do_format:
            values = [
                None if value is None else df_formatter(qty_values[i].val, unit_hint=col_unit, val_only=True)
                for i, value in enumerate(col_values)
            ]
        else:
            values = [None if value is None else qty_values[i].val for i, value in enumerate(col_values)]

        normalized_df[col] = values
        if col_unit:
            col_name = str(col)
            suffix = f'{qconst.TBL_UOM_SEP} {col_unit}'
            if not col_name.strip().endswith(suffix):
                rename_map[col] = f'{col_name} {suffix}'

    if rename_map:
        normalized_df = normalized_df.rename(columns=rename_map)

    if do_format:
        obj_cols_set = set(obj_cols)
        for col in normalized_df.columns:
            if col not in obj_cols_set:
                normalized_df[col] = normalized_df[col].map(df_formatter)

    return normalized_df
