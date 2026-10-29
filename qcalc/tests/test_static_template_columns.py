# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

from types import SimpleNamespace

import pytest
import qsett

qsett.init()

from calc.views import apply_effective_prefs
from calc.views_info_meta import resolve_static_side, side_columns, static_template_name, template_name

FIELDS = ['a', 'b', 'c', 'd']


@pytest.mark.parametrize('layout, icols, ocols, expected', [
    ('lr', 1, 1, 'lr'),
    ('lr', 2, 1, 'l2r'),
    ('lr', 1, 2, 'lr2'),
    ('lr', 2, 2, 'l2r2'),
    ('tb', 1, 1, 'tb'),
    ('tb', 2, 1, 't2b'),
    ('tb', 1, 2, 'tb2'),
    ('tb', 2, 2, 't2b2'),
])
def test_template_name_from_columns(layout, icols, ocols, expected):
    assert template_name(layout, icols, ocols) == expected


def test_side_columns_without_field_list_uses_spec():
    assert side_columns(None, '*') == 1
    assert side_columns(None, ['a']) == 2


def test_side_columns_explicit_value_wins():
    assert side_columns(1, ['a'], FIELDS) == 1
    assert side_columns(2, '*', FIELDS) == 2


def test_side_columns_depends_on_coverage_not_spelling():
    assert side_columns(None, list(FIELDS), FIELDS) == 1
    assert side_columns(None, ['a', 'b'], FIELDS) == 2


def _info(**kwargs):
    return {'layout': 'lr', 'input_columns': None, 'output_columns': None, **kwargs}


@pytest.mark.parametrize('group1', [list(FIELDS), list(reversed(FIELDS))])
def test_full_list_and_star_give_same_template(group1):
    info = _info(inp1=group1)
    resolve_static_side(info, 'input', FIELDS)
    assert info['template'] == 'lr'
    assert info['input_columns'] == 1


def test_partial_group_gives_two_columns():
    info = _info(inp1=['a', 'b'])
    resolve_static_side(info, 'input', FIELDS)
    assert info['template'] == 'l2r'
    assert info['inp1'] == ['a', 'b']


def test_explicit_one_column_ignores_subset():
    info = _info(inp1=['a'], input_columns=1)
    resolve_static_side(info, 'input', FIELDS)
    assert info['template'] == 'lr'


def test_explicit_two_columns_with_full_group_splits_fields():
    info = _info(inp1=list(FIELDS), input_columns=2)
    resolve_static_side(info, 'input', FIELDS)
    assert info['template'] == 'l2r'
    assert info['inp1'] == ['a', 'b']


def test_output_side_resolved_after_inputs():
    info = _info(inp1=list(FIELDS), out1=['x'])
    resolve_static_side(info, 'input', FIELDS)
    assert info['template'] == 'lr2'  # out1 spec not resolved yet, provisional
    info['out1'] = ['x', 'y']
    resolve_static_side(info, 'output', ['x', 'y'])
    assert info['template'] == 'lr'


def test_static_template_name_provisional_from_spec():
    assert static_template_name(_info(inp1='*', out1='*')) == 'lr'
    assert static_template_name(_info(inp1=['a'], out1='*')) == 'l2r'
    assert static_template_name(_info(layout='tb', inp1='*', out1=['x'])) == 'tb2'


def test_request_layout_keeps_resolved_columns_after_inp1_expansion():
    request = SimpleNamespace(
        pref={},
        extra={'layout': 'tb'},
        json_doc={'info': _info(inp1=list(FIELDS), out1='*', input_blocks=[], output_blocks=[])},
    )
    resolve_static_side(request.json_doc['info'], 'input', FIELDS)

    apply_effective_prefs(request)

    assert request.json_doc['info']['template'] == 'tb'
