# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import qtbl, as_qtable
from calc import QCals, QCalAlias
import pandas as pd
import re

ALIAS_PATTERN = re.compile(r'^[a-z][a-z0-9_]{0,31}$')
RESERVED_ALIASES = {'mycal', 'myalias'} # Reserved aliases that cannot be used by the user


def _norm_alias(alias_value):
    alias = str(alias_value or '').strip().lower()
    if not alias:
        return ''
    if not ALIAS_PATTERN.match(alias):
        raise ValueError(
            f"Invalid alias '{alias}'. Use 1-32 chars: lowercase letters, digits, underscore; must start with a letter."
        )
    if alias in RESERVED_ALIASES:
        raise ValueError(f"Alias '{alias}' is reserved.")
    existing = QCals.quick_find_func(alias)
    if existing == alias:
        raise ValueError(f"Alias '{alias}' conflicts with existing calculator name.")
    return alias


def _norm_target(target_value):
    target = str(target_value or '').strip().lower()
    if not target:
        raise ValueError('Target calculator is required.')
    resolved = QCals.quick_find_func(target)
    if resolved is None:
        raise ValueError(f"Target calculator '{target}' was not found.")
    return resolved


def _table_to_pairs(aliases):
    table = as_qtable(aliases)
    if 'Alias' not in table.columns or 'Calculator' not in table.columns:
        raise ValueError("Input table must include columns 'Alias' and 'Calculator'.")
    rows = []
    for _, row in table.iterrows():
        alias_raw = '' if pd.isna(row['Alias']) else row['Alias']
        target_raw = '' if pd.isna(row['Calculator']) else row['Calculator']
        if str(alias_raw).strip() == '' and str(target_raw).strip() == '':
            continue
        alias = _norm_alias(alias_raw)
        target = _norm_target(target_raw)
        rows.append((alias, target))
    return rows


def _pairs_to_qtbl(pairs):
    return {'columns': ['Alias', 'Calculator'], 'data': [[alias, target] for alias, target in pairs]}


def myalias__input(_kwargs):
    alias_map = QCalAlias.getp({})
    pairs = sorted(
        [
            (str(alias).strip().lower(), str(target).strip().lower())
            for alias, target in alias_map.items()
            if str(alias).strip() and str(target).strip()
        ],
        key=lambda x: x[0],
    )
    return {'aliases': _pairs_to_qtbl(pairs)}


def myalias__info():
    return {
        'title': 'Manage My Calculator Aliases',
        'desc': ('Create personal aliases used by "add calculator". '
                 'Aliases are not used in expression evaluation.'),
        'schema': {
            'aliases': {
                'label': 'Alias Table',
                'help_text': 'Columns: Alias, Calculator. Rows left blank are ignored. '
                'Saving replaces your alias list. Aliases are available from add calculator only.',
            }
        },
        'calculate': 'Save Aliases',
        'layout': 'tb',
    }


def myalias(aliases: qtbl = {'columns': ['Alias', 'Calculator'], 'data': [['mybmi', 'bmi']]}):
    pairs = _table_to_pairs(aliases)
    alias_map = {}
    for alias, target in pairs:
        alias_map[alias] = target

    QCalAlias.clear()
    for alias, target in alias_map.items():
        QCalAlias.setp1(alias, target)

    saved_pairs = sorted(alias_map.items(), key=lambda x: x[0])
    return {
        'Saved Aliases': len(saved_pairs),
        'Aliases': _pairs_to_qtbl(saved_pairs),
    }
