# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import json
import re

import qsett

qsett.init()

import pytest
import qvars
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory

from calc import QIO
from calc import views, views_step2
from calc.views_info_meta import _step2_into_inserts
from calculators.all.general.chart import pie_chart
from qcore import QChart, Qty
from qutil import action_spec, prefix_button_names, step2_attrs, step2_spec
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

    payload = views_step2.step2_compact_io_payload(
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

    payload = views_step2.step2_compact_io_payload(
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
    monkeypatch.setattr(views_step2.QCals, "quick_find_func", lambda name: name)

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

    response = views_step2.q1_step2(request, _fake_open_form)

    assert response.status_code == 200
    assert captured["fname"] == "demo_next"
    assert captured["part"] == "1"
    assert captured["fargs"]["target_arg"] == "2 kg"


def _post_step2(calc, fields, step2):
    from django.test import Client

    data = {"cid": f"{calc}__t1", "input_id": 0, **fields, "extra": json.dumps({"cmd": "step2", **step2})}
    return Client(HTTP_HOST="localhost").post(f"/calc/{calc}/?part=2", data, HTTP_HX_REQUEST="true")


def test_input_step2_opens_the_next_calculator_with_the_converted_live_form():
    step2 = {"step": "run", "func": "bmr", "source": "input",
             "spec": json.dumps({"weight": "weight", "height": "height"})}
    fields = {"weight": "70", "weight_uom": "kg", "height": "180", "height_uom": "cm"}

    html = _post_step2("bmi", fields, step2).content.decode()

    assert 'id="form-bmr__' in html and 'id="form-bmi__t1"' not in html
    assert re.search(r'name="weight"[^>]*value="70(\.0)?"', html) and 'data-default="kg"' in html
    assert re.search(r'name="height"[^>]*value="180(\.0)?"', html) and 'data-default="cm"' in html


def test_input_step2_reports_the_validation_error_like_calculate():
    step2 = {"step": "run", "func": "bmr", "source": "input", "spec": "weight"}

    response = _post_step2("bmi", {"weight": "abc", "weight_uom": "kg"}, step2)

    assert "Input validation failed" in response["HX-Trigger"] and 'id="form-bmr__' not in response.content.decode()


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

    response = views_step2.q1_step2(request, _fake_open_form)

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

    response = views_step2.calc_io_clear(request, "cid_a")
    body = json.loads(response.content)

    assert response.status_code == 200
    assert body["ok"] is True
    assert body["removed"] is True
    assert QIO.getp1("cid_a") is None
    assert QIO.getp1("cid_b") is not None


def _form_fields(html):
    """name -> value of the inputs and selects of the first calculator form, as the browser would post them."""
    form = html[html.index("<form"):html.index("</form>")]
    fields = {}
    for tag in re.findall(r"<input[^>]*>", form):
        name = re.search(r'name="([^"]+)"', tag)
        value = re.search(r'value="([^"]*)"', tag)
        if name and 'type="button"' not in tag and 'type="file"' not in tag:
            fields.setdefault(name.group(1), value.group(1) if value else "")
    for select in re.findall(r"<select[^>]*>", form):
        name = re.search(r'name="([^"]+)"', select)
        default = re.search(r'data-default="([^"]*)"', select)
        if name and default:
            fields[name.group(1)] = default.group(1)
    return fields


@pytest.mark.parametrize("calc, field, expected", [
    ("gold", "gold_weight_india", lambda v: v.count(",") == 3 and "vori" in v and "point" in v),  # 4 parts
    ("gold", "gold_weight_intl", lambda v: v == "10.0 g"),  # one part
    ("demo_arr2", "x", lambda v: v == [100, 200, 300]),  # qlist
    ("ccwork", "csg_ratio__gravel_part", lambda v: v == 4.0),  # a part of a composite is a function argument itself
])
def test_input_step2_caches_the_values_calculate_would_pass_for_composite_fields(calc, field, expected):
    from django.test import Client

    client = Client(HTTP_HOST="localhost")
    fields = _form_fields(client.get(f"/calc/core/{calc}/").content.decode())
    extra = {"cmd": "step2", "step": "run", "func": "bmi", "source": "input", "spec": ""}
    data = {**fields, "extra": json.dumps(extra)}

    response = client.post(f"/calc/{calc}/?part=2", data, HTTP_HX_REQUEST="true")
    assert response.headers.get("HX-Trigger") is None
    (payload,) = client.get("/calc/io/").json().values()
    cached = payload["input"]

    assert not any(k.endswith(("_uom", "_part_uom")) for k in cached)  # no raw unit inputs are left over
    assert expected(cached[field])


def test_cache_step2_input_keeps_the_cached_output():
    QThread.set_req(_make_request())
    QIO.clear()
    QIO.setp1("cid_k", {"function": "f", "input": {"a": "old"}, "output": {"r": 1}})

    views_step2.cache_step2_input("cid_k", "f", {"a": Qty("2 kg")})
    cached = QIO.getp1("cid_k")

    assert cached["output"] == {"r": 1}
    assert views_step2.QBridge.source_map(cached, "input") == {"a": "2.0 kg"}


def test_needs_step2_cache_only_when_an_entry_reads_the_result():
    inp = step2_spec("f", "F", spec="a", source="input")
    out = step2_spec("f", "F", spec="a")
    assert not views_step2.needs_step2_cache({"step2": [inp]})
    assert views_step2.needs_step2_cache({"step2": [inp, out]})
    assert views_step2.needs_step2_cache({"step2": [], "schema": {"go": {"button": out}}})
    assert not views_step2.needs_step2_cache({"step2": [], "schema": {"go": {"button": inp}}})
    assert not views_step2.needs_step2_cache({"schema": {"go": {"button": action_spec("load")}}})


def test_step2_attrs_post_the_form_to_its_calculator_for_input_and_the_card_cache_for_output():
    entry = step2_spec("f", "F", spec={"a": "b"}, source="input")
    attrs = step2_attrs(entry, func="src")
    assert 'hx-post="/calc/src/?part=2"' in attrs and 'hx-include="closest form"' in attrs
    assert "&quot;cmd&quot;:&quot;step2&quot;" in attrs and "src_cid" not in attrs
    with pytest.raises(ValueError):
        step2_attrs(entry)
    attrs = step2_attrs(step2_spec("f", "F", spec={"a": "b"}), "c1")
    assert 'hx-post="/calc/step2/"' in attrs and "hx-include" not in attrs
    assert "&quot;src_cid&quot;:&quot;c1&quot;" in attrs


def test_btn_field_bound_to_step2_renders_htmx_attributes():
    from qcore.qf_qwidgets import ButtonWidget

    entry = step2_spec("rates", "Show Rates", "open", {"rate_domain": "rate_domain"}, source="input")
    meta = {"initial": "Show Rates", "attrs": {"id": "b1"}, "button": entry, "button_func": "cost"}
    html = ButtonWidget(meta, "0").render("show_rates", None)

    assert 'class="btn btn-info btncmd"' in html
    assert 'hx-post="/calc/cost/?part=2"' in html and 'hx-include="closest form"' in html
    plain = ButtonWidget({"initial": "Go", "attrs": {"id": "b2"}}, "0").render("go", None)
    assert "hx-post" not in plain


def test_btn_field_bound_to_an_action_posts_the_command_to_its_calculator():
    from qcore.qf_qwidgets import ButtonWidget

    entry = action_spec("load", spec={"from": "upload_csv", "to": "csv_table"}, args=["a"], kwargs={"b": "x"},
                        extra={"quoting": "1"}, sync_table=True)
    meta = {"initial": "Load CSV", "attrs": {"id": "b3"}, "button": entry, "button_func": "csv_editor"}
    html = ButtonWidget(meta, "0").render("load", None)
    vals = json.loads(re.search(r'hx-vals="([^"]*)"', html).group(1).replace("&quot;", '"'))

    assert 'hx-post="/calc/csv_editor/?part=2"' in html and 'hx-target="closest form"' in html
    assert "data-qcalc-sync-table" in html and "update-after-swap" not in html
    assert vals == {"extra": {"cmd": "load", "quoting": "1", "from": "upload_csv", "to": "csv_table",
                              "args": ["a"], "kwargs": {"b": "x"}}, "qcalc_structural_cmd": "1"}


def test_nested_calculator_prefixes_the_field_names_of_its_buttons():
    from calc.mod_mfunc import QFuncInfo
    from qconst import DICT_CLASS_FUNC

    button = action_spec("load", spec={"from": "upload_csv"}, args=["a"], kwargs={"b": "x"}, extra={"q": "1"})
    info = {"child": {DICT_CLASS_FUNC: "child", "schema": {"load": {"button": button}}}}

    flat = QFuncInfo(info).flat["schema"]["child--load"]["button"]

    assert flat["spec"] == {"from": "child--upload_csv"}
    assert flat["args"] == ["child--a"] and flat["kwargs"] == {"child--b": "x"} and flat["extra"] == {"q": "1"}
    assert button["spec"] == {"from": "upload_csv"}
    assert prefix_button_names(step2_spec("f", "F", spec="a,b"), "p--")["spec"] == "a,b"


def test_step2_into_inserts_places_input_entries_and_keeps_author_inserts_intact():
    authored = {"form_bottom": "<i>x</i>"}
    info = {"inserts": authored, "step2": [
        step2_spec("f", "In", source="input"),
        step2_spec("f", "Top", source="input", place="form_top"),
        step2_spec("f", "Out"),
    ]}

    _step2_into_inserts(info, "host")

    assert info["inserts"]["form_bottom"].startswith("<i>x</i><button")
    assert ">In<" in info["inserts"]["form_bottom"] and "/calc/host/?part=2" in info["inserts"]["form_bottom"]
    assert ">Top<" in info["inserts"]["form_top"]
    assert "Out" not in "".join(info["inserts"].values())
    assert authored == {"form_bottom": "<i>x</i>"}
