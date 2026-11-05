# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import json

import qsett

qsett.init()

from django.test import RequestFactory

from calc import QPref, StdList
from calc.views import set_theme


def test_set_theme_persists_valid_choice(monkeypatch):
    monkeypatch.setattr(StdList, 'theme_list', {'choices': ['auto', 'light', 'dark']})
    saved = {}
    monkeypatch.setattr(QPref, 'setp1', lambda key, value: saved.update({key: value}))
    request = RequestFactory().post('/calc/theme/', {'theme': 'dark'})

    response = set_theme(request)

    assert response.status_code == 200
    assert json.loads(response.content) == {'ok': True, 'theme': 'dark'}
    assert saved == {'theme': 'dark'}


def test_set_theme_rejects_invalid_choice(monkeypatch):
    monkeypatch.setattr(StdList, 'theme_list', {'choices': ['auto', 'light', 'dark']})
    request = RequestFactory().post('/calc/theme/', {'theme': 'neon'})

    response = set_theme(request)

    assert response.status_code == 400
    assert json.loads(response.content) == {'ok': False, 'error': 'Invalid theme'}


def test_set_theme_returns_htmx_fragment_and_trigger(monkeypatch):
    monkeypatch.setattr(StdList, 'theme_list', {'choices': ['auto', 'light', 'dark']})
    saved = {}
    monkeypatch.setattr(QPref, 'setp1', lambda key, value: saved.update({key: value}))
    request = RequestFactory().post('/calc/theme/', {'theme': 'light'}, HTTP_HX_REQUEST='true')

    response = set_theme(request)

    assert response.status_code == 200
    assert '"qcalc:theme-changed": {"theme": "light"}' in response['HX-Trigger']
    assert b'id="nav-theme"' in response.content
    assert saved == {'theme': 'light'}
