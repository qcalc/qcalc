# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import json
import re
from html.parser import HTMLParser
from types import SimpleNamespace

import qsett

qsett.init()

import pytest
import qvars
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.template.loader import get_template
from django.test import RequestFactory

from calc import QIO
from calc import views, views_step2
from qutil.timed_thread import QThread


def _make_get_request(path, query):
    request = RequestFactory().get(path, data=query)
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    return request


def _make_post_request(path, data):
    request = RequestFactory().post(path, data=data)
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    return request


class _HxValuesParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, _tag, attrs):
        attributes = dict(attrs)
        if "hx-vals" in attributes:
            self.values.append(attributes["hx-vals"])


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


def test_add_accepts_long_expression_path_in_post_body(monkeypatch):
    captured = {}
    expression = (
        "optima_sop(label='Demand +10%', literal_percent_code='%2B', table="
        + ("x" * 10000)
        + ")"
    )
    path = f"eva/code/{expression}"

    def _fake_open_form(_request, path, part):
        captured.update({
            "path": path,
            "part": part,
            "method": _request.method,
            "query_path": _request.GET.get("path"),
            "query_cid": _request.GET.get("cid"),
            "query_keys": set(_request.GET),
        })
        return HttpResponse("ok")

    request = _make_post_request(
        "/calc/add/",
        {
            "path": path,
            "cid": "optima_sop__existing",
            "input_id": "42",
            "unrelated_input": "must not leak",
        },
    )
    QThread.set_req(request)
    monkeypatch.setattr(views, "q1999_func_to_form", _fake_open_form)

    response = views.q1_add_func(request)

    assert response.status_code == 200
    assert captured["path"] == path
    assert captured["part"] == "1"
    assert captured["method"] == "GET"
    assert captured["query_path"] == path
    assert captured["query_cid"] is None
    assert captured["query_keys"] == {"path"}


def test_add_get_keeps_literal_percent_sequence(monkeypatch):
    captured = {}
    path = "eva/code/show('%2B')"

    def _fake_open_form(_request, path, part):
        captured.update({"path": path, "part": part})
        return HttpResponse("ok")

    request = _make_get_request("/calc/add/", {"path": path})
    QThread.set_req(request)
    monkeypatch.setattr(views, "q1999_func_to_form", _fake_open_form)

    response = views.q1_add_func(request)

    assert response.status_code == 200
    assert captured["path"] == path
    assert captured["part"] == "1"


def test_expression_action_posts_escaped_path_in_request_body():
    expression = "optima_sop(table=[\"A's\", \"line\\nbreak\"])" + ("x" * 10000)
    info = SimpleNamespace(step2=False, url=False, xpr=True, loop=False)
    document = SimpleNamespace(info=info, name="optima_sop", fxpr=expression)
    context = {
        "request": SimpleNamespace(success=True, method="POST", ojson_keep_dumps="{}"),
        "input": SimpleNamespace(doc=document, cid="cid-long-expression"),
        "user": SimpleNamespace(is_staff=False),
    }

    html = get_template("insert-calculator-section-outbtns.html").render(context)
    parser = _HxValuesParser()
    parser.feed(html)

    assert 'hx-post="/calc/add/"' in html
    assert 'hx-get="/calc/add/?path=' not in html
    assert 'hx-params="path"' in html
    assert json.loads(parser.values[0])["path"] == f"eva/code/{expression}"


def test_expression_post_renders_eva_with_isolated_output_target(monkeypatch):
    source_cid = "optima_sop__existing"
    request = _make_post_request(
        "/calc/add/",
        {
            "path": "eva/code/show('Demand +10%')",
            "cid": source_cid,
            "input_id": "42",
        },
    )
    request.session["hash"] = "test-user"
    QThread.set_req(request)
    monkeypatch.setattr(qvars, "super_user", SimpleNamespace(username="admin"))

    response = views.q1_add_func(request)
    html = response.content.decode()
    cid_match = re.search(r'id="form-([^"]+)"', html)

    assert response.status_code == 200
    assert cid_match is not None
    eva_cid = cid_match.group(1)
    assert eva_cid.startswith("eva__")
    assert eva_cid != source_cid
    assert f'hx-target="#output-part-{eva_cid}"' in html
    assert source_cid not in html
    assert "Demand +10%" in html


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

    monkeypatch.setattr(views_step2.QCals, "quick_find_func", lambda name: name)

    def _alias_lookup(_alias, default=''):
        raise AssertionError("Alias lookup must not be used outside add flow")

    monkeypatch.setattr(views.QCalAlias, "getp1", _alias_lookup)

    response = views_step2.q1_step2(request, _fake_open_form)

    assert response.status_code == 200
    assert captured["fname"] == "demo_next"
    assert captured["part"] == "1"
    assert captured["fargs"]["target_arg"] == "2 kg"
