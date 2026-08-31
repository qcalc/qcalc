# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import QPref, QMem
from calc import QData, QTemp, QKeep, QSave, QIO, QRam, QMeta, QMyCal, QFav
from qcore import QScreen, quom, color_schemes, legend_locations, qpretty_json
from qutil import nzs, css2strs, truncate, user_process, command_button, QThread
from qvars import qc_gpref as gs
from calc import list2options, StdList

MIN_EXECUTION_TIMEOUT = 1
MAX_EXECUTION_TIMEOUT = 900


def pref__info():
    return {
        'title': 'User Preferences',
        'schema': {
            'request': {'attrs': {'readonly': True}},
            'theme': list2options(StdList.theme_list, initial="default"),  # {'type': 'choice', 'choices': theme_list},
            'decimal': {'attrs': {'max': '16', 'min': '2'}},
            'qty_decimal': {'attrs': {'max': '16', 'min': '2'}},
            'currency_decimal': {'attrs': {'max': '16', 'min': '2'}},
            # 'initial' spec is also an alternative to dynamic assignment
            'exponent_threshold_min': {'attrs': {'max': '1e-6', 'min': '1e-16'}},
            'exponent_threshold_max': {'attrs': {'max': '1e16', 'min': '1e9'}},
            'memory': {'attrs': {'max': '100', 'min': '0'}},
            'chart_width': {'attrs': {'max': '3000', 'min': '128'}},
            'chart_height': {'attrs': {'max': '3000', 'min': '128'}},
            # 'page_font_size': {'attrs': {'max': '125', 'min': '75'}},
            # 'chart_pie_radius': {'attrs': {'max': '2.0', 'min': '0.2'}},
            'chart_legend': {'type': 'choice', 'choices': legend_locations},
            'chart_color_scheme': {'type': 'select2', 'choices': color_schemes},
            'execution_timeout': {'attrs': {'max': '900.0', 'min': '1.0'}},
        },
        'calculate': 'Save',
        # 'col': ["1-9", "10-17"],
        'col': 2,
        'script':
            """
$(document).ready(function() {
    theme_choice_id = 'id_' + getCid() + '_@theme';
    themeChanger(theme_choice_id);
});
"""
    }


def pref__input(_kwargs):  # alternative to func__info() 'schema':{}'
    # dynamic assignment of arg initials, every time before creation of form
    us = gs.copy()
    us.update(QPref.getp())  # User's Session Defaults
    return {  # pref-02
        # 'request': '__req__',
        'theme': us['theme'],
        'ignore_decimal_format': us['ignore_decimal_format'],
        'decimal': us['decimal'],
        'qty_decimal': us['qty_decimal'],
        'currency_decimal': us['currency_decimal'],
        'thousands_separator': us['thousands_separator'],
        'exponent_threshold_min': us['exponent_threshold_min'],
        'exponent_threshold_max': us['exponent_threshold_max'],
        'defa_currency': us['defa_currency'],  # 'USD',
        'memory': us['memory'],
        'fuzzy_search': us['fuzzy_search'],
        'semantic_search': us['semantic_search'],
        'chart_color_scheme': us['chart_color_scheme'],
        'chart_width': us['chart_width'],
        'chart_height': us['chart_height'],
        # 'page_font_size': us['page_font_size'],
        'chart_legend': us['chart_legend'],
        'strict_assign': us['strict_assign'],
        'execution_timeout': us['execution_timeout'],
    }


def pref(  # pref-03
    # request: qreq,
    theme,
    ignore_decimal_format: bool,
    decimal: int,
    qty_decimal: int,
    currency_decimal: int,
    thousands_separator: bool,
    exponent_threshold_min: float,
    exponent_threshold_max: float,
    defa_currency: quom,
    memory: int,
    fuzzy_search: bool,
    semantic_search: bool,
    chart_color_scheme,
    chart_width: int,
    chart_height: int,
    # page_font_size: int,
    chart_legend,
    strict_assign: bool,
    execution_timeout: int,
):
    try:
        execution_timeout = float(execution_timeout)
    except (TypeError, ValueError):
        execution_timeout = float(gs.get('execution_timeout', 60))
    execution_timeout = max(MIN_EXECUTION_TIMEOUT, min(MAX_EXECUTION_TIMEOUT, execution_timeout))

    # user settings
    us = {  # pref-04
        'theme': theme,
        'ignore_decimal_format': ignore_decimal_format,
        'decimal': decimal,
        'qty_decimal': qty_decimal,
        'currency_decimal': currency_decimal,
        'thousands_separator': thousands_separator,
        'exponent_threshold_min': exponent_threshold_min,
        'exponent_threshold_max': exponent_threshold_max,
        'defa_currency': defa_currency,
        'memory': memory,
        'fuzzy_search': fuzzy_search,
        'semantic_search': semantic_search,
        'chart_color_scheme': chart_color_scheme,
        'chart_width': chart_width,
        'chart_height': chart_height,
        # 'page_font_size': page_font_size,
        'chart_legend': chart_legend,
        'strict_assign': strict_assign,
        'execution_timeout': int(execution_timeout),
    }
    try:
        if memory == 0: QMem.clear()
    except:
        pass

    # save settings to session/db and thread local storage
    QPref.setp(us)
    QThread.set_pref(us)
    return 'Preferences Saved'


def mem__info():
    return {
        'title': 'User Memory',
        'schema': {
            'request': {'attrs': {'readonly': True}},
        },
        'calculate': 'Show'
    }


def mem(functions='', json_format=True, clear_memory=False):
    if clear_memory:
        QMem.clear(functions)

    mem_dict = QMem.getp()
    if nzs(functions) != '' and not clear_memory:
        keylist = css2strs(functions)
        mem_dict = {k: mem_dict.get(k, None) for k in keylist if k in mem_dict}

    bin_cnt = QPref.getp1('memory')
    resp = {'Store Size': bin_cnt}
    if json_format:
        out = QScreen()
        out.write(resp)
        for k, v in mem_dict.items():
            out.write({k: truncate(v, 64)})
            out.write('')
        return out.flush()
    else:
        resp.update(mem_dict)
        return resp

sesn_objs = {'qd': QData, 'qmr': QMem, 'qt': QTemp, 'qk': QKeep, 'qs': QSave, 'qi': QIO, 'qr': QRam,
             'qmy': QMyCal, 'qm': QMeta,
             'qf': QFav
             }

def temp__command(fkwargs, extra):
    result = ''
    action = extra['args'][0]
    if action == 'delete':
        data = fkwargs['data']
        try:
            selected_keys = sesn_objs.keys() if data == 'all' else [data]
            if data == 'qmy+qm':  # delete calculators and directory together
                selected_keys = ['qmy', 'qm']
            for key in selected_keys:
                if key in ['qmy', 'qm', 'qf']:
                    sesn_objs[key].clear_temp()
                else:
                    sesn_objs[key].clear()
            result = 'Selected data object(s) deleted'
        except Exception as e:
            result = str(e)
    return result


def temp__info():
    return {
        'title': 'Your Temporary Data',
        'schema': {
            'data': {
                'type': 'choice',
                'choices': {
                    'qd': 'Your temporary data e.g. rates',  # QData
                    'qmr': 'Your temporary input',  # QMem
                    'qt': 'Your temporary files',  # QTemp
                    'qk': 'Your collected data for aggregation',  # QKeep
                    'qs': 'Your last input/output for saving',  # QSave
                    'qi': 'Your input/output saved for step2',  # QIO
                    'qr': 'Your console variables',  # QRam
                    'qmy+qm': 'Your temporary calculators',  # QMyCal (db)
                    # 'qm': 'Your temporary calculator directory',  # QMeta uc_list, uc_dict, uc_tree
                    'qf': 'Your temporary favorites',  # QFavs (db)
                    'all': 'All your temporary data',  # All
                },
            },
        },
        'calculate': 'Show',
        'inserts': {
            'form_top':
                command_button('temp', 'Delete Data', '__command', args=['delete']),
        }
    }


def temp(data='all'):
    selected_keys = sesn_objs.keys() if data == 'all' else [data]
    if data == 'qmy+qm': # List calculators and directory together
        selected_keys = ['qmy', 'qm']
    out = QScreen()
    out.write(user_process())
    for key in selected_keys:
        sobj = sesn_objs[key]
        out.write('Object: ' + sobj.prefix)
        if key in ['qmy', 'qm', 'qf']:
            temp_dict = sobj.getp_temp()
        else:
            temp_dict = sobj.getp()
        for k, v in temp_dict.items():
            if isinstance(v, dict) and 'file' in v:
                tvf = truncate(v['file'], 64)
                v.update({'file': tvf})
            out.write({k: v})
            out.write('')
    return out.flush()


def pinfo__info():
    return {
        'title': 'Process Information',
        'calculate': 'Show',
    }


def pinfo():
    return user_process()
