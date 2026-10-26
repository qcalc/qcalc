# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import inspect
import re

import pandas as pd

from calc import QCals, mod_optima_tables
from qcore import as_qtable, qchar, qcode, qerror, qhtml, qtable, qtext, qwarn
from qutil import md2html
from qutil.mod_code_info import build_info as _build_info

OVERRIDE_COLUMNS = ['Argument', 'Label', 'Help', 'Choices', 'Group', 'Show When']
ID_PATTERN = re.compile(r'^[A-Za-z_]\w*$')
STANDARD_CAL_MODULE = 'calculators.'


def _table_helpers():
    return {name for name in dir(mod_optima_tables) if name.startswith('table_')}


def _source_of_standard_calculator(cal_name):
    """Module source and function name of a standard (non-user) calculator."""
    func_id = QCals.quick_find_func(cal_name, scope='q')
    if not isinstance(func_id, str):
        raise ValueError(f"Calculator '{cal_name}' was not found among standard calculators")
    func = QCals.addr(func_id, 'q')
    module = inspect.getmodule(func)
    if func is None or module is None or not module.__name__.startswith(STANDARD_CAL_MODULE):
        raise ValueError(f"Source of '{cal_name}' is not available, paste its code instead")
    return inspect.getsource(module), func.__name__


def _override_rows(overrides):
    if overrides is None:
        return []
    table = as_qtable(overrides)
    return [
        {col: row[col] for col in table.columns if not pd.isna(row[col])}
        for _, row in table.iterrows()
    ]


def _code_block(code, lang='python'):
    # a longer fence than any backtick run in the code keeps the block closed
    longest = max((len(m) for m in re.findall(r'`+', code)), default=0)
    fence = '`' * max(3, longest + 1)
    return f'{fence}{lang}\n{code.rstrip()}\n{fence}'


def infogen__info():
    return {
        'title': 'Generate Calculator Info',
        'desc': (
            'Draft the __info() metadata of a calculator from its function signature or code'
        ),
        'calculate': 'Generate',
        'kins': 'eva, mycal, mycal2, ai_chat, q2cal',
        'tags': 'create calculator, metadata, schema, developer, author',
        'layout': 'tb',
        'input_columns': 1,
        'input_blocks': [
            {
                'column': 1,
                'tabs': [
                    {
                        'title': 'Source',
                        'fields': ['source', 'func_name', 'tabs', 'scan_body', 'explicit_defaults', 'overrides'],
                    },
                    {
                        'title': 'Details',
                        'fields': ['title', 'desc', 'tags', 'proper', 'outputs'],
                    },
                ],
            },
        ],
        'schema': {
            'source': {
                'help_text': (
                    'A function signature such as "calc(x, y=1.0)" (def and colon are optional), '
                    'a whole function or module, an argument list such as "x, y=1.0", '
                    'or the name of a standard calculator.'
                ),
            },
            'func_name': {
                'help_text': 'Function to use when the source contains several functions.',
            },
            'title': {'help_text': 'Calculator title. Defaults to a title built from the function name.'},
            'desc': {'help_text': 'Description. Defaults to the first paragraph of the docstring.'},
            'tags': {'help_text': 'Comma separated tags. Defaults to words from the name and feature groups.'},
            'proper': {
                'help_text': (
                    'Comma separated words that keep their case in titles, e.g. "SOP, BOM, qCalc". '
                    'Written as the "proper" key of __info().'
                ),
            },
            'outputs': {
                'help_text': (
                    'Comma separated output names. Used to build output tabs when the code does not '
                    'return a dict literal.'
                ),
            },
            'tabs': {
                'type': 'choice',
                'choices': {'auto': 'Automatic', 'yes': 'Use tabs', 'no': 'No tabs'},
                'initial': 'auto',
                'help_text': 'Group input fields in tabs.',
            },
            'scan_body': {
                'type': 'checkbox',
                'initial': True,
                'help_text': 'Infer choices and output names from the function body.',
            },
            'explicit_defaults': {
                'type': 'checkbox',
                'initial': False,
                'help_text': (
                    'Also write type and initial value for fields that have a default in the signature. '
                    'Not needed, qcalc derives them from the default.'
                ),
            },
            'overrides': {
                'help_text': (
                    'Per argument refinements. Choices: "a=Label A, b=Label B". Show When: '
                    '"controller == value", "controller != value" or "controller in a, b". '
                    'Group is a tab title.'
                ),
            },
        },
    }


def infogen(
    source: qcode = 'def my_calc(objective, rate_pct=5.0, use_extra=False, extra_cost=0.0):',
    func_name: qchar = '',
    title: qchar = '',
    desc: qtext = '',
    tags: qtext = '',
    proper: qtext = '',
    outputs: qtext = '',
    tabs='auto',
    scan_body=True,
    explicit_defaults=False,
    overrides: qtable = pd.DataFrame({col: [''] for col in OVERRIDE_COLUMNS}),
):
    try:
        source = source.strip()
        func_name = func_name.strip()
        if ID_PATTERN.match(source):
            source, func_name = _source_of_standard_calculator(source)

        hints = {
            'func_name': func_name,
            'title': title.strip(),
            'desc': desc.strip(),
            'tags': tags.strip(),
            'proper': proper.strip(),
            'outputs': outputs,
            'tabs': {'yes': True, 'no': False}.get(tabs),
        }
        hints = {k: v for k, v in hints.items() if v not in ('', None)}
        hints['scan_body'] = bool(scan_body)
        hints['explicit_defaults'] = bool(explicit_defaults)
        result = _build_info(
            source,
            overrides=_override_rows(overrides),
            hints=hints,
            table_helpers=_table_helpers(),
        )
    except Exception as e:
        return qerror(f'Error (CIF): {e}')

    # qhtml, not qchat: qchat auto-scrolls to the end, and .md-content adds a Copy button to code blocks
    output = {'Info Code': qhtml(md2html(_code_block(result.code), wrap=True))}
    if result.warnings:
        output['Notes'] = qwarn('\n'.join(f'- {w}' for w in result.warnings))
    return output
