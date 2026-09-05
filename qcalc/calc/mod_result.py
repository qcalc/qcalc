# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil import title_to_variable
from qcore import isMeasureQuantity as isPQ
import pandas as pd


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
        elif isinstance(value, pd.DataFrame):
            pass
        elif str(type(value)).lower().find('chart') > -1:
            pass
        else:
            ojson_data[name] = value
        return

    def process_result(result, name=''):  # v2
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
