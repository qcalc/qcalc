# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

import json

import pandas as pd
import pytest
from django.core.exceptions import ValidationError

from qcore import Qty, numeric_columns
from qcore.qf_qfields import TabulatorField
from qcore.qf_qwidgets import (
    TabulatorWidget, style_table_headers, table_column_options, table_lock_indices, table_out_attrs,
)

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


# --- column widths: attrs['col_widths']

def test_column_options_whole_number_is_the_maximum_width():
    assert table_column_options({"col_widths": {"Item": 150}}, BASE["columns"]) == {0: ' tabulator-maxwidth="150"'}


def test_column_options_dict_gives_min_max_width_and_wrap():
    options = table_column_options(
        {"col_widths": {"Item": {"min": 80, "max": 200, "width": 120, "wrap": True}}}, BASE["columns"])

    assert options == {0: ' tabulator-minwidth="80" tabulator-maxwidth="200" tabulator-width="120"'
                          ' tabulator-formatter="textarea"'}


def test_column_options_match_base_name_ignoring_case_and_uom_and_skip_unknown_columns():
    options = table_column_options({"col_widths": {"PRICE": {"min": 70}, "missing": 40}}, BASE["columns"])

    assert options == {1: ' tabulator-minwidth="70"'}


def test_column_options_empty_without_the_attribute():
    assert table_column_options({}, BASE["columns"]) == {}
    assert table_column_options(None, BASE["columns"]) == {}


@pytest.mark.parametrize("spec", [0, -5, 1.5, True, "wide", {"max": 0}, {"min": "a"}, {"color": 1}, {"min": 200, "max": 100}, [100]])
def test_column_options_reject_invalid_values(spec):
    with pytest.raises(ValueError):
        table_column_options({"col_widths": {"Item": spec}}, BASE["columns"])


def test_column_options_reject_a_col_widths_that_is_not_a_dict():
    with pytest.raises(ValueError):
        table_column_options({"col_widths": ["Item"]}, BASE["columns"])


def test_widget_adds_width_options_to_the_header_cells_only_for_listed_columns():
    widget = TabulatorWidget(cid="cid1", class_="table-in")
    widget.attrs.update({"col_widths": {"Item": {"max": 90, "wrap": True}, "Qty": {"min": 60}}})

    html = widget.render("t", BASE, attrs=None)

    assert '<th tabulator-maxwidth="90" tabulator-formatter="textarea">Item</th>' in html
    assert "<th>Price|USD</th>" in html
    assert '<th tabulator-minwidth="60">Qty</th>' in html
    assert "data-lock" not in html  # widths do not lock anything


def test_widget_combines_lock_and_width_options_on_the_same_column():
    widget = TabulatorWidget(cid="cid1", class_="table-in")
    widget.attrs.update({"readonly_cols": ["Item"], "col_widths": {"Item": 90}})

    html = widget.render("t", BASE, attrs=None)

    assert ('<th tabulator-editabletitle="false" tabulator-editor="false" tabulator-cssclass="q-col-locked"'
            ' tabulator-maxwidth="90">Item</th>') in html


def test_widget_without_col_widths_keeps_plain_header_cells():
    widget = TabulatorWidget(cid="cid1", class_="table-in")

    html = widget.render("t", BASE, attrs=None)

    assert "tabulator-" not in html.split("</thead>", 1)[0]


def test_widths_do_not_make_the_field_restore_or_lock_posted_values():
    field = _field(col_widths={"Item": {"max": 90}})
    posted = _post(["X", "Y", "Z"], [[1, 2, 3]])

    assert field.clean(posted) == posted


# --- output tables: attrs['align'], out_schema

def test_column_options_align_combines_with_widths_and_validates():
    options = table_column_options(
        {"col_widths": {"Price": 80}, "align": {"price": "right", "Item": "center", "missing": "left"}},
        BASE["columns"])

    right = 'tabulator-hozalign="right" tabulator-headerhozalign="right"'
    assert options == {0: ' tabulator-hozalign="center" tabulator-headerhozalign="center"',
                       1: f' tabulator-maxwidth="80" {right}'}
    for bad in ({"Item": "middle"}, ["Item"]):
        with pytest.raises(ValueError):
            table_column_options({"align": bad}, BASE["columns"])


def test_column_options_numeric_positions_are_right_aligned_unless_the_author_says_otherwise():
    options = table_column_options({"align": {"Qty": "left"}}, BASE["columns"], numeric=[1, 2])

    assert options == {1: ' tabulator-hozalign="right" tabulator-headerhozalign="right"',
                       2: ' tabulator-hozalign="left" tabulator-headerhozalign="left"'}


def test_numeric_columns_detects_numbers_quantities_and_numeric_text_only():
    df = pd.DataFrame({
        "int": [1, 2], "float": [1.5, None], "flag": [True, False], "text": ["a", "b"],
        "unitext": ["399.6 bag", "-"], "mixed": ["12", "dozen"], "pct": ["+39 %", ""], "num": ["1,234.5", "7"],
        "qty": [Qty(3, "m"), Qty(4, "ft")], "dates": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "blank": ["-", ""], "sentence": ["1 st Floor", "2 nd Floor"],
    })

    assert [df.columns[i] for i in numeric_columns(df)] == ["int", "float", "unitext", "pct", "num", "qty"]


def test_style_table_headers_tags_only_listed_header_cells():
    html = "<table><thead><tr><th>A</th><th>B</th></tr></thead><tbody><tr><td>1</td><td>2</td></tr></tbody></table>"

    assert style_table_headers(html, {1: ' tabulator-hozalign="right"'}) == html.replace(
        "<th>B</th>", '<th tabulator-hozalign="right">B</th>')
    assert style_table_headers(html, {}) == html


def test_out_attrs_find_the_result_by_title_or_variable_name_and_validate():
    schema = {"Method Comparison": {"attrs": {"page_all": True, "align": {"A": "right"}}}}

    assert table_out_attrs(schema, "Method Comparison", "method_comparison") == schema["Method Comparison"]["attrs"]
    assert table_out_attrs(schema, "other", "method_comparison") == {}
    assert table_out_attrs(None, "x") == {}
    for bad in ({"attrs": {"readonly_cols": True}}, {"attrs": {"page_all": 1}}):
        with pytest.raises(ValueError):
            table_out_attrs({"x": bad}, "x")
