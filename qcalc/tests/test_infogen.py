# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import html
import inspect
import re

import pandas as pd

import qsett

qsett.init()

from calc import QCals
from calculators.all.general.author.cal_infogen import infogen, infogen__info, _code_block


def _code(result):
    assert isinstance(result, dict), result
    block = result['Info Code']
    assert block.startswith('<div class="md-content">')
    match = re.search(r'<code[^>]*>(.*?)</code>', block, re.S)
    return html.unescape(match.group(1))


def test_code_block_fence_outgrows_backticks_in_code():
    block = _code_block("x = '```'\ny = '`'")

    assert block.startswith('````python\n')
    assert block.endswith('\n````')
    assert _code_block('x = 1').startswith('```python\n')


def test_infogen_output_is_escaped_markdown_code_block():
    block = infogen(source="def calc(a_type='<b>&', price=1.0):\n    '''Cost is $5 and $6.'''")['Info Code']

    assert '<pre>' in block and 'language-python' in block
    assert '<b>' not in block  # raw HTML is escaped inside the code block
    assert '$5' in block and 'math/tex' not in block


def test_infogen_default_example_generates_valid_code():
    code = _code(infogen())

    compile(code, '<infogen>', 'exec')
    assert 'def my_calc__info():' in code
    assert "'rate_pct'" in code


def test_infogen_overrides_table_is_applied():
    overrides = pd.DataFrame({
        'Argument': ['objective'],
        'Label': [''],
        'Help': ['Main goal'],
        'Choices': ['cost=Minimize Cost, service'],
        'Group': [''],
        'Show When': [''],
    })
    code = _code(infogen(overrides=overrides))

    assert "'Main goal'" in code
    assert "'cost': 'Minimize Cost'" in code


def test_infogen_reports_notes_and_errors():
    result = infogen(source='def calc(unknown_type):', overrides=pd.DataFrame())

    assert 'Notes' in result
    assert str(infogen(source='def (:')).startswith('Error (CIF)')


def test_infogen_resolves_standard_calculator_by_name(monkeypatch):
    from calculators.all.business.planning import cal_sop

    monkeypatch.setattr(QCals, 'quick_find_func', classmethod(lambda cls, name, scope='qpots': 'optima_sop'))
    monkeypatch.setattr(QCals, 'addr', classmethod(lambda cls, fid, scope='qpots': cal_sop.optima_sop))

    code = _code(infogen(source='optima_sop'))

    assert 'def optima_sop__info():' in code
    assert "'stability_enabled'" in code
    assert "table_sop_demand('sop_demand')" in code


def test_infogen_proper_words_are_applied_and_written():
    code = _code(infogen(source='def sop_plan(x=1.0)', proper='SOP'))

    assert "'title': 'SOP Plan'" in code
    assert "'proper': 'SOP'" in code


def test_infogen_own_info_is_consistent():
    info = infogen__info()
    schema = info['schema']
    tabs = {t['title']: t['fields'] for t in info['input_blocks'][0]['tabs']}

    assert tabs['Details'] == ['title', 'desc', 'tags', 'proper', 'outputs']
    assert sorted(sum(tabs.values(), [])) == sorted(inspect.signature(infogen).parameters)
    assert info['calculate'] == 'Generate' and info['tags']
    assert schema['tabs']['initial'] == 'auto'
    assert schema['scan_body']['initial'] is True
