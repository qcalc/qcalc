import qsett

qsett.init()

import pytest
import qvars
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from calc import QPref, QRam
from calculators.all.general.cal_evacon import qeval
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
