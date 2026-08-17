# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import QScreen
import qvars
from calc import QCache, QCals
from qutil import nzs, css2strs, truncate
import logging

logger = logging.getLogger(__name__)


def gpref__info():
    return {
        'title': 'Global Settings',
        'schema': {
            'range_limit': {'attrs': {'max': '2000', 'min': '10'}},
            'execution_mode': {'type': 'choice',
                               'choices': {'0': 'Main Thread', '1': 'Child Thread'}},
        },
        'calculate': 'Save',
    }


def gpref__input(_kwargs):
    gs = qvars.qc_gpref
    return {
        # global settings
        'range_limit': gs['range_limit'],
        'demo_mode': gs['demo_mode'],
        'schema_cache': gs['schema_cache'],
        'uom_v2': gs['uom_v2'],
        'execution_mode': gs['execution_mode'],
    }


def gpref(
    # global settings
    range_limit: int,
    demo_mode: bool,
    schema_cache: bool,
    uom_v2: bool,
    execution_mode
):
    # global settings
    # Make admin global-setting changes only during maintenance windows.
    # Restart all app workers immediately after each change.
    # As the inconsistency risk exists in multi-worker setups:
    # it mutates in-process memory only, so different workers can run different values after a change.
    # Avoid live toggling under load.
    gs = qvars.qc_gpref  # | change in gs will change qcconfig.qc_pref
    gs['range_limit'] = range_limit  # global
    gs['demo_mode'] = demo_mode  # global
    gs['schema_cache'] = schema_cache  # global
    gs['uom_v2'] = uom_v2  # global
    gs['execution_mode'] = execution_mode  # global
    # save settings
    return 'Global Preferences Updated'


def qcache__info():
    return {
        'title': 'User Cache',
        'calculate': 'Show',
    }


def qcache(functions='', clear_cache=False):
    if nzs(functions) != '':
        keylist = css2strs(functions)
        if clear_cache:
            for key in keylist:
                QCache.remove(key)
            keylist = QCals.qc_list
    else:
        keylist = QCals.qc_list  # QCache.keys() no way to get Memcached keys
        if clear_cache:
            QCache.clear()
            keylist = {}

    res = {}
    try:
        out = QScreen()
        out.write('')
        for k in keylist:
            v = QCache.get_data(k)
            if v is not None:
                out.write({k: truncate(v, 64)})
                out.write('')
        res = out.flush()
    except Exception as e:
        logger.error(f'QCH: Could not connect to cache server; {e}')

    gs = qvars.qc_gpref
    return {
        'Status': 'Active' if QCache.active else 'Inactive',
        'Schema Cacheing': 'On' if gs['schema_cache'] else 'Off',
        'Content': res
    }
