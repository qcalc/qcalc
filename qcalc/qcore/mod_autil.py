# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import numpy as _np
import pandas as _pd
import inspect
from qutil.mod_basic import css2strs
from .qc_units import UnitRegistry
from .qc_qty import QtyRegistry
import fnmatch


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


def qsymbols(scope='api', name_filter=None, include_members=False):
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
    Set include_members=True to include public class members as
    <ClassSymbol>.<member> in the output.
    """
    from calc import QCals, CalcSandbox, qapis  # local import: calc imports qutil, avoid circular import

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

    # | remarks from: calc/mod_sandbox.py
    # | all qfunc_dict items except admin and demo cals, will eventually include pylib_dict and calc_dict
    # |     when create_standard_cataog_from_packages() are executed
    # | all UnitRegistry.table items that includes units and currencies
    # | all formal api items from __evacon__
    # | all auxiliary functions (qcalc/python) from make_symbol_table
    # | qsymbols = (qfunc_dict - admin cals - demo cals)  + UnitRegistry.table + QtyRegistry.info + __evacon__ + make_symbols_table
    # | qfunc_dict = (all calculators + auxiliaries) + (pylib_dict + calc_dict)

    names = set()
    if 'api' in scope_names or 'all' in scope_names:
        names |= qapis()
    if 'cal' in scope_names or 'all' in scope_names:
        names |= {
            name
            for name, obj in QCals.qfunc_dict.items()
            if callable(obj)
               and '__' not in name
               and f"{name}__info" in QCals.qfunc_dict
               and name in CalcSandbox.symbols  # admin and demo cals are excluded
        }
    if 'aux' in scope_names or 'all' in scope_names:
        names |= {
            name
            for name, obj in CalcSandbox.symbols.items()
            if callable(obj)
               and name not in qapis()
               and '__' not in name
               and f"{name}__info" not in QCals.qfunc_dict
        }
    if 'unit' in scope_names or 'all' in scope_names:
        names |= {
            name
            for name, unit in UnitRegistry.table.items()
            if unit.dimension != 'C'
        }
    if 'cur' in scope_names or 'all' in scope_names:
        names |= {
            name
            for name, unit in UnitRegistry.table.items()
            if unit.dimension == 'C'
        }
    if 'qty' in scope_names or 'all' in scope_names:
        names |= {
            name
            for name in QtyRegistry.info
        }
    if include_members:
        member_names = set()
        for name in names:
            obj = resolve_qsym_obj(name, QCals, CalcSandbox)
            if inspect.isclass(obj):
                member_names |= class_member_symbols(name, obj)
        names |= member_names

    entries = []
    for name in names:
        if name.startswith('_'):
            continue
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
    from calc import QCals, QtyCatalog, CalcSandbox

    name = str(name).strip()
    if not name:
        return 'Error: a name is required'

    if '.' in name:
        class_name, member_name = name.split('.', 1)
        if not class_name or not member_name:
            return f"Help not found for: {name}"

        cls = resolve_qsym_obj(class_name, QCals, CalcSandbox)
        if not inspect.isclass(cls):
            return f"Help not found for: {name}"

        member = inspect.getattr_static(cls, member_name, None)
        if member is None:
            return f"Help not found for: {name}"

        help_text = class_member_doc(cls, member_name, member)
        if not help_text:
            return f"Help not found for: {name}"
        return f"*** {name} ***\n{help_text}"

    # CAL / UNIT / CUR / QTY use TreeNode metadata.
    for root_name, root in (('calc_root', getattr(QCals, 'calc_root', None)),
                            ('qty_root', getattr(QtyCatalog, 'root', None))):
        if root is None:
            continue

        node = root.get_node_by_id(name)
        if node is not None:
            parts = []

            title = (getattr(node, 'title', '') or '').strip()
            desc = (getattr(node, 'desc', '') or '').strip()

            if title:
                parts.append(f"Title: {title}")
            if desc:
                parts.append(f"Description: {desc}")

            help_text = '\n'.join(parts) if parts else ""
            if root_name == 'calc_root':
                obj = getattr(QCals, 'qfunc_dict', {}).get(name)
                help_text += "\n" + obj_doc(obj)

            return f"*** {name} ***\n{help_text}"

    # API / AUX / qapi symbols use inline docstrings.
    obj = resolve_qsym_obj(name, QCals, CalcSandbox)

    help_text = obj_doc(obj)
    if not help_text:
        names = [sym_name for sym_name in qsymbols('all') if sym_name.lower() == name.lower()]
        if len(names) > 1:
            return f"Ambiguous symbol name: {name}. Matches: {', '.join(sorted(names))}"
        if len(names) == 1 and names[0] != name:
            return qsymhelp(names[0])
    if not help_text:
        return f"Help not found for: {name}"

    return f"*** {name} ***\n{help_text}"


def sig_doc(obj):
    if not callable(obj):
        return ""

    func_sig = inspect.signature(obj)
    help_text = f"\nFunction: {obj.__name__}{func_sig}"
    docstring = inspect.getdoc(obj)
    if docstring:
        help_text += f"\n\nNote: {docstring}"

    return help_text


def resolve_qsym_obj(name, QCals, CalcSandbox):
    obj = CalcSandbox.symbols.get(name)
    if obj is None:
        obj = getattr(QCals, 'qfunc_dict', {}).get(name)
    if obj is None:
        try:
            import qapi
            obj = getattr(qapi, name, None)
        except ImportError:
            obj = None
    return obj


def class_member_doc(cls, member_name, member):
    if isinstance(member, property):
        help_text = f"\nProperty: {cls.__name__}.{member_name}"
        docstring = inspect.getdoc(member.fget)
        if docstring:
            help_text += f"\n\nNote: {docstring}"
        return help_text

    target = member
    if isinstance(member, staticmethod):
        target = member.__func__
    elif isinstance(member, classmethod):
        target = member.__func__

    if callable(target):
        try:
            sig = inspect.signature(target)
        except (TypeError, ValueError):
            sig = "(...)"
        help_text = f"\nMethod: {cls.__name__}.{member_name}{sig}"
        docstring = inspect.getdoc(target)
        if docstring:
            help_text += f"\n\nNote: {docstring}"
        return help_text

    return f"\nProperty: {cls.__name__}.{member_name}"


def class_members_doc(cls):
    methods = []
    properties = []

    for name in dir(cls):
        if name.startswith('_'):
            continue

        try:
            member = inspect.getattr_static(cls, name)
        except Exception:
            continue

        target = member
        if isinstance(member, staticmethod):
            target = member.__func__
        elif isinstance(member, classmethod):
            target = member.__func__
        elif isinstance(member, property):
            properties.append(name)
            continue

        if callable(target):
            try:
                sig = inspect.signature(target)
            except (TypeError, ValueError):
                sig = "(...)"
            methods.append(f"{name}{sig}")
            continue

        if not hasattr(member, '__get__') and not hasattr(member, '__set__'):
            properties.append(name)

    lines = [f"\nClass: {cls.__name__}"]
    if methods:
        lines.append("\nPublic methods:")
        lines.extend(f"- {name}" for name in sorted(methods))
    if properties:
        lines.append("\nPublic properties:")
        lines.extend(f"- {name}" for name in sorted(set(properties)))
    return "\n".join(lines)


def class_member_symbols(class_name, cls):
    names = set()
    for member_name in dir(cls):
        if member_name.startswith('_'):
            continue
        try:
            member = inspect.getattr_static(cls, member_name)
        except Exception:
            continue

        target = member
        if isinstance(member, staticmethod):
            target = member.__func__
        elif isinstance(member, classmethod):
            target = member.__func__

        if isinstance(member, property) or callable(target):
            names.add(f"{class_name}.{member_name}")
            continue

        if not hasattr(member, '__get__') and not hasattr(member, '__set__'):
            names.add(f"{class_name}.{member_name}")
    return names


def obj_doc(obj):
    if inspect.isclass(obj):
        return class_members_doc(obj)
    return sig_doc(obj)
