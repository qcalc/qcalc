# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""Effective preference resolution.

A preference can be defined at three levels, resolved once per request by resolve_effective_prefs():

1. session:    the user's saved defaults (pref()), request.session_pref
2. calculator: keys declared by the calculator's __info(), request.json_doc['declared']
3. request:    values posted by the page in 'extra', request.req_pref

Modes (PREF_OPTIONS[key]['mode']):
- 'override': request > calculator > session > default
- 'gate':     calculator and session must both allow it (the calculator defaults to the session value)
"""

import json

from qconst import QCALC_LAYOUTS


def _parse_bool(value):
    if value == '1':
        return True
    if value == '0':
        return False
    raise ValueError(f'Invalid boolean request preference: {value!r}')


def _serialize_bool(value):
    return '1' if value else '0'


def _parse_layout(value):
    if value not in QCALC_LAYOUTS:
        raise ValueError(f'Invalid calculator layout: {value!r}')
    return value


# key: preference name as found in request.pref
#   extra:   key in the page's 'extra' that carries the request level value (absent: not settable per request)
#   calc:    True if __info() may declare it under the same key
#   session: name of the session level preference when it differs from the key
#   default: used when no level defines it (absent: leave it undefined)
PREF_OPTIONS = {
    'layout': {
        'extra': 'layout',
        'calc': True,
        'mode': 'override',
        'default': 'lr',
        'parse': _parse_layout,
        'serialize': str,
    },
    'interactive': {
        'calc': True,
        'mode': 'gate',
        'default': False,
    },
    'interactive_enabled': {
        'extra': 'interactive_enabled',
        'mode': 'override',
        'default': True,
        'parse': _parse_bool,
        'serialize': _serialize_bool,
    },
    'slider_enabled': {
        'extra': 'slider_enabled',
        'session': 'slider',
        'mode': 'override',
        'default': True,
        'parse': _parse_bool,
        'serialize': _serialize_bool,
    },
    'ignore_decimal_format': {
        'extra': 'ignoredec',
        'mode': 'override',
        'parse': _parse_bool,
        'serialize': _serialize_bool,
    },
}


def declared_prefs(func_info):
    # | keys of the calculator level defined by __info()
    return sorted(key for key, option in PREF_OPTIONS.items() if option.get('calc') and key in func_info)


def _request_overrides(request):
    if not hasattr(request, 'req_pref'):
        request.req_pref = {}
    return request.req_pref


def apply_persistent_request_prefs(request):
    # | request level: import the values posted in 'extra'
    overrides = _request_overrides(request)
    for key, option in PREF_OPTIONS.items():
        extra_key = option.get('extra')
        if extra_key and extra_key in request.extra:
            value = option['parse'](request.extra[extra_key])
            request.pref[key] = value
            overrides[key] = value


def serialize_persistent_request_prefs(request):
    # | only request level values, so that the session or calculator defaults are not turned into overrides
    overrides = _request_overrides(request)
    result = {}
    for key, option in PREF_OPTIONS.items():
        extra_key = option.get('extra')
        if extra_key and key in overrides:
            result[extra_key] = option['serialize'](overrides[key])
    return json.dumps(result, separators=(',', ':'))


def resolve_effective_prefs(request):
    # | compute the effective value of every option in one place, into request.pref and info
    # Inputs, one per level:
    #   session:    the user's saved defaults in pref()
    #   calculator: only the options __info() declared
    #   request:    only the values posted by the page in 'extra'
    info = request.json_doc['info']
    declared = set(request.json_doc.get('declared', ()))
    session = getattr(request, 'session_pref', {})
    overrides = _request_overrides(request)

    for key, option in PREF_OPTIONS.items():
        # Step 1: session level value, or the option's default when the user never saved one
        session_key = option.get('session', key)
        session_has = session_key in session
        session_value = session[session_key] if session_has else option.get('default')

        # Step 2a: 'gate' mode (interactive): the calculator and the session must both allow it
        if option.get('mode') == 'gate':
            # the calculator defaults to the session value when it did not declare the option
            calc_value = info.get(key) if key in declared else session_value
            info[key] = bool(calc_value) and bool(session_value)
            # request.pref keeps the session value, it is the user's veto
            if session_has:
                request.pref[key] = session_value
            continue

        # Step 2b: 'override' mode, the most specific level wins: request > calculator > session > default
        if key in overrides:
            value = overrides[key]
        elif key in declared:
            value = info[key]
        elif session_has:
            value = session[session_key]
        elif 'default' in option:
            value = option['default']
        else:
            # no level defines it and there is no default, leave it undefined
            continue

        # Step 3: publish the effective value, request.pref for the code and templates that read preferences,
        # info for the options a calculator may declare
        request.pref[key] = value
        if option.get('calc'):
            info[key] = value
