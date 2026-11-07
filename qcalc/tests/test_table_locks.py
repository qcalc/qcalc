# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

import json

import pytest
from django.core.exceptions import ValidationError

from qcore.qf_qfields import TabulatorField
from qcore.qf_qwidgets import TabulatorWidget, table_lock_indices

BASE = {"columns": ["Item", "Price|USD", "Qty"], "data": [["a", 1, 2], ["b", 3, 4]]}


def _field(**attrs):
    field = TabulatorField({"attrs": {"class": "table-in"}}, "cid1", initial=BASE)
    field.widget.attrs.update(attrs)
    return field


def _post(columns, data):
    return json.dumps({"columns": columns, "data": data, "shape": ["2", "3"], "mode": "edit"})


def test_lock_indices_match_base_name_and_ignore_case_and_uom():
    headers, values = table_lock_indices({"readonly_cols": ["item"], "fixed_headers": ["PRICE"]}, BASE["columns"])

    assert values == {0}
    assert headers == {0, 1}


def test_lock_indices_true_locks_every_column():
    headers, values = table_lock_indices({"fixed_headers": True}, BASE["columns"])

    assert headers == {0, 1, 2}
    assert values == set()


def test_field_restores_locked_header_and_values():
    field = _field(readonly_cols=["Item"], fixed_headers=["Qty"])

    cleaned = json.loads(field.clean(_post(["X", "Price", "Y"], [["hack", 9, 9], ["hack", 8, 8]])))

    assert cleaned["columns"] == ["Item", "Price", "Qty"]
    assert [r[0] for r in cleaned["data"]] == ["a", "b"]
    assert [r[1:] for r in cleaned["data"]] == [[9, 9], [8, 8]]  # unlocked values stay editable
    assert cleaned["mode"] == "edit"


def test_field_rejects_row_change_when_values_locked():
    field = _field(readonly_cols=["Item"])

    with pytest.raises(ValidationError):
        field.clean(_post(BASE["columns"], BASE["data"] + [["c", 5, 6]]))


def test_field_allows_row_change_when_only_headers_fixed():
    field = _field(fixed_headers=["Item"])

    cleaned = json.loads(field.clean(_post(BASE["columns"], BASE["data"] + [["c", 5, 6]])))

    assert len(cleaned["data"]) == 3


def test_field_rejects_removed_locked_column():
    field = _field(fixed_headers=["Qty"])

    with pytest.raises(ValidationError):
        field.clean(_post(["Item", "Price|USD"], [["a", 1], ["b", 3]]))


def test_field_without_locks_returns_posted_value_unchanged():
    field = _field()
    posted = _post(["X", "Y", "Z"], [[1, 2, 3]])

    assert field.clean(posted) == posted


def test_widget_marks_locked_headers_and_fixes_rows():
    widget = TabulatorWidget(cid="cid1", class_="table-in")
    widget.attrs.update({"readonly_cols": ["Item"], "fixed_headers": ["Qty"]})

    html = widget.render("t", BASE, attrs=None)

    assert 'data-lock-rows="true"' in html and 'data-lock-headers="true"' in html
    assert '<th tabulator-editabletitle="false" tabulator-editor="false" tabulator-cssclass="q-col-locked">Item</th>' in html
    assert "<th>Price|USD</th>" in html
    assert '<th tabulator-editabletitle="false" tabulator-cssclass="q-col-fixed-head">Qty</th>' in html
    assert 'class="vt mr-2" readonly' in html  # the Row box is locked
    assert html.count('class="vt mr-2" readonly') == 1  # the Col box stays editable


def test_widget_fully_locked_table_marks_columns_without_tint():
    widget = TabulatorWidget(cid="cid1", class_="table-in")
    widget.attrs.update({"readonly_cols": True})

    html = widget.render("t", BASE, attrs=None)

    assert html.count('tabulator-cssclass="q-col-locked q-col-all"') == 3


def test_widget_resize_cannot_change_rows_or_drop_locked_columns():
    widget = TabulatorWidget(cid="cid1", class_="table-in")
    widget.attrs.update({"readonly_cols": ["Qty"]})
    value = {"columns": BASE["columns"], "data": BASE["data"], "shape": ["5", "1"]}

    html = widget.render("t", value, attrs=None)

    payload = json.loads(html.split('value="', 1)[1].split('" id=', 1)[0].replace("&quot;", '"'))
    assert payload["shape"] == ["2", "3"]
