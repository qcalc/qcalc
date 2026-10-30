# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from calc import QPref, QMem
from calc import QData, QTemp, QKeep, QSave, QIO, QRam, QMeta, QMyCal, QFav, QOpenAIChat, QMyCalAI
from calc.mod_credentials import (
    provider_choices,
    has_user_api_key,
    get_user_api_key_suffix,
    has_system_api_key,
    set_user_api_key,
    delete_user_api_key,
)
from calc.mod_api_keys import ApiKeyError, create_api_key, list_api_keys, revoke_api_key, delete_api_key
from calc.mod_api_quota import api_limits, key_usage
from django.conf import settings
import logging
import qconst
from qcore import QScreen, quom, color_schemes, legend_locations, qtext, qinfo, qwarn
from qutil import nzs, css2strs, truncate, user_process, callback_button, QThread, is_loggedin, addcal_button, qaddr
from qvars import qc_gpref as gs
from calc import (
    OPENAI_MODEL_CHOICES,
    dict2options,
    StdList,
    normalize_openai_model,
)

MIN_EXECUTION_TIMEOUT = 1
MAX_EXECUTION_TIMEOUT = 900

logger = logging.getLogger(__name__)


def _normalize_theme(theme_name, fallback='default'):
    choices = StdList.theme_list.get('choices', []) if isinstance(StdList.theme_list, dict) else []
    if choices and theme_name not in choices:
        return fallback
    return theme_name


def pref__info():
    general_options = 'interactive, slider, layout, calc_per_row, uom_subset_enabled, memory, strict_*'
    number_options = 'ignore_decimal_format, decimal, *_decimal, thousands_separator, exponent_*'
    chart_options = 'chart_*'
    other_options = 'theme, defa_currency, execution_timeout, xpr_max_table_cells, remember_file_kb, openai_model'
    pane1 = {'title': 'General', 'fields': general_options}
    pane2 = {'title': 'Number', 'fields': number_options}
    pane3 = {'title': 'Chart', 'fields': chart_options}
    pane4 = {'title': 'Others', 'fields': other_options}
    input_blocks = [
        {
            'column': 1,
            'tabs': [pane1, pane2, pane3, pane4],
        }
    ]
    return {
        'title': 'User Preferences',
        'kins': 'api_keys',
        'tags': 'cache',
        'schema': {
            # 'request': {'attrs': {'readonly': True}},
            'theme': {
                **dict2options(StdList.theme_list, initial="default"),  # {'type': 'choice', 'choices': theme_list},
                'help_text': 'Select qCalc look and feel from the available theme list.',
            },
            'interactive': {
                'help_text': 'Enable or disable interactive mode when a calculator supports. When enabled, calculations are triggered automatically whenever an input changes.',
            },
            'slider': {
                'help_text': 'Show a slider under the focused numeric input to adjust its value by dragging. It can also be switched on or off for a single calculator from its menu.',
            },
            'layout': {
                'help_text': 'Select default layout',
                'type': 'choice', 'choices': {'lr': 'Left/Right Layout', 'tb': 'Top/Bottom Layout'},
            },
            'calc_per_row': {
                'attrs': {'max': '6', 'min': '0'},
                'help_text': 'Maximum number of calculators in a row from 1 to 6; 0 for no cap. Fewer are shown when the screen is narrow. Takes effect after page reload.',
            },
            'ignore_decimal_format': {
                'help_text': 'Ignore decimal format specified below when displaying numbers.',
            },
            'decimal': {
                'attrs': {'max': '16', 'min': '2'},
                'help_text': 'Number precision from 2 to 16.',
            },
            'qty_decimal': {
                'attrs': {'max': '16', 'min': '2'},
                'help_text': 'Quantity precision from 2 to 16.',
            },
            'currency_decimal': {
                'attrs': {'max': '16', 'min': '2'},
                'help_text': 'Currency precision from 2 to 16.',
            },
            # 'initial' spec is also an alternative to dynamic assignment
            'exponent_threshold_min': {
                'attrs': {'max': '1e-6', 'min': '1e-16'},
                'help_text': 'Lower bound for switching to scientific notation, from 1e-16 to 1e-6.',
            },
            'exponent_threshold_max': {
                'attrs': {'max': '1e16', 'min': '1e9'},
                'help_text': 'Upper bound for switching to scientific notation, from 1e9 to 1e16.',
            },
            'defa_currency': {
                'help_text': 'Currency code used as the default currency.',
            },
            'uom_subset_enabled': {
                'help_text': 'Use compact unit subsets for unit dropdowns.',
            },
            'memory': {
                'attrs': {'max': '100', 'min': '0'},
                'help_text': 'Number of calculator input data items to keep in memory from 0 to 100; set 0 to clear stored data.',
            },
            'chart_width': {
                'attrs': {'max': '3000', 'min': '128'},
                'help_text': 'Chart width in pixels from 128 to 3000.',
            },
            'chart_height': {
                'attrs': {'max': '3000', 'min': '128'},
                'help_text': 'Chart height in pixels from 128 to 3000.',
            },
            'chart_legend': {
                'type': 'choice',
                'choices': legend_locations,
                'help_text': 'Choose one of the available chart legend locations.',
            },
            'chart_color_scheme': {
                'type': 'select2',
                'choices': color_schemes,
                'help_text': 'Choose one of the available chart color schemes.',
            },
            'strict_assign': {
                'help_text': 'Reject console assignments that do not match known symbol names.',
            },
            'strict_table_input': {
                'help_text': 'Reject input table columns that are not required by the calculator.',
            },
            'execution_timeout': {
                'attrs': {'max': MAX_EXECUTION_TIMEOUT, 'min': MIN_EXECUTION_TIMEOUT},
                'help_text': f'Calculator execution timeout in seconds from {MIN_EXECUTION_TIMEOUT} to {MAX_EXECUTION_TIMEOUT}.',
            },
            'xpr_max_table_cells': {
                'attrs': {'max': '10000', 'min': '0'},
                'help_text': 'Maximum number of table cells expression building can continue with, from 0 to 10000.',
            },
            'remember_file_kb': {
                'attrs': {'max': str(qconst.REMEMBER_FILE_KB_MAX), 'min': '0'},
                'help_text': f'Largest uploaded file in KB that is remembered as calculator input, '
                             f'from 0 to {str(qconst.REMEMBER_FILE_KB_MAX)}; 0 never remembers files. '
                             f'Larger files must be selected again.',
            },
            'openai_model': {
                'type': 'select2',
                'choices': OPENAI_MODEL_CHOICES,
                'help_text': 'Select the OpenAI model ID used by AI features, e.g. in mycal, mycal2, ai_chat, etc.',
            },
        },
        'calculate': 'Save',
        'layout': 'tb',
        'input_columns': 1,
        'input_blocks': input_blocks,
        'script':
            """
            $(document).ready(function() {
                theme_choice_id = QCALC_TOK_ID_PREFIX + getCid() + '_@theme';
                themeChanger(theme_choice_id);
            });
            """,
        'inserts': {
            'form_bottom': addcal_button('api_keys', 'Personal API Keys'),
        },
    }


def pref__input(_kwargs):  # alternative to func__info() 'schema':{}'
    # dynamic assignment of arg initials, every time before creation of form
    us = gs.copy()
    req = QThread.get_req()
    if req.recall:  # if refresh button is clicked, recall will False
        us.update(QPref.getp())  # User's Session Defaults
    us['theme'] = _normalize_theme(us.get('theme', 'default'))
    return {  # pref-02
        # 'request': '__req__',
        'theme': us['theme'],
        'interactive': us['interactive'],
        'slider': us['slider'],
        'layout': us['layout'],
        'calc_per_row': us['calc_per_row'],
        'ignore_decimal_format': us['ignore_decimal_format'],
        'decimal': us['decimal'],
        'qty_decimal': us['qty_decimal'],
        'currency_decimal': us['currency_decimal'],
        'thousands_separator': us['thousands_separator'],
        'exponent_threshold_min': us['exponent_threshold_min'],
        'exponent_threshold_max': us['exponent_threshold_max'],
        'defa_currency': us['defa_currency'],  # 'USD',
        'uom_subset_enabled': us['uom_subset_enabled'],
        'memory': us['memory'],
        'chart_color_scheme': us['chart_color_scheme'],
        'chart_width': us['chart_width'],
        'chart_height': us['chart_height'],
        # 'page_font_size': us['page_font_size'],
        'chart_legend': us['chart_legend'],
        'strict_assign': us['strict_assign'],
        'strict_table_input': us['strict_table_input'],
        'execution_timeout': us['execution_timeout'],
        'xpr_max_table_cells': us['xpr_max_table_cells'],
        'remember_file_kb': us['remember_file_kb'],
        'openai_model': us['openai_model'],
    }


def pref(  # pref-03
    theme,
    interactive: bool,
    slider: bool,
    layout,
    calc_per_row: int,
    ignore_decimal_format: bool,
    decimal: int,
    qty_decimal: int,
    currency_decimal: int,
    thousands_separator: bool,
    exponent_threshold_min: float,
    exponent_threshold_max: float,
    defa_currency: quom,
    uom_subset_enabled: bool,
    memory: int,
    chart_color_scheme,
    chart_width: int,
    chart_height: int,
    # page_font_size: int,
    chart_legend,
    strict_assign: bool,
    strict_table_input: bool,
    execution_timeout: int,
    xpr_max_table_cells: int,
    remember_file_kb: int,
    openai_model,
):
    theme = _normalize_theme(theme)
    openai_model = normalize_openai_model(openai_model)
    # user settings
    us = {  # pref-04
        'theme': theme,
        'interactive': interactive,
        'slider': slider,
        'layout': layout,
        'calc_per_row': max(0, min(int(calc_per_row), 6)),
        'ignore_decimal_format': ignore_decimal_format,
        'decimal': decimal,
        'qty_decimal': qty_decimal,
        'currency_decimal': currency_decimal,
        'thousands_separator': thousands_separator,
        'exponent_threshold_min': exponent_threshold_min,
        'exponent_threshold_max': exponent_threshold_max,
        'defa_currency': defa_currency,
        'uom_subset_enabled': uom_subset_enabled,
        'memory': memory,
        'chart_color_scheme': chart_color_scheme,
        'chart_width': chart_width,
        'chart_height': chart_height,
        # 'page_font_size': page_font_size,
        'chart_legend': chart_legend,
        'strict_assign': strict_assign,
        'strict_table_input': strict_table_input,
        'execution_timeout': int(execution_timeout),
        'xpr_max_table_cells': xpr_max_table_cells,
        'remember_file_kb': max(0, min(int(remember_file_kb), qconst.REMEMBER_FILE_KB_MAX)),
        'openai_model': openai_model,
    }
    try:
        if memory == 0: QMem.clear()
    except:
        pass

    # save settings to session/db and thread local storage
    QPref.setp(us)
    QThread.set_pref(us)
    return qinfo('Preferences Saved')


def api_keys__info():
    return {
        'title': 'Personal API Keys for External Providers',
        'desc': 'Save your personal provider API keys securely.',
        'kins': 'pref, ai_chat, mycal2',
        'tags': 'ai, preferences',
        'remember': False,
        'schema': {
            'action': {
                'type': 'choice',
                'choices': {
                    'status': 'Show status',
                    'activate': 'Activate personal keys',
                    'inactivate': 'Inactivate personal keys',
                    'set': 'Set / Replace key',
                    'delete': 'Delete key',
                },
            },
            'provider': {
                'type': 'choice',
                'choices': provider_choices(),
                'help_text': 'Select the provider for this key.',
            },
            'api_key': {
                'help_text': 'Paste a new API key only when using "Set / Replace key"; it will be encrypted before storage.',
                'attrs': {'autocomplete': 'off'},
            },
        },
        'showhide': {
            'action': {'fields': ['provider', 'api_key'], 'callback': 'show_action_fields'}
        },
        'script':
            """
            function show_action_fields(v){
                return [v !== 'activate' && v !== 'inactivate', v === 'set'];
            }
            """,
        'calculate': 'Apply',
    }


def api_keys__input(_kwargs):
    return {
        'api_key': '',
    }


def api_keys(action='status', provider='openai', api_key: qtext = ''):
    req = QThread.get_req()
    if not is_loggedin(req):
        raise Exception('Please login to manage personal API keys')

    personal_api_keys_active = QPref.getp1('personal_api_keys_active', True)
    if action == 'activate':
        personal_api_keys_active = True
        QPref.setp1('personal_api_keys_active', True)
    elif action == 'inactivate':
        personal_api_keys_active = False
        QPref.setp1('personal_api_keys_active', False)

    if action == 'set':
        set_user_api_key(req.user, provider, api_key)
    elif action == 'delete':
        delete_user_api_key(req.user, provider)
    elif action not in ['status', 'activate', 'inactivate']:
        raise Exception(f'Unsupported action: {action}')

    resp = {
        'Personal API Keys Active': 'Yes' if personal_api_keys_active else 'No',
    }
    if action in ['status', 'set', 'delete']:
        personal_key_status = 'Not configured'
        if has_user_api_key(req.user, provider):
            key_suffix4 = get_user_api_key_suffix(req.user, provider)
            if key_suffix4 != '':
                personal_key_status = f'Configured (…{key_suffix4})'
            else:
                personal_key_status = 'Configured'
        resp.update({
            'Provider': provider,
            'Personal Key': personal_key_status,
            'System Fallback': 'Configured' if has_system_api_key(provider) else 'Not configured',
        })
    return resp


def api_access__info():
    return {
        'title': 'Personal API Keys for qCalc',
        'desc': 'Create and manage keys for calling qCalc calculators from your own scripts and apps.',
        'kins': 'api_keys, pref',
        'tags': 'api, account',
        'remember': False,
        'layout': 'tb',
        'xpr': False,
        'url': False,
        'schema': {
            'action': {
                'type': 'choice',
                'choices': {
                    'status': 'Show my keys',
                    'create': 'Create a key',
                    'revoke': 'Revoke a key',
                    'delete': 'Delete a key',
                },
            },
            'name': {
                'help_text': 'A label to tell your keys apart, e.g. "spreadsheet".',
                'attrs': {'autocomplete': 'off'},
            },
            'prefix': {
                'help_text': 'The 8 character prefix shown in the key list (the part after "qck_").',
                'attrs': {'autocomplete': 'off'},
            },
        },
        'showhide': {
            'action': {'fields': ['name', 'prefix'], 'callback': 'show_action_fields'}
        },
        'script':
            """
            function show_action_fields(v){
                return [v === 'create', v === 'revoke' || v === 'delete'];
            }
            """,
        'calculate': 'Apply',
    }


def _api_key_table(user):
    keys = list_api_keys(user)
    usage = key_usage([k.pk for k in keys])
    limits = api_limits()

    def fmt_used(used, limit):
        return f'{used} / {limit}' if limit else f'{used}'

    rows = [[
        k.name, f'qck_{k.prefix}_...', 'Active' if k.is_active else 'Revoked',
        k.added_on.strftime('%Y-%m-%d'),
        k.last_used_on.strftime('%Y-%m-%d %H:%M') if k.last_used_on else 'Never',
        fmt_used(usage[str(k.pk)]['day'], limits.get('key_day')),
        fmt_used(usage[str(k.pk)]['month'], limits.get('key_month')),
    ] for k in keys]
    return {
        'columns': ['Name', 'Key', 'State', 'Created', 'Last used (UTC)', 'Runs today', 'Runs this month'],
        'data': rows,
    }


def api_access(action='status', name='', prefix=''):
    req = QThread.get_req()
    if not is_loggedin(req):
        raise Exception('Please login to manage API access keys')

    user = req.user
    resp = {}
    try:
        if action == 'create':
            _record, raw_key = create_api_key(user, name, max_active=settings.QCALC_API_KEYS_MAX_PER_USER)
            resp['New API Key'] = qinfo(raw_key)
            resp['Important'] = qwarn('Copy this key now. It is shown only once and cannot be recovered.')
            logger.note('API: key created | user=%s | prefix=%s', user.username, _record.prefix)
        elif action == 'revoke':
            record = revoke_api_key(user, prefix)
            resp['Revoked'] = f"'{record.name}' (qck_{record.prefix}_...) can no longer be used"
            logger.note('API: key revoked | user=%s | prefix=%s', user.username, record.prefix)
        elif action == 'delete':
            record = delete_api_key(user, prefix)
            resp['Deleted'] = f"'{record.name}' (qck_{record.prefix}_...)"
            logger.note('API: key deleted | user=%s | prefix=%s', user.username, record.prefix)
        elif action != 'status':
            raise Exception(f'Unsupported action: {action}')
    except ApiKeyError as e:
        raise Exception(str(e))

    limits = api_limits()
    resp['My API Keys'] = _api_key_table(user)
    resp['Limits per key'] = (
        f"{limits.get('key_day') or 'unlimited'} runs/day, {limits.get('key_month') or 'unlimited'} runs/month; "
        f"{limits.get('user_day') or 'unlimited'} runs/day across all your keys (resets 00:00 UTC)"
    )
    resp['Max active keys'] = settings.QCALC_API_KEYS_MAX_PER_USER
    resp['Base URL'] = f'{qaddr()}/calc/api/v1/'
    resp['Example'] = (
        f'curl -H "Authorization: Bearer <your key>" "{qaddr()}/calc/api/v1/?q=bmi"'
    )
    return resp


def mem__info():
    return {
        'title': 'User Memory',
        # 'schema': {
        #     'request': {'attrs': {'readonly': True}},
        # },
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
             'qf': QFav,
             'qaichat': QOpenAIChat, 'qaical': QMyCalAI,
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
        'kins': 'mycal, mycal2, ai_chat, rates',
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
                    'qf': 'Your temporary favorites',  # QFavs (db)
                    'qaichat': 'Your AI chat cache',  # QOpenAIChat
                    'qaical': 'Your AI assisted calculator creation cache',  # QMyCalAI
                    'all': 'All your temporary data',  # All
                },
            },
        },
        'calculate': 'Show',
        'inserts': {
            'form_top':
                callback_button('temp', 'Delete Data', '__command', args=['delete']),
        }
    }


def temp(data='all'):
    selected_keys = sesn_objs.keys() if data == 'all' else [data]
    if data == 'qmy+qm':  # List calculators and directory together
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
