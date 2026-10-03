# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import qconst
from qutil import title_to_variable, replace_variables, replace_parameter_values
from qcore import as_qtable, Qty, str_to_qty, df_formatter


def is_scalar(value):
    return isinstance(value, Qty) or isinstance(value, float) or isinstance(value, int) or value is None


def scalar_results(xpr: str, variable: str, var_vals: list, variation_target: str = 'p'):
    # imported lazily: eva -> cal_eva -> "from calc import QCals" would otherwise
    # circular-import back into this module while calc/__init__.py is still loading
    # variation target can be 'p' (parameters in a function/calculator) or 'v' (variables in an expression)
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
            filtered = {}
            for key, value in result.items():
                if is_scalar(value):
                    filtered[key] = value
            return filtered

        return None

    failed = 0
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
        except Exception:
            failed += 1
            continue

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
            raise Exception("No numeric results were produced; check the expression")
    if not results:
        raise Exception("No numeric results were produced; check the expression")
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
        elif (
            isinstance(value, float) or
            isinstance(value, int)
        ):
            ojson_data[name] = value
        elif value is None:
            ojson_data[name] = None
        else:
            pass
        return

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


def df2unit_normalized(df, do_format: bool = False) -> pd.DataFrame:
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
