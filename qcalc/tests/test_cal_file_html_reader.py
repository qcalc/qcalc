# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qsett

qsett.init()

from calculators.all.general.file.cal_file import html_reader
from qcore import qhtml


def test_html_reader_code_mode_shows_source():
    rendered = html_reader(
        html_text='<h1>Hello</h1><p>World</p>',
        mode='Text',
        display='Code',
    )
    assert isinstance(rendered, qhtml)
    out = str(rendered)
    assert '&lt;h1&gt;Hello&lt;/h1&gt;' in out
    assert '&lt;p&gt;World&lt;/p&gt;' in out


def test_html_reader_text_mode_strips_tags():
    rendered = html_reader(
        html_text='<h1>Hello</h1><p>World</p>',
        mode='Text',
        display='Text',
    )
    out = str(rendered)
    assert 'Hello World' in out
    assert '&lt;h1&gt;' not in out
    assert '&lt;p&gt;' not in out


def test_html_reader_formatted_mode_renders_safely():
    rendered = html_reader(
        html_text='<h1>Hello</h1><a href="javascript:alert(1)">click</a><script>alert(1)</script>',
        mode='Text',
        display='Formatted',
    )
    out = str(rendered)
    assert '<h1>Hello</h1>' in out
    assert '<script>' not in out
    assert 'javascript:alert(1)' not in out
    assert '<a>click</a>' in out


def test_html_reader_display_text_mode_for_plain_text_output():
    rendered = html_reader(
        html_text='<b>Hello</b>',
        mode='Text',
        display='Text',
    )
    out = str(rendered)
    assert 'Hello' in out
    assert '&lt;b&gt;' not in out
