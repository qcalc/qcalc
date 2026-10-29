# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import json
from types import SimpleNamespace

import pytest
import qsett

qsett.init()

from calc.mod_prefs import (
    apply_persistent_request_prefs,
    declared_prefs,
    resolve_effective_prefs,
    serialize_persistent_request_prefs,
)
from calc.views import apply_effective_prefs


def _request(session=None, extra=None, declared=(), info=None):
    session = dict(session or {})
    return SimpleNamespace(
        pref=dict(session),
        session_pref=session,
        extra=dict(extra or {}),
        json_doc={
            'declared': list(declared),
            'info': {
                'layout': 'lr',
                'template': 'lr',
                'interactive': False,
                'inp1': '*',
                'out1': '*',
                'input_blocks': [],
                'output_blocks': [],
                **(info or {}),
            },
        },
    )


def _resolve(request):
    apply_effective_prefs(request)
    return request


def test_q1141_records_declared_prefs(monkeypatch):
    from calc.mod_qcals import QCals
    from calc.views_info_meta import q1141_read_func_meta

    monkeypatch.setattr(QCals, 'run_func_info', classmethod(
        lambda cls, func_id, scope='qpots': {'layout': 'tb', 'interactive': False, 'title': 'T'}))
    doc = q1141_read_func_meta('bmi')

    assert doc['declared'] == ['interactive', 'layout']
    assert doc['info']['layout'] == 'tb'


def test_q1141_invalid_layout_is_not_declared(monkeypatch):
    from calc.mod_qcals import QCals
    from calc.views_info_meta import q1141_read_func_meta

    monkeypatch.setattr(QCals, 'run_func_info', classmethod(lambda cls, func_id, scope='qpots': {'layout': 'x'}))
    doc = q1141_read_func_meta('bmi')

    assert 'layout' not in doc['declared']
    assert doc['info']['layout'] == 'lr'


def test_declared_prefs_lists_only_calculator_level_options():
    assert declared_prefs({'layout': 'lr', 'interactive': True, 'title': 'x', 'slider': False}) == [
        'interactive', 'layout']


@pytest.mark.parametrize('session, declared, info_layout, extra, expected', [
    ({'layout': 'tb'}, [], 'lr', {}, 'tb'),  # session level only
    ({}, [], 'lr', {}, 'lr'),  # global default
    ({'layout': 'tb'}, ['layout'], 'lr', {}, 'lr'),  # calculator beats session
    ({'layout': 'lr'}, ['layout'], 'tb', {}, 'tb'),
    ({'layout': 'tb'}, ['layout'], 'lr', {'layout': 'tb'}, 'tb'),  # request beats calculator
    ({'layout': 'lr'}, [], 'lr', {'layout': 'tb'}, 'tb'),  # request beats session
])
def test_layout_precedence(session, declared, info_layout, extra, expected):
    request = _resolve(_request(session, extra, declared, {'layout': info_layout}))

    assert request.json_doc['info']['layout'] == expected
    assert request.pref['layout'] == expected


def test_bmi_like_calculator_layout_wins_over_saved_user_layout():
    request = _resolve(_request({'layout': 'tb'}, declared=['layout'], info={'layout': 'lr'}))

    assert request.json_doc['info']['template'] == 'lr'


def test_template_follows_effective_layout():
    request = _resolve(_request({'layout': 'tb'}))

    assert request.json_doc['info']['template'] == 'tb'


@pytest.mark.parametrize('session, declared, info_interactive, expected', [
    ({'interactive': True}, [], False, True),  # calculator defaults to the session value
    ({'interactive': False}, [], False, False),
    ({'interactive': True}, ['interactive'], False, False),  # calculator opts out
    ({'interactive': True}, ['interactive'], True, True),
    ({'interactive': False}, ['interactive'], True, False),  # session vetoes
    ({}, ['interactive'], True, False),
])
def test_interactive_is_a_gate(session, declared, info_interactive, expected):
    request = _resolve(_request(session, declared=declared, info={'interactive': info_interactive}))

    assert request.json_doc['info']['interactive'] is expected


@pytest.mark.parametrize('session, extra, expected', [
    ({}, {}, True),
    ({'slider': False}, {}, False),
    ({'slider': False}, {'slider_enabled': '1'}, True),
    ({'slider': True}, {'slider_enabled': '0'}, False),
])
def test_slider_enabled_precedence(session, extra, expected):
    request = _resolve(_request(session, extra))

    assert request.pref['slider_enabled'] is expected


def test_ignore_decimal_format_session_value_kept_unless_overridden():
    assert _resolve(_request({'ignore_decimal_format': True})).pref['ignore_decimal_format'] is True
    request = _resolve(_request({'ignore_decimal_format': True}, {'ignoredec': '0'}))
    assert request.pref['ignore_decimal_format'] is False


def test_saved_defaults_are_not_serialized_as_overrides():
    request = _resolve(_request({'layout': 'tb', 'slider': False, 'ignore_decimal_format': True}))

    assert json.loads(serialize_persistent_request_prefs(request)) == {}


def test_request_overrides_round_trip_through_extra():
    first = _resolve(_request({'layout': 'lr'}, {'layout': 'tb', 'slider_enabled': '0'}))
    serialized = json.loads(serialize_persistent_request_prefs(first))

    assert serialized == {'layout': 'tb', 'slider_enabled': '0'}

    second = _resolve(_request({'layout': 'lr'}, serialized, declared=['layout'], info={'layout': 'lr'}))
    assert second.json_doc['info']['layout'] == 'tb'


def test_reapplying_request_prefs_is_idempotent():
    request = _request({'layout': 'lr'}, {'layout': 'tb'})

    apply_persistent_request_prefs(request)
    apply_persistent_request_prefs(request)
    resolve_effective_prefs(request)

    assert request.req_pref == {'layout': 'tb'}
    assert request.pref['layout'] == 'tb'
