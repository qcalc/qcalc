# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest
import qsett

qsett.init()

from django.template.loader import get_template, render_to_string

import qvars
from calc import QPref
from calculators.all.general.user import cal_ucache as cu
from qutil import QThread


def test_slider_script_does_not_touch_document_body_at_load():
    # qslider.js is loaded from <head> where document.body is still null; a
    # body.addEventListener at load time aborts the script before the menu
    # handler (qcalc_ToggleSlider) is defined.
    source = (Path(qvars.__file__).parent / 'qsite' / 'static' / 'qsite' / 'js' / 'qslider.js').read_text(encoding='utf-8')

    assert 'document.body.addEventListener' not in source
    assert 'window.qcalc_ToggleSlider = ' in source


def test_pref_calculator_exposes_slider_in_general_pane():
    info = cu.pref__info()

    general = info['input_blocks'][0]['tabs'][0]
    assert general['title'] == 'General'
    assert 'slider' in [f.strip() for f in general['fields'].split(',')]
    assert info['schema']['slider']['help_text']


def test_pref_calculator_input_and_signature_stay_in_sync(monkeypatch):
    monkeypatch.setattr(QThread, 'get_req', classmethod(lambda cls: SimpleNamespace(recall=False)))
    monkeypatch.setattr(QPref, 'getp', lambda: {})

    initials = cu.pref__input({})
    params = list(inspect.signature(cu.pref).parameters)

    assert set(params) == set(initials)


@pytest.mark.parametrize('enabled, checked, icon, other_icon', [
    (True, 'true', 'icon-checkbox-checked2', 'icon-checkbox-unchecked2'),
    (False, 'false', 'icon-checkbox-unchecked2', 'icon-checkbox-checked2'),
])
def test_calculator_menu_item_reflects_card_slider_state(enabled, checked, icon, other_icon):
    html = render_to_string('insert-calculator-section-inpbtns.html', {
        'input': {'cid': 'c7', 'doc': {'name': 'bmi', 'info': {'calculate': 'Calculate'}}},
        'request': SimpleNamespace(pref={'slider_enabled': enabled}),
    })

    assert 'id="slider-c7"' in html
    assert f'aria-checked="{checked}"' in html
    assert "qcalc_ToggleSlider(this, 'c7')" in html
    assert icon in html
    assert other_icon not in html
    assert 'Numeric Slider' in html


# gen-calculator-content-* are generated from insert-calculator-section-inpbtns.html
# by gulp (setup/run_gulp.bat); this fails when the generated files are stale.
@pytest.mark.parametrize('template', [
    'gen-calculator-content-l2r.html',
    'gen-calculator-content-l2r2.html',
    'gen-calculator-content-lr.html',
    'gen-calculator-content-lr2.html',
    'gen-calculator-content-t2b.html',
    'gen-calculator-content-t2b2.html',
    'gen-calculator-content-tb.html',
    'gen-calculator-content-tb2.html',
    'insert-calculator-section-inpbtns.html',
])
def test_every_calculator_menu_has_the_slider_item(template):
    source = get_template(template).template.source

    assert "qcalc_ToggleSlider(this, '{{ input.cid }}')" in source
    assert 'insert-calculator-menu-slider' not in source
