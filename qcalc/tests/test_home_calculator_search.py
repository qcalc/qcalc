# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

from django.template.loader import get_template
from django.test import RequestFactory
from qcore import qhtml

from calc import views
from calculators.all.general.user import cal_chat


def test_home_calculator_search_posts_to_q2cal():
    html = get_template(
        'include-search-calculator-onpage.html'
    ).render({}, request=RequestFactory().get('/'))

    assert 'hx-post="/calc/search-calculators/"' in html
    assert 'hx-target="#calculator-search-results"' in html
    assert 'name="query"' in html
    assert 'name="n" value="3"' in html


# def test_home_uses_calculator_search_include():
#     source = get_template('pages/home.html').template.source
#
#     assert "include 'include-search-calculator-onpage.html'" in source
#     assert "include 'include-search-catalog-onpage.html'" not in source


def test_calculator_search_endpoint_returns_only_q2cal_html(monkeypatch):
    monkeypatch.setattr(
        cal_chat,
        'q2cal',
        lambda query, n: qhtml(
            '<div class="mb-2"><a href="/calc/bmi/">BMI</a></div>'
        ),
    )
    request = RequestFactory().post(
        '/calc/search-calculators/',
        {'query': 'calculate bmi', 'n': '3'},
    )

    response = views.q2cal_search(request)
    html = response.content.decode()

    assert response.status_code == 200
    assert html == '<div class="mb-2"><a href="/calc/bmi/">BMI</a></div>'
    assert 'section-outbtns' not in html
    assert 'Browse' not in html
    assert 'Express' not in html
