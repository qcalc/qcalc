# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil import title_to_variable, replace_words
from qcore import isMeasureQuantity as isPQ


def is_scalar(value):
    return isPQ(value) or isinstance(value, float) or isinstance(value, int) or value is None


def scalar_results(xpr: str, variable: str, var_vals: list):
    # imported lazily: eva -> cal_eva -> "from calc import QCals" would otherwise
    # circular-import back into this module while calc/__init__.py is still loading
    from calculators.all.general.cal_eva import eva

    def filter_scalar(result) -> dict | list | None:
        if is_scalar(result):
            return [result]

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
        code = replace_words(xpr, [variable], str(var_val))
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
        if isPQ(value):
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
