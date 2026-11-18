# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

import pytest
import qvars
import calc
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from calc import QPref, QRam
from calculators.all.general import qeval
from qcore.mod_autil import qsymbols
from qutil.timed_thread import QThread


def _make_request():
    request = RequestFactory().get("/")
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    return request


@pytest.fixture
def request_(request, monkeypatch):
    # q1139_request_init() reads qvars.super_user.username; stub it out since
    # this test suite has no pytest-django/DB setup to look up a real User.
    monkeypatch.setattr(qvars, "super_user", type("_FakeUser", (), {"username": "super"})())

    req = _make_request()
    QThread.set_req(req)
    QRam.clear()
    QPref.setp1("strict_assign", False)
    yield req
    QThread.set_req(None)


def test_dict_subscript_assignment_persists(request_):
    qeval(request_, "x={}")
    qeval(request_, 'x["name"]=5')

    result, _ = qeval(request_, "x")

    assert result == {"name": 5}


def test_augmented_assignment_persists(request_):
    qeval(request_, "y=2")
    qeval(request_, "y+=8")

    result, _ = qeval(request_, "y")

    assert result == 10


def test_multi_statement_assignment_persists(request_):
    qeval(request_, "x=1;y=2")

    result, _ = qeval(request_, "y")

    assert result == 2


def test_strict_mode_blocks_subscript_assignment_to_reserved_name(request_):
    QPref.setp1("strict_assign", True)

    result, _ = qeval(request_, "min[0] = 1")

    assert "can't be assigned" in result


def test_strict_mode_blocks_reserved_name_in_multi_statement(request_):
    QPref.setp1("strict_assign", True)

    result, _ = qeval(request_, "min=1; x=2")

    assert "can't be assigned" in result


def test_forget_clears_assigned_variables(request_):
    qeval(request_, "x=42")
    qeval(request_, "forget")

    result, stdout = qeval(request_, "x")

    # "x" is no longer defined, so evaluating it should fail rather than
    # return the previously assigned value
    assert result != 42


def test_help_command_keyword_is_case_insensitive(request_):
    result, _ = qeval(request_, "HeLP")
    assert isinstance(result, str)
    assert result.startswith("Commands:")


def test_find_command_keyword_is_case_insensitive(request_):
    result, _ = qeval(request_, "FiNd")
    assert result == "Usage: find <name>"


def test_help_symbol_lookup_is_case_insensitive_when_unique(request_):
    result, _ = qeval(request_, "help QSYMBOLS")
    assert isinstance(result, str)
    assert "*** qsymbols ***" in result


def test_help_class_shows_class_and_init_docstrings_before_members(request_):
    result, _ = qeval(request_, "help Qtable")

    class_doc = "Create a table from rows and optional column rules."
    init_doc = "Initialize a QTable instance with the given data, columns, schema, and constraints."
    member_listing = "\nClass: QTable"

    assert f"Description:\n{class_doc}" in result
    assert f"Constructor (__init__):\n{init_doc}" in result
    assert result.index(class_doc) < result.index(init_doc) < result.index(member_listing)


def test_find_includes_class_members_in_search(request_, monkeypatch):
    captured = {}

    def _fake_qsymbols(scope, name_filter=None, include_members=False):
        captured['scope'] = scope
        captured['name_filter'] = name_filter
        captured['include_members'] = include_members
        return ['DemoClass.member']

    monkeypatch.setattr('qcore.mod_autil.qsymbols', _fake_qsymbols)
    monkeypatch.setattr('qcore.mod_autil.qsymhelp', lambda name: f'help for {name}')

    result, _ = qeval(request_, "find DemoClass.mem*")

    assert captured == {
        'scope': 'all',
        'name_filter': 'DemoClass.mem*',
        'include_members': True,
    }
    assert result == "Match: DemoClass.member\nhelp for DemoClass.member"


def test_qsymbols_restricts_leading_underscore_names(monkeypatch):
    monkeypatch.setattr(calc, "qapis", lambda: {"visible_api", "_hidden_api"})

    names = qsymbols("api")

    assert "visible_api" in names
    assert "_hidden_api" not in names
