# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qsett

qsett.init()

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from qutil.mod_df import resize_df
from qcore.mod_qwidgets import TabulatorWidget
from calc import views as calc_views


# --- resize_df: pure-function regression coverage for the 0-row/0-col crash ---

def test_resize_df_zero_shape_does_not_raise_and_clamps_to_one():
    df = pd.DataFrame({"A": [1, 2, 3]})

    result = resize_df(df, 0, 0)

    assert len(result) == 1
    assert len(result.columns) == 1


def test_resize_df_zero_col_with_keep_last_col_does_not_raise():
    df = pd.DataFrame({"A": [1, 2, 3]})

    result = resize_df(df, 0, 0, 1)

    assert len(result) == 1
    assert len(result.columns) >= 1


def test_resize_df_negative_shape_clamps_to_one():
    df = pd.DataFrame({"A": [1, 2, 3]})

    result = resize_df(df, -5, -5)

    assert len(result) == 1
    assert len(result.columns) == 1


def test_resize_df_new_cells_are_blank_not_none_text():
    # na_rep='None' (used by df.to_html for redo/chart compatibility) must
    # only affect genuine missing values, not cells added by a resize.
    df = pd.DataFrame({"A": [1, None], "B": [3, 4]})

    grown = resize_df(df, 4, 3)
    html = grown.to_html(na_rep="None", index=False)

    assert html.count("None") == 1  # only the pre-existing NaN in column A
    assert "<td></td>" in html  # resized cells render blank


def test_resize_df_grows_rows_and_cols():
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

    result = resize_df(df, 4, 3)

    assert len(result) == 4
    assert len(result.columns) == 3


def test_resize_df_shrinks_rows_and_cols():
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})

    result = resize_df(df, 1, 1)

    assert len(result) == 1
    assert len(result.columns) == 1


def test_resize_df_ncol_clamped_to_100():
    df = pd.DataFrame({"A": [1]})

    result = resize_df(df, 1, 500)

    assert len(result.columns) == 100


# --- TabulatorWidget: end-to-end resize/update through the actual input-table widget ---

def _resize_value(data, columns, row, col, mode="edit"):
    return json.dumps({
        "data": data,
        "columns": columns,
        "shape": [row, col],
        "mode": mode,
    })


def test_tabulator_widget_resize_to_zero_does_not_crash():
    widget = TabulatorWidget(cid="cid1", class_="table-in")

    html = widget.render(
        "mytable",
        _resize_value(data=[[1, 2]], columns=["A", "B"], row=0, col=0),
        attrs=None,
    )

    assert html  # rendered without raising, table degraded to 1x1 rather than exploding


def test_tabulator_widget_update_preserves_data_without_resize():
    widget = TabulatorWidget(cid="cid1", class_="table-in")
    value = json.dumps({
        "data": [[1, 2], [3, 4]],
        "columns": ["A", "B"],
        "shape": [],
        "mode": "edit",
    })

    html = widget.render("mytable", value, attrs=None)

    assert "table-in" in html
    assert "cid1_mytable" in html


def test_tabulator_widget_resize_grows_table():
    widget = TabulatorWidget(cid="cid1", class_="table-in")

    html = widget.render(
        "mytable",
        _resize_value(data=[[1, 2]], columns=["A", "B"], row=5, col=4),
        attrs=None,
    )

    assert 'value="5" id="id_cid1_mytable_row"' in html


# --- q1999_func_to_form: server-side gate that keeps structural table commands
# (Resize/Edit/...) from being answered with the interactive output-only fragment ---

def _make_view_request(monkeypatch, cmd, interactive_pref=True, interactive_info=True):
    rendered = {}

    def fake_common(request, **dictf):
        pass  # request already carries the pref/json_doc/cmd needed by the branch under test

    def fake_render(request, template_name, context):
        rendered["template"] = template_name
        return SimpleNamespace(status_code=200)

    monkeypatch.setattr(calc_views, "q1199_func_to_form_common", fake_common)
    monkeypatch.setattr(calc_views, "q1_render", fake_render)

    request = SimpleNamespace(
        method="POST",
        GET={},
        pref={"interactive": interactive_pref},
        json_doc={"info": {"interactive": interactive_info}},
        cmd=cmd,
        context={},
    )
    calc_views.q1999_func_to_form(request)
    return rendered["template"]


@pytest.mark.parametrize("cmd", ["load", "resize", "edit", "display", "__modify"])
def test_structural_table_commands_bypass_interactive_output_fragment(monkeypatch, cmd):
    template = _make_view_request(monkeypatch, cmd=cmd)

    assert template != "insert-calculator-output-response.html"


def test_plain_field_change_uses_interactive_output_fragment_when_enabled(monkeypatch):
    template = _make_view_request(monkeypatch, cmd="")

    assert template == "insert-calculator-output-response.html"


def test_interactive_output_fragment_not_used_when_calculator_not_interactive(monkeypatch):
    template = _make_view_request(monkeypatch, cmd="", interactive_info=False)

    assert template != "insert-calculator-output-response.html"


def test_interactive_output_fragment_not_used_when_pref_disabled(monkeypatch):
    template = _make_view_request(monkeypatch, cmd="", interactive_pref=False)

    assert template != "insert-calculator-output-response.html"
