# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
import qconst
from .mod_mfunc import q0162_dictify_fargs
from .mod_qcals import QCals
import inspect
from django.conf import settings
from qcore import Qty, complex_input_xpr, complex_input_url
from qutil import fid2help_file, QDateTime
import re
from datetime import date, datetime, time as dt_time
from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def ancestors(page_id, page_type='c'):
    aids = []
    if page_type == 'c':
        node = QCals.calc_root.get_node_by_id(page_id)  # unique id
        if node: aids = node.get_ancestor_ids()
    elif page_type == 'q':
        node = QCals.qty_root.get_node_by_id(page_id)  # unique id
        if node: aids = node.get_ancestor_ids()
    return aids


def get_help_path(func_id, qty=False):
    help_file, help_file_opt = fid2help_file(func_id, qty)  # considers user catalog name and demo function

    def check_help_file(help_file):
        help_path = Path(settings.HELP_FILES_DIR) / help_file
        # | if .html help does not exist check also .md file
        # | if .md file exists then returns it otherwise return the non-existent .html file path
        # | currently .html help file can be edited online by 'super' user
        if not help_path.exists():  # which is a .html file
            help_path_md = help_path.with_suffix('.md')
            help_path = help_path_md if help_path_md.exists() else None
        return help_path

    help_path = check_help_file(help_file)
    if not help_path:
        help_path = check_help_file(help_file_opt)

    # Return the primary HTML path even if it does not exist.
    return help_path or Path(settings.HELP_FILES_DIR) / help_file


def val_de_quote(val):
    val = val.replace('/', '!').replace('"', '%22').replace("'", '%27').replace('+', '%2B')
    return val


def furl_from_json(func_id, json_data, json_data_type):
    # print(json_data)
    json_data_copy = json_data
    furl = f'/calc/{func_id}/'
    args_str = ''
    empties = 0
    for name in json_data_copy:
        val = json_data_copy[name]
        if json_data_type[name] in complex_input_url:
            empties += 1
            return ''
            # continue
        if isinstance(val, (list, tuple)):
            return ''
        elif val == '' or val is None:
            empties += 1
            continue
        else:
            sc_val = scalar_or_none(val, json_data_type[name])
            if sc_val is None:
                empties += 1
                return ''
                # continue
            val = sc_val
        args_str += f'{name}/{val}/'

    furl += args_str
    if empties > 0: furl += '---/'
    return furl


def scalar_or_none(val, jdata_type: str):
    if isinstance(val, int) or isinstance(val, float):
        return val
    elif isinstance(val, str):
        if len(val) < qconst.SCALAR_LENGTH:
            return val_de_quote(val)
        else:
            return None
    elif isinstance(val, (date, datetime, dt_time)):
        return val_de_quote(str(QDateTime(val)))  # can have +
    elif jdata_type in complex_input_xpr:
        return None
    else:
        return val  # bool
    # return None


def fxpr_from_json(func_id, json_data, json_data_type, forced=False):
    # print('j', func_id, json_data, json_data_type)

    # if func_id in ['eva']: #, 'redo', 'compare', 'monte_carlo' has variables inside code]:
    #     # Expression is whatever inside codeedit field
    #     name = 'code' if func_id=='eva' else 'xpr'
    #     return val_de_quote(json_data[name])

    json_data_copy = q0162_dictify_fargs(json_data)
    json_data_type_copy = q0162_dictify_fargs(json_data_type)
    # print('1', json_data_copy)
    # print('2', json_data_type_copy)

    for name in json_data_copy:
        # print('|', name, json_data_copy[name], json_data_type_copy[name])
        val = json_data_copy[name]
        if isinstance(val, (list, tuple)):
            json_data_copy[name] = [
                scalar_or_none(list_val, json_data_type[name])
                for list_val in val
            ]
        elif isinstance(val, pd.DataFrame):
            # json_data_copy[name] = val
            json_data_copy[name] = {
                'columns': [str(col) for col in val.columns],
                'data': val.to_numpy().tolist(),
            }
        elif isinstance(val, dict):
            if qconst.DICT_CLASS_FUNC in val:
                cfname = val.pop(qconst.DICT_CLASS_FUNC)
                cfname_type = json_data_type_copy[name]
                json_data_copy[name] = fxpr_from_json(cfname, val, cfname_type)
                # print('func',json_data_copy[name])
            elif qconst.DICT_CLASS_PLAIN in val:
                cfname = val.pop(qconst.DICT_CLASS_PLAIN)
                cfname_type = json_data_type_copy[name]
                json_data_copy[name] = fxpr_from_json(cfname, val, cfname_type)
            # else:
            #     json_data_copy[name] = _plain_fxpr_value(val)
        elif json_data_type[name] in complex_input_xpr:
            return ''
            json_data_copy[name] = None
        elif val is None:
            json_data_copy[name] = None
        else:
            sc_val = scalar_or_none(val, json_data_type[name])
            if sc_val is None:
                return ''
            json_data_copy[name] = sc_val

    json_data_copy = {k: v for k, v in json_data_copy.items()}  # if v is not None}
    func_call_str = json_to_func_call(func_id, json_data_copy)
    return func_call_str


def is_function_call(call_str):
    """
    Check if a string is a valid function call, possibly with nested function calls.
    - Starts with a valid identifier (function name).
    - Has balanced parentheses.
    """
    # Ensure the string starts with a valid function name
    if not re.match(r'^[a-zA-Z_]\w*\(.*\)$', call_str):
        return False

    # Check if parentheses are balanced to allow for nested calls
    paren_count = 0
    for char in call_str:
        if char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1
        if paren_count < 0:  # More closing than opening
            return False

    return paren_count == 0  # Must end with balanced parentheses


def json_to_func_call(func_id, json_var):
    # print('3', func_name, json_var)
    # List of key-value pairs to transform into arguments
    args_list = []

    for key, value in json_var.items():
        # Convert lists to strings with brackets, otherwise use str(value)
        if isinstance(value, str) and is_function_call(value):
            value_str = value  # Use the function call directly
        elif isinstance(value, list):
            value_str = f"[{', '.join(map(repr, value))}]"
        else:
            value_str = repr(value)  # Use repr to ensure proper string formatting

        # Append key=value format
        args_list.append(f"{key}={value_str}")

    # Join all arguments with a comma
    args_str = ", ".join(args_list)

    # Form the final function call string
    if '-' not in func_id and not func_id.startswith('demo_'):
        func_call_str = f"{func_id}({args_str})"
    else:
        func_call_str = f"call('{func_id}')({args_str})"

    return func_call_str


def xpr2loop(xpr: str):
    return xpr + "/varx_start/1/varx_stop/1/varx_step/1/step_round/2"


# def xpr2loop(func_id, xpr:str):
#     if func_id in ['redo','compare','monte_carlo']:
#         return ''
#     if func_id in ['eva']:
#         xpr = xpr.replace(f"eva(code=", '')[:-2]
#     return xpr + "/varx_start/1/varx_stop/1/varx_step/1/step_round/2"

def get_fhelp(func_id, __info):
    func_help = ''
    # | start callback point __help (q1, mod_cutil.py, line 117)
    # | func__help([__info])
    # | get additional help text if any, will be printed after static help text inside help window
    fhelp = QCals.addr(func_id + '__help')
    if fhelp is not None:
        args_count = len(inspect.signature(fhelp).parameters)

        if args_count == 0:
            func_help = fhelp()
        elif args_count == 1:
            func_help = fhelp(__info)
    # | end of exit point
    return func_help


def valid_numq(val, is_print=False):
    if isinstance(val, (float, int)):
        return val
    elif isinstance(val, Qty):
        return str(val) if is_print else val
    elif isinstance(val, str):
        try:
            return float(val.replace(',', ''))
        except ValueError:
            pass

        try:
            q = Qty(val)
            return str(q) if is_print else q
        except:
            pass

    elif isinstance(val, list):
        return [valid_numq(item, is_print) for item in val] if val else val

    return None


def keep_format(result):
    to_be_kept = {}
    if not isinstance(result, dict):
        result = {"Result": result}
    for key, val in result.items():
        v = valid_numq(val, True)
        if v:
            to_be_kept[key] = v
    return to_be_kept


def _test():
    # Example usage
    json_var = {
        'quantity': 'L',
        'mode': 'u2u',
        'value': '1.0',
        'from_unit': ['femtom', 'ft'],
        'from_qty': 'l_earth_moon',
        'to_units': ['lyr', 'm'],
        'to_qty': '',
        'unit_cost': 'None UNC!ft'
    }
    print(json_to_func_call('conv2', json_var))
    json_var = {
        'land_image': "image_reader(image_url='http:!!127.0.0.1:8000!static!demo!irg_land.jpg', show_exif_tags=False)"}
    print(json_to_func_call('irg_landimg', json_var))


if __name__ == '__main__':
    _test()
