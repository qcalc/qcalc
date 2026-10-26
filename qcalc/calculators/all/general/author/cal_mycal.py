# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import qcode, qhtml, qinfo, qerror, br
from calc.mod_mfunc import *
from calc import UCals
from qutil import callback_button, page_link, format_py_code, ensure_calculator_info, extract_calculator_name, \
    get_functions, pretty_json, addcal_button

from .mod_mycal_validation import (
    format_calculator_validation_report,
    get_calculator_validation_report,
)


def validate_calculator_code(user_code):
    report = get_calculator_validation_report(user_code)
    message = format_calculator_validation_report(report)
    return qinfo(message) if report['valid'] else qerror(message)


def mycal__command(fkwargs, extra):
    result = ''
    action = extra['args'][0]
    if action == 'validate':
        result = validate_calculator_code(fkwargs['code'])
    return result


def mycal__modify(arg_name, arg_value, action):
    request = QThread.get_req()  # | not allowd in user's calculators
    uc = UCals()
    if arg_name == 'code' and action == 'load':
        cal_name = request.POST.get('cal_name', '').strip()
        if cal_name:
            user_code = uc.get_code(cal_name)
            return user_code or qerror(f'{cal_name} not found')
        return qinfo('Enter a calculator name')
    elif arg_name == 'cal_name' and action == 'delete':
        cal_name = arg_value.strip()
        if cal_name:
            return uc.del_cal(cal_name)
        return qinfo('Enter a calculator name')
        # | raise Exception(result)
    elif arg_name == 'code' and action == 'format':
        cal_name = request.POST.get('cal_name', '').strip()
        user_code = arg_value
        user_code, functions = ensure_calculator_info(user_code, cal_name)
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
        'kins': 'eva, mycal2, infogen, ai_chat, q2cal',
        'tags': 'create calculator, developer, author',
        'inserts': {
            'form_bottom':
                callback_button('mycal', 'Format Code', '__modify', kwargs={'code': 'format'}) +
                callback_button('mycal', 'Validate Code', '__command', args=['validate']) +
                page_link('/catalog/user/', 'My Catalog', 'btn btnurl', 'icon-tree5'),
        },
        'calculate': 'Save',
        'layout': 'tb',
    }


def mycal(cal_name='',
          _cal_buttons=qhtml(br(
              callback_button('mycal2', 'Load Code', '__modify', kwargs={'code': 'load'}) +
              callback_button('mycal2', 'Delete Code', '__modify', kwargs={'cal_name': 'delete'}))),
          code: qcode = """
def addlen(x='7 ft',y='8 m'):
    z=Qty(x)+Qty(y)
    return z.to('m')

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
        cal_name = extract_calculator_name(get_functions(code))
        # | a calculator can exist with same name either in qcalc or in another user account
        cal_id = f"{cal_name}-{uc.cal_owner}"
        open_button = qhtml(addcal_button(cal_id, f'Open {cal_name}'))
        return {
            'Remarks': res,
            'Open': open_button
        }
    except Exception as e:
        return f'Error (MC): {e}'


# def mytree__info():
#     return {'title': 'Read My Calculator cache'}
#
#
# def mytree():
#     uc = UCals()
#     node = uc.get_tree()
#     if node:
#         utree_node = node.tree_to_dict()
#     else:
#         utree_node = {}
#     return {
#         'data_from_tree': pretty_json(utree_node)  # | simple json dumps
#     }
