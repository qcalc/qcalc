# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qsett

qsett.init()

from pathlib import Path

from calculators.all.general.user.cal_share import embed_code, embed_code__help

JS = Path(__file__).resolve().parent.parent / 'qsite/static/qsite/js/qembed.js'


def test_embed_code_snippet():
    out = embed_code('bmi', '600', True)
    assert 'data-qcalc=&quot;bmi&quot;' in out['Embed code']
    assert 'data-height' not in out['Embed code']
    assert 'qembed.js' in out['Embed code']
    assert '/calc/core/bmi/?embed=1&amp;run' in out['Note']


def test_embed_code_iframe_snippet():
    out = embed_code('bmi', '600', True)['Embed code (no JavaScript)']
    assert '&lt;iframe src=&quot;' in out
    assert '/calc/core/bmi/?embed=1&amp;run' in out
    assert 'height=&quot;600&quot;' in out


def test_embed_code_iframe_percent_height():
    out = embed_code('bmi', ' 100% ', True)['Embed code (no JavaScript)']
    assert 'height=&quot;100%&quot;' in out


def test_embed_code_rejects_bad_height():
    assert 'Height must be' in embed_code('bmi', '600"><script>', True)


def test_embed_code_norun_and_escaping():
    out = embed_code('a"><script>', '480', False)
    assert 'data-run' in out['Embed code']
    assert '<script>' not in out['Note']
    assert '<script>' not in out['Embed code (no JavaScript)']
    assert 'embed=1&amp;run' not in out['Note']


def test_embed_code_requires_id():
    assert 'missing' in embed_code('')


def test_powered_by_only_in_embed_mode():
    from django.test import Client
    c = Client(HTTP_HOST='localhost')
    assert 'Powered by' in c.get('/calc/core/bmi/?embed=1&run').content.decode()
    assert 'Powered by' not in c.get('/calc/core/bmi/?run').content.decode()


def test_embed_mode_survives_htmx_post():
    from django.test import Client
    c = Client(HTTP_HOST='localhost')
    data = {'cid': 'bmi__abc123', 'input_id': 0}  # invalid input still renders the output chrome

    def post(page_url):
        return c.post('/calc/bmi/', data, HTTP_HX_REQUEST='true', HTTP_HX_CURRENT_URL=page_url).content.decode()

    assert 'section-outbtns' not in post('http://localhost/calc/core/bmi/?embed=1&run')
    assert 'section-outbtns' in post('http://localhost/calc/core/bmi/?run')


def test_embed_code_help():
    html = embed_code__help()
    assert '100%' in html and 'iframe' in html and 'auto-fits' in html


def test_loader_and_child_roles_in_one_file():
    src = JS.read_text(encoding='utf-8')
    assert "hasAttribute('data-child')" in src
    assert '[data-qcalc]' in src
    assert 'e.origin !== origin' in src
