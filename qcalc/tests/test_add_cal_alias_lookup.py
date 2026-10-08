import json

import qsett

qsett.init()

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory

from calc import QIO
from calc import views
from qutil.timed_thread import QThread


def _make_get_request(path, query):
    request = RequestFactory().get(path, data=query)
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    return request


@pytest.fixture(autouse=True)
def _clear_thread_request():
    QThread.set_req(None)
    yield
    QThread.set_req(None)


def test_add_uses_personal_alias_when_function_not_found(monkeypatch):
    captured = {}

    def _fake_open_form(_request, fname, part, fargs=None):
        captured.update({"fname": fname, "part": part, "fargs": fargs})
        return HttpResponse("ok")

    def _quick_find(name):
        if name == "mybmi":
            return None
        if name == "bmi":
            return "bmi"
        return None

    request = _make_get_request("/calc/add/", {"fname": "mybmi"})
    QThread.set_req(request)
    monkeypatch.setattr(views, "q1999_func_to_form", _fake_open_form)
    monkeypatch.setattr(views.QCals, "quick_find_func", _quick_find)
    monkeypatch.setattr(views.QCalAlias, "getp1", lambda alias, default='': "bmi" if alias == "mybmi" else default)

    response = views.q1_add_func(request)

    assert response.status_code == 200
    assert captured["fname"] == "bmi"
    assert captured["part"] == "1"


def test_add_prefers_real_function_over_alias(monkeypatch):
    captured = {}

    def _fake_open_form(_request, fname, part, fargs=None):
        captured.update({"fname": fname, "part": part, "fargs": fargs})
        return HttpResponse("ok")

    request = _make_get_request("/calc/add/", {"fname": "bond"})
    QThread.set_req(request)
    monkeypatch.setattr(views, "q1999_func_to_form", _fake_open_form)
    monkeypatch.setattr(views.QCals, "quick_find_func", lambda name: "bond" if name == "bond" else None)

    def _alias_lookup(_alias, default=''):
        raise AssertionError("Alias lookup must not run when direct function match exists")

    monkeypatch.setattr(views.QCalAlias, "getp1", _alias_lookup)

    response = views.q1_add_func(request)

    assert response.status_code == 200
    assert captured["fname"] == "bond"
    assert captured["part"] == "1"


def test_step2_run_does_not_use_personal_alias_lookup(monkeypatch):
    captured = {}

    def _fake_open_form(_request, fname, fargs, part):
        captured.update({"fname": fname, "part": part, "fargs": fargs})
        return HttpResponse("ok")

    request = _make_get_request(
        "/calc/step2/",
        {
            "step": "run",
            "func": "demo_next",
            "src_cid": "cid_alias_guard",
            "spec": json.dumps({"target_arg": "mass"}),
        },
    )
    QThread.set_req(request)
    QIO.clear()
    QIO.setp1(
        "cid_alias_guard",
        {
            "input": {"mass": {"__qcalc_type": "qty", "value": "2 kg"}},
            "output": {},
        },
    )

    monkeypatch.setattr(views, "q1999_func_to_form", _fake_open_form)
    monkeypatch.setattr(views.QCals, "quick_find_func", lambda name: name)

    def _alias_lookup(_alias, default=''):
        raise AssertionError("Alias lookup must not be used outside add flow")

    monkeypatch.setattr(views.QCalAlias, "getp1", _alias_lookup)

    response = views.q1_step2(request)

    assert response.status_code == 200
    assert captured["fname"] == "demo_next"
    assert captured["part"] == "1"
    assert captured["fargs"]["target_arg"] == "2 kg"
