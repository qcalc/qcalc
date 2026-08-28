# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import inspect

from qcore.mod_anno import *
from calc.mod_mfunc import *
from calc import UCals, QCals
from qutil import command_button, page_link, format_py_code, ensure_info_function, extract_common_prefix, \
    get_functions, pretty_json, addcal_button #cal_link, calurl,


def validate_calculator_defaults(user_code):
    local_dict = QCals.safe_exec(user_code)
    functions = {
        name: function
        for name, function in local_dict.items()
        if inspect.isfunction(function) and not name.endswith('__info')
    }

    if not functions:
        raise ValueError('No calculator function was found.')

    validated = []
    for name, function in functions.items():
        required = [
            parameter.name
            for parameter in inspect.signature(function).parameters.values()
            if parameter.default is inspect.Parameter.empty
            and parameter.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
        ]
        if required:
            raise ValueError(
                f"Cannot validate '{name}': required input(s): {', '.join(required)}."
            )

        try:
            function()
        except Exception as e:
            raise ValueError(f"Default values for '{name}' failed: {e}") from e
        validated.append(name)

    return f"Validation successful: {', '.join(validated)}"


def mycal__command(fkwargs, extra):
    result = ''
    action = extra['args'][0]
    if action == 'syntax':
        user_code = fkwargs['code']
        try:
            _ = QCals.safe_exec(user_code)  # | validate and returns exception if invalid code
            result = 'Syntax check successful'
        except Exception as e:
            result = str(e)
    elif action == 'validate':
        user_code = fkwargs['code']
        try:
            result = validate_calculator_defaults(user_code)
        except Exception as e:
            result = str(e)
    return result


def mycal__modify(arg_name, arg_value, action):
    request = QThread.get_req()  # | not allowd in user's calculators
    uc = UCals()
    if arg_name == 'code' and action == 'load':
        cal_name = request.POST.get('cal_name', '').strip()
        # cal_name = cal_name.split('-')[0]
        if cal_name:
            user_code = uc.get_code(cal_name)
            return user_code or f'{cal_name} not found'
        return 'Enter a calculator name'
    elif arg_name == 'cal_name' and action == 'delete':
        cal_name = arg_value.strip()
        # cal_name = cal_name.split('-')[0]
        if cal_name:
            return uc.del_cal(cal_name)
        return 'Enter a calculator name'
        # | raise Exception(result)
    elif arg_name == 'code' and action == 'format':
        cal_name = request.POST.get('cal_name', '').strip()
        # cal_name = cal_name.split('-')[0]
        user_code = arg_value
        user_code, functions = ensure_info_function(user_code, cal_name)
        user_code = format_py_code(user_code)
        return user_code
    return arg_value


def mycal__input(kwargs):
    uc = UCals()
    user_code = uc.get_code(kwargs.get('cal_name', ''))
    if user_code:
        return {
            'code': user_code
        }
    else:
        return {'cal_name': ''}


def mycal__info():
    return {
        'title': 'Create My Calculator',
        'inserts': {
            'form_top':
                command_button('mycal', 'Load Code', '__modify', kwargs={'code': 'load'}) +
                command_button('mycal', 'Delete Code', '__modify', kwargs={'cal_name': 'delete'}) +
                page_link('/catalog/user/', 'My Catalog', 'btn btnurl', 'icon-tree5'),
            'form_bottom':
                command_button('mycal', 'Check Syntax', '__command', args=['syntax']) +
                command_button('mycal', 'Format Code', '__modify', kwargs={'code': 'format'}) +
                command_button('mycal', 'Validate Input', '__command', args=['validate']),
        },
        'calculate': 'Save',
    }


def mycal(cal_name='', code: qcode = """
def addlen(x='7 ft',y='8 m'):
    z=Qty(x)+Qty(y)
    return z

def addlen__info():
    return {
        'title':'Add Two Lengths'
    }
"""
          ):
    try:
        uc = UCals()
        res = uc.edit_cal(cal_name, code)
        # | clear input memory
        cal_name = extract_common_prefix(get_functions(code))
        # | a calculator can exist with same name either in qcalc or in another user account
        cal_id = f"{cal_name}-{uc.cal_owner}"
        open_button = qhtml(addcal_button(cal_id, f'Open {cal_name}'))
        return {
            'Remarks': res,
            'Open': open_button
        }
    except Exception as e:
        return f'Error (MC): {e}'


def mytree__info():
    return {'title': 'Read My Calculator cache'}


def mytree():
    uc = UCals()
    node = uc.get_tree()
    if node:
        utree_node = node.tree_to_dict()
    else:
        utree_node = {}
    return {
        'data_from_tree': pretty_json(utree_node)  # | simple json dumps
    }
