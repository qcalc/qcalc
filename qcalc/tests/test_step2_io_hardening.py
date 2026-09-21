import json

import qsett

qsett.init()

import pytest
import qvars
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory

from calc import QIO
from calc import views
from calculators.all.general.chart import pie_chart
from qcore import QChart, Qty
from qutil.timed_thread import QThread


def _make_request(path="/calc/step2/", query=None, method="get"):
    query = query or {}
    rf = RequestFactory()
    request = rf.post(path, data=query) if method == "post" else rf.get(path, data=query)
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    return request


@pytest.fixture(autouse=True)
def _stub_super_user(monkeypatch):
    monkeypatch.setattr(qvars, "super_user", type("_FakeUser", (), {"username": "super"})())


@pytest.fixture(autouse=True)
def _clear_thread_request():
    QThread.set_req(None)
    yield
    QThread.set_req(None)


def test_step2_compact_payload_keeps_qty_and_chart_data():
    chart = QChart(width=200)
    chart.save_data({"xvals": [1, 2], "yvals2d": [[3, 4]], "labels": ["s1"]}, "lines")

    payload = views._step2_compact_io_payload(
        "demo_func",
        {"mass": Qty("2 kg")},
        {"plot": chart, "price": Qty("12 USD")},
    )

    assert payload["function"] == "demo_func"
    assert payload["input"]["mass"]["__qcalc_type"] == "qty"
    assert payload["output"]["price"]["__qcalc_type"] == "qty"
    assert payload["output"]["plot"]["__qcalc_type"] == "chart"
    assert payload["output"]["plot"]["chtype"] == "lines"


def test_step2_compact_payload_handles_self_referential_chart_data():
    chart = pie_chart(labels="A,B", values="2,3")["chart"]

    payload = views._step2_compact_io_payload(
        "cost",
        {},
        {"Chart": chart},
    )

    packed_chart = payload["output"]["Chart"]
    assert packed_chart["__qcalc_type"] == "chart"
    assert packed_chart["chtype"] == "pie_chart"
    assert "chart" not in packed_chart["data"]


def test_q1_step2_run_unpacks_qty_as_string(monkeypatch):
    captured = {}

    def _fake_open_form(_request, fname, fargs, part):
        captured.update({"fname": fname, "fargs": fargs, "part": part})
        return HttpResponse("ok")

    monkeypatch.setattr(views, "q1999_func_to_form", _fake_open_form)
    monkeypatch.setattr(views.QCals, "quick_find_func", lambda name: name)

    request = _make_request(
        query={
            "step": "run",
            "func": "demo_next",
            "src_cid": "cid_run",
            "spec": json.dumps({"target_arg": "mass"}),
        }
    )
    QThread.set_req(request)
    QIO.clear()
    QIO.setp1(
        "cid_run",
        {
            "input": {"mass": {"__qcalc_type": "qty", "value": "2 kg"}},
            "output": {},
        },
    )

    response = views.q1_step2(request)

    assert response.status_code == 200
    assert captured["fname"] == "demo_next"
    assert captured["part"] == "1"
    assert captured["fargs"]["target_arg"] == "2 kg"


def test_q1_step2_run_cost_alias_works_with_cost_style_spec(monkeypatch):
    captured = {}

    def _fake_open_form(_request, fname, fargs, part):
        captured.update({"fname": fname, "fargs": fargs, "part": part})
        return HttpResponse("ok")

    monkeypatch.setattr(views, "q1999_func_to_form", _fake_open_form)
    monkeypatch.setattr(views.QCals, "quick_find_func", lambda name: name)

    request = _make_request(
        query={
            "step": "run",
            "func": "cost",
            "src_cid": "cid_run_cost",
            "spec": json.dumps({"exclude": ["skip_this"]}),
        }
    )
    QThread.set_req(request)
    QIO.clear()
    QIO.setp1(
        "cid_run_cost",
        {
            "input": {},
            "output": {
                "mass": {"__qcalc_type": "qty", "value": "2 kg"},
                "skip_this": {"__qcalc_type": "qty", "value": "3 kg"},
                "price": {"__qcalc_type": "qty", "value": "12 USD"},
                "label": "ignore",
            },
        },
    )

    response = views.q1_step2(request)

    assert response.status_code == 200
    assert captured["fname"] == "cost"
    assert captured["part"] == "1"
    items = captured["fargs"]["items"]
    assert list(items["Item"]) == ["mass"]
    assert isinstance(items["Quantity"].iloc[0], Qty)


def test_q1_step2_chart_works_with_packed_chart(monkeypatch):
    captured = {}

    def _fake_open_form(_request, fname, fargs, part):
        captured.update({"fname": fname, "fargs": fargs, "part": part})
        return HttpResponse("ok")

    monkeypatch.setattr(views, "q1999_func_to_form", _fake_open_form)

    chart_data = {
        "xvals": [1, 2],
        "yvals2d": [[3, 4]],
        "labels": ["series"],
    }

    request = _make_request(
        query={
            "step": "chart",
            "src_cid": "cid_chart",
            "spec": json.dumps({"field": "plot"}),
        }
    )
    QThread.set_req(request)
    QIO.clear()
    QIO.setp1(
        "cid_chart",
        {
            "input": {},
            "output": {
                "plot": {
                    "__qcalc_type": "chart",
                    "chtype": "lines",
                    "data": chart_data,
                }
            },
        },
    )

    response = views.q1_step2(request)

    assert response.status_code == 200
    assert captured["fname"] == "lines"
    assert captured["part"] == "1"
    assert captured["fargs"] == chart_data


def test_calc_io_clear_deletes_only_requested_cid():
    request = _make_request(path="/calc/io/clear/cid_a/", method="post")
    QThread.set_req(request)
    QIO.clear()
    QIO.setp1("cid_a", {"input": {}, "output": {}})
    QIO.setp1("cid_b", {"input": {}, "output": {}})

    response = views.calc_io_clear(request, "cid_a")
    body = json.loads(response.content)

    assert response.status_code == 200
    assert body["ok"] is True
    assert body["removed"] is True
    assert QIO.getp1("cid_a") is None
    assert QIO.getp1("cid_b") is not None
