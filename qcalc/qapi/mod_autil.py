# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import numpy as _np
import pandas as _pd
from qutil import css2strs


def to_plain(value):
    """Convert pandas/numpy result types to plain Python so nothing with extra
    methods (eval/query/to_pickle/ctypes/...) ever escapes to sandboxed code."""
    if isinstance(value, (_pd.Series, _pd.DataFrame)):
        return value.to_dict()
    if isinstance(value, _pd.Index):
        return value.tolist()
    if isinstance(value, _np.ndarray):
        return value.tolist()
    if isinstance(value, _np.generic):
        return value.item()
    return value


def qsymbols(scope='api', name_filter=None):
    """
    List callables reachable from eva()/console/mycal() code.
    Optional name_filter can have wildcard (case-insensitive, *=any chars, ?=one char),
    e.g. 'add*', '*len*', matched against the full name.
    Prefix with '~' to negate, e.g. '~*info' lists names NOT ending in 'info'
    'scope' controls kind of symbols you want to list:
      'api' (default) - search only formally specified functions
      'cal' - search only calculators
      'aux' - search only auxiliary functions used by calculators
      'unit' - search only unit names (excluding currencies)
      'cur' - search only currency names
      'qty' - search only quantity names
      'all' - search all functions and symbols
      scope can also be a comma separated list of scope names: e.g. 'api, aux'
    """
    from calc import QCals  # local import: calc imports qutil, avoid circular import
    from . import _qapis
    from qcore import _unit_table, _qty_info
    import fnmatch

    allowed = {'api', 'cal', 'aux', 'unit', 'cur', 'qty', 'all'}
    scope_names = set(css2strs(scope))

    invalid = sorted(scope_names - allowed)
    if invalid:
        raise ValueError("scope must be one or more of: 'api', 'cal', 'aux', 'unit', 'cur', 'qty', or 'all'")

    negate = False
    if name_filter:
        name_filter = name_filter.lower()
        if name_filter.startswith('~'):
            negate = True
            name_filter = name_filter[1:]

    # | remarks from: mod_qcals.py
    # | all qfunc_dict items except admin and demo cals, will eventually include pylib_dict and calc_dict
    # |     when create_standard_cataog_from_packages() are executed
    # | all _unit_table items that includes units and currencies
    # | all formal api items from __evacon__
    # | all auxiliary functions (qcalc/python) from make_symbol_table
    # | qsymbols = (qfunc_dict - admin cals - demo cals)  + _unit_table + _qty_info + __evacon__ + make_symbols_table
    # | qfunc_dict = (all calculators + auxiliaries) + (pylib_dict + calc_dict)

    names = set()
    if 'api' in scope_names or 'all' in scope_names:
        names |= _qapis()
    if 'cal' in scope_names or 'all' in scope_names:
        names |= {
            name
            for name, obj in QCals.qfunc_dict.items()
            if callable(obj)
               and '__' not in name
               and f"{name}__info" in QCals.qfunc_dict
               and name in QCals.qsymbol_dict  # admin and demo cals are excluded
        }
    if 'aux' in scope_names or 'all' in scope_names:
        names |= {
            name
            for name, obj in QCals.qsymbol_dict.items()
            if callable(obj)
               and name not in _qapis()
               and '__' not in name
               and f"{name}__info" not in QCals.qfunc_dict
        }
    if 'unit' in scope_names or 'all' in scope_names:
        names |= {
            name
            for name, unit in _unit_table.items()
            if unit.dimension != 'C'
        }
    if 'cur' in scope_names or 'all' in scope_names:
        names |= {
            name
            for name, unit in _unit_table.items()
            if unit.dimension == 'C'
        }
    if 'qty' in scope_names or 'all' in scope_names:
        names |= {
            name
            for name in _qty_info
        }
    entries = []
    for name in names:
        if name_filter and fnmatch.fnmatch(name.lower(), name_filter) == negate:
            continue

        entries.append(name)

    entries.sort()
    return entries


def qsymstat():
    """Return a summary dict of qsymbol counts by category and total."""
    stats = {
        'api': len(qsymbols('api')),
        'cal': len(qsymbols('cal')),
        'aux': len(qsymbols('aux')),
        'unit': len(qsymbols('unit')),
        'cur': len(qsymbols('cur')),
        'qty': len(qsymbols('qty')),
        'total': len(qsymbols('all')),
    }
    return stats


def qsymhelp(name):
    """Print a short help/description for a qcalc symbol and return it."""
    from calc import QCals

    name = str(name).strip()
    if not name:
        return 'Error: a name is required'

    # CAL / UNIT / CUR / QTY use TreeNode metadata.
    for root_name in ('calc_root', 'qty_root'):
        root = getattr(QCals, root_name, None)
        if root is None:
            continue

        node = root.get_node_by_id(name)
        if node is not None:
            parts = []

            title = (getattr(node, 'title', '') or '').strip()
            desc = (getattr(node, 'desc', '') or '').strip()

            if title:
                parts.append(title)
            if desc:
                parts.append(desc)

            help_text = (
                '\n'.join(parts) if parts else ""
            )

            return f"*** {name} ***\n{help_text}"

    # API / AUX / qapi symbols use inline docstrings.
    obj = getattr(QCals, 'qsymbol_dict', {}).get(name)
    if obj is None:
        obj = getattr(QCals, 'qfunc_dict', {}).get(name)

    if obj is None:
        try:
            import qapi
            obj = getattr(qapi, name, None)
        except ImportError:
            obj = None

    help_text = getattr(obj, '__doc__', None)
    if help_text:
        help_text = help_text.strip()
        return f"*** {name} ***\n{help_text}"

    return f"Help not found for: {name}"
