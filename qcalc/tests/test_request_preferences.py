# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json
from types import SimpleNamespace

import pytest
import qsett

qsett.init()

from calc.views import apply_request_layout
from calc.views_form_data import (
    apply_persistent_request_prefs,
    q11421_get_extra_form_data_posted,
    q11441a_get_user_pref,
    serialize_persistent_request_prefs,
)
from calc import QPref


def test_persistent_request_preferences_round_trip_without_commands():
    request = SimpleNamespace(
        extra={
            'ignoredec': '1',
            'layout': 'tb',
            'interactive_enabled': '0',
            'cmd': 'resize',
            'args': ['rows'],
        },
        pref={'interactive': True},
    )

    apply_persistent_request_prefs(request)
    serialized = json.loads(serialize_persistent_request_prefs(request))

    assert request.pref == {
        'interactive': True,
        'ignore_decimal_format': True,
        'layout': 'tb',
        'interactive_enabled': False,
    }
    assert serialized == {
        'ignoredec': '1',
        'layout': 'tb',
        'interactive_enabled': '0',
    }


def test_user_preference_initializes_per_card_interactive_state(monkeypatch):
    monkeypatch.setattr(QPref, 'getp', lambda: {'interactive': False})
    request = SimpleNamespace(pref={})

    q11441a_get_user_pref(request)

    assert request.pref == {
        'interactive': False,
        'interactive_enabled': True,
    }


def test_refresh_get_imports_persistent_request_preferences():
    request = SimpleNamespace(
        method='GET',
        GET={'extra': '{"ignoredec":"1","layout":"tb","interactive_enabled":"0"}'},
        POST={},
        cmd='',
        extra={},
        pref={},
    )

    q11421_get_extra_form_data_posted(request)
    apply_persistent_request_prefs(request)

    assert request.extra == {
        'ignoredec': '1',
        'layout': 'tb',
        'interactive_enabled': '0',
    }
    assert request.pref == {
        'ignore_decimal_format': True,
        'layout': 'tb',
        'interactive_enabled': False,
    }


@pytest.mark.parametrize('layout', ['', 'horizontal', None])
def test_invalid_request_layout_is_rejected(layout):
    request = SimpleNamespace(extra={'layout': layout}, pref={})

    with pytest.raises(ValueError, match='Invalid calculator layout'):
        apply_persistent_request_prefs(request)


def test_request_layout_selects_static_template():
    request = SimpleNamespace(
        pref={'layout': 'tb'},
        json_doc={
            'info': {
                'layout': 'lr',
                'template': 'lr',
                'inp1': '*',
                'out1': ['result'],
                'input_blocks': [],
                'output_blocks': [],
            }
        },
    )

    apply_request_layout(request)

    assert request.json_doc['info']['layout'] == 'tb'
    assert request.json_doc['info']['template'] == 'tb2'


def test_request_layout_preserves_dynamic_template():
    request = SimpleNamespace(
        pref={'layout': 'tb'},
        json_doc={
            'info': {
                'layout': 'lr',
                'template': 'dynamic',
                'inp1': '*',
                'out1': '*',
                'input_blocks': [{'fields': ['value']}],
                'output_blocks': [],
            }
        },
    )

    apply_request_layout(request)

    assert request.json_doc['info']['layout'] == 'tb'
    assert request.json_doc['info']['template'] == 'dynamic'
