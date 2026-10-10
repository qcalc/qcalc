# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import re
import numpy as np
import pandas as pd
import datetime

import qconst
from qutil import title_to_variable, replace_variables, replace_parameter_values, QDateTime, css2strs, specified_args
from qcore import as_qtable, is_qtbl, Qty, str_to_qty, df_formatter
from qvars import qc_gpref as gs
from .mod_input_fields import ResultCellsError

_PERCENT = re.compile(r'^\s*([+-]?\d+(?:\.\d*)?|[+-]?\.\d+)\s*%\s*$')


def _cell_value(value):
    """Return a numeric/Qty cell value, converting '8.28%' to 0.0828; None for anything else."""
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bool):
        return None
    if isinstance(value, float) and value != value:
        return None
    if isinstance(value, str):
        match = _PERCENT.match(value)
        return float(match.group(1)) / 100.0 if match else None
    if isinstance(value, (int, float, Qty)):
        return value
    return None


def _unique_names(names):
    seen = {}
    unique = []
    for name in names:
        count = seen.get(name, 0) + 1
        seen[name] = count
        unique.append(name if count == 1 else f'{name} ({count})')
    return unique


def _result_tables(result) -> dict:
    if isinstance(result, pd.DataFrame) or is_qtbl(result):
        return {'Table': result}
    if isinstance(result, dict):
        return {str(key): value for key, value in result.items()
                if isinstance(value, pd.DataFrame) or is_qtbl(value)}
    return {}


_ROW_INDEX = re.compile(r'^\d+(\s*-\s*\d+)?$')


def _select_indexes(display_names, label_lists, valid_rows, part):
    """Row indexes picked by one row part.

    Row numbers, ranges and the display name (unique, e.g. 'Total (2)') address single rows.
    Names and wildcards also match by value in every label column, selecting all rows sharing it.
    """
    negate = part.startswith('~')
    token = part[1:].strip() if negate else part
    if not token:
        return set(valid_rows)
    index_of = {name: i for i, name in enumerate(display_names)}
    hit = {index_of[name] for name in specified_args(display_names, [token], empty_spec='*')}
    if not _ROW_INDEX.match(token):
        for labels in label_lists:
            values = list(dict.fromkeys(label for label in labels if label))
            matched = set(specified_args(values, [token], empty_spec='*'))
            hit.update(i for i, label in enumerate(labels) if label in matched)
    return set(valid_rows) - hit if negate else hit & set(valid_rows)


def _table_cells(table_name, df, row_part, column_part) -> tuple[dict, dict]:
    """Extract the cells of one table as ({'Table: Row[: Column]': value}, {key: [alias keys]})."""
    columns = [str(col) for col in df.columns]
    col_values = [df.iloc[:, j].tolist() for j in range(len(columns))]
    is_value = [any(_cell_value(v) is not None for v in values) for values in col_values]
    value_idx = [j for j, flag in enumerate(is_value) if flag]
    label_idx = [j for j, flag in enumerate(is_value) if not flag]
    if not value_idx:
        return {}, {}

    nrows = len(df)

    def label_of(j, i):
        text = str(col_values[j][i]).strip() if col_values[j][i] is not None else ''
        return '' if text.lower() in ('nan', 'none') else text

    label_lists = [[label_of(j, i) for i in range(nrows)] for j in label_idx]
    if label_lists:
        display = [next((labels[i] for labels in label_lists if labels[i]), '') for i in range(nrows)]
    else:
        display = [str(i + 1) for i in range(nrows)]
    valid_rows = [i for i in range(nrows) if display[i]]

    # blank labels get unique placeholders so index lookups stay one-to-one
    def name_list(labels):
        return _unique_names([labels[i] if labels[i] else f'_blank_{i}' for i in range(nrows)])

    display_names = name_list(display)
    rows = sorted(_select_indexes(display_names, label_lists, valid_rows, row_part)) if row_part else valid_rows

    value_names = _unique_names([columns[j] for j in value_idx])
    picked_cols = specified_args(value_names, [column_part], empty_spec='*') if column_part else value_names
    show_column = len(value_idx) > 1

    cells = {}
    aliases = {}
    for i in rows:
        alt_labels = [labels[i] for labels in label_lists if labels[i] and labels[i] != display[i]]
        for col_name in picked_cols:
            value = _cell_value(col_values[value_idx[value_names.index(col_name)]][i])
            if value is None:
                continue
            suffix = f': {col_name}' if show_column else ''
            key = f'{table_name}: {display_names[i]}{suffix}'
            cells[key] = value
            if alt_labels:
                aliases[key] = [f'{table_name}: {label}{suffix}' for label in alt_labels]
    return cells, aliases


class ResultCells(dict):
    """Result dict whose cell keys can also be referred to by alias (e.g. an acronym) in column filters."""

    def __init__(self, *args, aliases=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.aliases = aliases or {}


def flatten_tables(result, cells_spec: str):
    """Turn tabular results into {'Table: Row[: Column]': value} scalars selected by cells_spec.

    cells_spec is comma separated tokens of the form 'Table[: Row[: Column]]'. Each part is
    resolved with specified_args (name, 1-based index, a-b range, * wildcard, ~ exclusion).
    Rows are matched by any non-value (text) column, e.g. both line item and acronym.
    Non-table entries of a dict result (e.g. scalar values) are kept, followed by the selected
    cells; a cell whose name collides with an existing key gets a ' (2)' style suffix.
    The returned ResultCells also records the other row labels (e.g. acronyms) as aliases of a
    cell's column name. A blank spec, or a result without tables, is returned unchanged.
    """
    tokens = [token for token in css2strs(cells_spec or '') if token]
    tables = _result_tables(result)
    if not tokens or not tables:
        return result

    names = list(tables)
    flat = {}
    flat_aliases = {}
    for token in tokens:
        parts = [part.strip() for part in token.split(':', 2)]
        parts += [''] * (3 - len(parts))
        table_part, row_part, column_part = parts
        for table_name in specified_args(names, [table_part], empty_spec='*'):
            cells, aliases = _table_cells(table_name, as_qtable(tables[table_name]), row_part, column_part)
            flat.update(cells)
            flat_aliases.update(aliases)
        if len(flat) > gs['range_limit']:
            raise ResultCellsError(f"Range limit of {gs['range_limit']} exceeded for result cells")

    merged = ResultCells(
        {key: value for key, value in result.items() if key not in tables} if isinstance(result, dict) else {})
    for key, value in flat.items():
        unique_key, n = key, 1
        while unique_key in merged:
            n += 1
            unique_key = f'{key} ({n})'
        merged[unique_key] = value
        if key in flat_aliases:
            merged.aliases[unique_key] = flat_aliases[key]
    return merged


def is_scalar(value):
    return value is None or isinstance(value, (
        Qty,
        int,
        float,
        QDateTime,
        datetime.datetime,
        datetime.date,
        datetime.time,
    ))


def scalar_results(xpr: str, variable: str, var_vals: list, variation_target: str = 'p', cells: str = ''):
    # imported lazily: eva -> cal_eva -> "from calc import QCals" would otherwise
    # circular-import back into this module while calc/__init__.py is still loading
    # variation target can be 'p' (parameters in a function/calculator) or 'v' (variables in an expression)
    # cells ('Table: Row: Column, ...') picks cells of tabular results as scalar values, see flatten_tables()
    from calculators.all.general import eva

    def filter_scalar(result) -> dict | list | None:
        if is_scalar(result):
            return result

        filtered = []
        if isinstance(result, set) or isinstance(result, tuple) or isinstance(result, list):
            for value in result:
                if is_scalar(value):
                    filtered.append(value)

            return filtered

        if isinstance(result, dict):
            filtered = ResultCells() if isinstance(result, ResultCells) else {}
            for key, value in result.items():
                if is_scalar(value):
                    filtered[key] = value
            if isinstance(result, ResultCells):
                filtered.aliases = {key: names for key, names in result.aliases.items() if key in filtered}
            return filtered

        return None

    failed = 0
    saw_table = False
    last_error = None
    results = []
    xvals = []
    for var_val in var_vals:
        if isinstance(var_val, dict):
            if variation_target == 'p':
                code = replace_parameter_values(xpr, var_val)
            else:  # 'v'
                code = replace_variables(xpr, var_val)
        else:
            if variation_target == 'p':
                code = replace_parameter_values(xpr, {variable: var_val})
            else:  # 'v'
                code = replace_variables(xpr, {variable: str(var_val)})
                # code = replace_words(xpr, [variable], str(var_val))

        try:
            result = eva(code=code)
        except Exception as e:
            failed += 1
            last_error = str(e)
            continue

        if isinstance(result, dict) and set(result) == {'result'} and isinstance(result['result'], str):
            # eva() reports a failed expression as {'result': '<error text>'} instead of raising
            failed += 1
            last_error = result['result']
            continue

        if cells:
            result = flatten_tables(result, cells)
        elif _result_tables(result):
            saw_table = True

        sc = filter_scalar(result)
        if isinstance(sc, (dict, list)) and not sc:
            # every field was filtered out (e.g. the expression errored for this
            # trial but eva() returned an error dict/string instead of raising)
            failed += 1
            continue
        if sc is not None:
            if not isinstance(var_val, dict):
                xvals.append(var_val)
            results.append(sc)
        else:
            raise Exception("No scalar results were produced; check the expression")
    if not results:
        if saw_table:
            raise Exception("No scalar results were produced; the expression returned tables, "
                            "specify [Result Cells] to pick table cells")
        if last_error:
            raise Exception(f"No scalar results were produced; the last trial failed: {last_error}")
        raise Exception("No scalar results were produced; check the expression")
    return results, xvals


def result_values(result):
    # this is short and local data version of q0170_result_to_form_schema()
    # this is to process result and tabulate data for redo()
    # returning ojson_data {} a dict of key, and value
    # and a dict {} of uoms
    ojson_data = {}  # data for form
    ojson_uoms = {}

    def rs_item(arg_name, value):
        name = title_to_variable(arg_name)

        if isinstance(value, Qty):
            ojson_data[name] = value.val
            ojson_uoms[name] = value.uom
        elif isinstance(value, QDateTime):
            ojson_data[name] = value.val
        elif value is None or isinstance(value, (
                int, float, datetime.datetime, datetime.date, datetime.time)):
            ojson_data[name] = value

    def process_result(result, name=''):  # v2
        if isinstance(result, set):
            result = list(result)
        if name == '':
            name = 'result'

        if isinstance(result, tuple) or isinstance(result, list):  # result can be a list or tuple of values/qts
            i = 0
            for value in result:
                process_result(value, name + '_' + str(i + 1))
                i += 1
        elif isinstance(result, dict):  # result can be a dictionary of values or quantities
            i = 0
            for name, value in result.items():
                process_result(value, name)
                i += 1
        else:  # result can be simply a value or quantity
            rs_item(name, result)

    # first scan
    if isinstance(result, dict):  # result can be also a dictionary of result/table/chart
        if 'result' in result.keys():
            rdata = result['result']
            process_result(rdata)
            del result['result']
        if 'table' in result.keys():
            del result['table']
        if 'chart' in result.keys():
            del result['chart']
    process_result(result)  # after removing table and chart from the result dictionary
    return ojson_data, ojson_uoms


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
