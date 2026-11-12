# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

from types import SimpleNamespace

import qsett

qsett.init()

from calc.views_result import q1145_result_to_form_schema
from qcore import Qty, qchat


def test_qchat_renders_as_scrollable_html_output():
    request = SimpleNamespace(
        pref={},
        recall=False,
        remember=False,
        success=True,
        var_owner='',
        variant='',
        token='',
        cmd='',
        ojson_d4f={},
        json_doc={'info': {'out1': '', 'output_blocks': []}},
    )

    q1145_result_to_form_schema(
        request,
        func_id='ai_chat',
        cid='chat1',
        result={'Conversation': qchat('<p>Hello</p>')},
        proper_dict={},
    )

    assert request.ojson_schema[0]['type'] == 'html'
    rendered = str(request.ojson_schema[0]['initial'])
    assert 'class="elem-wrapper chat-wrap"' in rendered
    assert 'class="qchat"' in rendered
    assert 'class="fullscreen-square"' in rendered
    assert 'toggleFullscreen' in rendered
    assert 'role="log"' in rendered
    assert '<p>Hello</p>' in rendered
    assert 'scrollHeight' in rendered


def _render_table(table=None, **info):
    request = SimpleNamespace(
        pref={}, recall=False, remember=False, success=True, var_owner='', variant='', token='', cmd='',
        ojson_d4f={}, json_doc={'info': {'out1': '', 'output_blocks': [], **info}},
    )
    table = table or {'columns': ['Material', 'Quantity'], 'data': [['Cement', 5], ['Sand', 7]]}
    q1145_result_to_form_schema(
        request, func_id='x', cid='c1', result={'Method Comparison': table}, proper_dict={})
    return str(request.ojson_schema[0]['initial'])


RIGHT = 'tabulator-hozalign="right" tabulator-headerhozalign="right"'


def test_out_schema_formats_the_output_table_header_and_paging():
    rendered = _render_table(out_schema={'Method Comparison': {'attrs': {
        'col_widths': {'Material': {'max': 140, 'wrap': True}}, 'page_all': True}}})

    assert '<th tabulator-maxwidth="140" tabulator-formatter="textarea">Material</th>' in rendered
    assert f'<th {RIGHT}>Quantity</th>' in rendered
    assert 'data-page-all="true"' in rendered


def test_out_schema_page_all_overrides_table_out_all_for_one_table():
    schema = {'Method Comparison': {'attrs': {'page_all': False}}}

    assert 'data-page-all' not in _render_table(table_out_all=True, out_schema=schema)
    assert 'data-page-all="true"' in _render_table(table_out_all=True)


def test_numeric_output_columns_are_right_aligned_and_the_author_can_override():
    table = {'columns': ['Item', 'Note', 'Qty', 'Price'],
             'data': [['a', 'x', Qty(1000, 'kg'), '3 %'], ['b', 'y', Qty(2, 'kg'), '-']]}

    rendered = _render_table(table)
    assert f'<th {RIGHT}>Qty | kg</th>' in rendered
    assert f'<th {RIGHT}>Price</th>' in rendered
    assert '<th>Item</th>' in rendered and '<th>Note</th>' in rendered

    left = _render_table(table, out_schema={'Method Comparison': {'attrs': {'align': {'Qty': 'left', 'Price': 'left'}}}})
    assert RIGHT not in left
    assert '<th tabulator-hozalign="left" tabulator-headerhozalign="left">Qty | kg</th>' in left
