# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

from datetime import date

import pytest

import qsett

qsett.init()

from qutil.mod_basic import (
    category_slug, css2floats, css2ints, css2set, css2strs, css2values, curdir_fullpath, doctrim,
    docstring_to_html, fchoices, iif, joinx, key_val, nzs, nzv, parameter_values, replace_parameter_values,
    replace_variables, replace_words, sort_by_val, truncate, vals2css, xpr_coeffs,
)


def test_fchoices_dict_gives_items():
    assert fchoices({1: 'a', 2: 'b', 3: 'c'}) == [(1, 'a'), (2, 'b'), (3, 'c')]


def test_fchoices_pairs_pass_through_as_list():
    expected = [(1, 'a'), (2, 'b'), (3, 'c')]
    assert fchoices(((1, 'a'), (2, 'b'), (3, 'c'))) == expected
    assert fchoices([(1, 'a'), (2, 'b'), (3, 'c')]) == expected


def test_fchoices_list_of_name_value_dicts():
    choices = [{'name': 'a', 'value': 1}, {'name': 'b', 'value': 2}, {'name': 'c', 'value': 3}]
    assert fchoices(choices) == [(1, 'a'), (2, 'b'), (3, 'c')]


def test_fchoices_plain_values_are_duplicated():
    assert fchoices(['a', 'b', 'c']) == [('a', 'a'), ('b', 'b'), ('c', 'c')]
    assert sorted(fchoices({'a', 'b', 'c'})) == [('a', 'a'), ('b', 'b'), ('c', 'c')]


def test_fchoices_empty_and_unsupported_input():
    assert fchoices([]) == []
    assert fchoices(()) == []
    assert fchoices(None) == []
    assert fchoices('abc') == []


def test_css2strs_string_list_and_tuple():
    assert css2strs('1, 2, 3') == ['1', '2', '3']
    assert css2strs([1, 2, 3]) == [1, 2, 3]
    assert css2strs((1, 2, 3)) == (1, 2, 3)
    assert css2strs('  ') == []


def test_css2set_normalizes_case_and_blanks():
    assert css2set(' A, b ,,C ') == {'a', 'b', 'c'}
    assert css2set({' X ', 'y', ''}) == {'x', 'y'}
    for blank in (None, '', 'none', 'NaN', 'NA', 'null'):
        assert css2set(blank) == set()


def test_css2floats_and_css2ints():
    assert css2floats('1, 2.5,-3') == [1.0, 2.5, -3.0]
    assert css2floats('') == []
    assert css2floats([1, 2]) == [1, 2]
    assert css2ints('1, 2.0, 3.9') == [1, 2, 3]
    assert css2ints('  ') == []
    with pytest.raises(ValueError):
        css2floats('1, x')


def test_css2values_infers_type():
    assert css2values('1, 2, 3') == ([1, 2, 3], int)
    assert css2values('1.5, 2') == ([1.5, 2.0], float)
    assert css2values('a, b') == (['a', 'b'], str)
    assert css2values('') == ([], float)
    assert css2values([]) == ([], float)
    assert css2values(['x', 'y']) == (['x', 'y'], str)


def test_css2values_dates_and_times():
    values, dtype = css2values('2024-01-02, 2024-03-04')
    assert dtype is date
    assert values == [date(2024, 1, 2), date(2024, 3, 4)]
    values, dtype = css2values('06:00, 12:00', time2val='hr')
    assert dtype is float
    assert values == [6.0, 12.0]


def test_css2values_reports_input_issue():
    with pytest.raises(ValueError, match='C2V'):
        css2values('1, 2, x')


def test_vals2css_and_iif_and_none_helpers():
    assert vals2css([1, 'a', 2.5]) == '1, a, 2.5'
    assert vals2css([1, 2], separator=';') == '1;2'
    assert iif(True, 'y', 'n') == 'y'
    assert iif(0, 'y', 'n') == 'n'
    assert nzv(None) == 0 and nzv(5) == 5
    assert nzs(None) == '' and nzs('x') == 'x'


def test_truncate():
    assert truncate('abc', 3) == 'abc'
    assert truncate('abcdef', 3) == 'abc... Truncated'


def test_joinx_skips_separators_around_blank_items():
    assert joinx(('hello', '', 'how', 'you', '?')) == 'hello how you ?'
    assert joinx(('a', 'b'), separator='-') == 'a-b'
    assert joinx(('a',)) == 'a'


def test_sort_by_val_and_category_slug():
    assert list(sort_by_val({'a': 3, 'b': 1, 'c': 2})) == ['b', 'c', 'a']
    assert category_slug('Health (Body), Other') == 'health-body'


def test_key_val_and_curdir_fullpath():
    assert key_val('k1/v1/k2/v2') == {'k1': 'v1', 'k2': 'v2'}
    assert curdir_fullpath('/a/b/ref.py', 'f.txt', 'sub').replace('\\', '/') == '/a/b/sub/f.txt'


def test_xpr_coeffs():
    assert xpr_coeffs('3x-a+2y2-9.5_zZ') == [3, -1, 2, -9.5]
    assert xpr_coeffs('2x - y') == [2, -1]
    assert xpr_coeffs('x + y') == [1, 1]
    assert xpr_coeffs('x + 2y - z') == [1, 2, -1]
    with pytest.raises(ValueError):
        xpr_coeffs('x^2')
    with pytest.raises(ValueError):
        xpr_coeffs('x**2')


def test_replace_words_respects_word_boundaries_and_case():
    assert replace_words('km/usd', ['USD'], 'bdt') == 'km/usd'
    assert replace_words('km/uSd', ['USD'], 'bdt', False) == 'km/bdt'
    assert replace_words('usdx usd', ['usd'], 'bdt') == 'usdx bdt'


def test_replace_variables():
    assert replace_variables('a + b * a', {'a': '1', 'b': '2'}) == '1 + 2 * 1'
    assert replace_variables('A + b', {'a': '1'}, case_sensitive=False) == '1 + b'
    assert replace_variables('A + b', {'a': '1'}) == 'A + b'


def test_parameter_values_numbers_and_quantities():
    xpr = "f(power='1.3 kW', factor=0.8, n=-2)"
    assert parameter_values(xpr) == {'power': 1.3, 'factor': 0.8, 'n': -2.0}
    assert parameter_values("f(Power=1)") == {'power': 1.0}
    assert parameter_values("f(Power=1)", case_sensitive=True) == {'Power': 1.0}


def test_replace_parameter_values_keeps_units_and_unknown_names():
    xpr = "f(power='1.3 kW', usage='150.0 hr/mo', factor=0.8)"
    result = replace_parameter_values(xpr, {'power': 1.25, 'factor': 0.75})
    assert result == "f(power='1.25 kW', usage='150.0 hr/mo', factor=0.75)"


def test_replace_parameter_values_case_sensitivity():
    assert replace_parameter_values('f(Power=1)', {'power': 2}) == 'f(Power=2)'
    assert replace_parameter_values('f(Power=1)', {'power': 2}, case_sensitive=True) == 'f(Power=1)'


def test_doctrim():
    assert doctrim('') == ''
    assert doctrim(None) == ''
    assert doctrim('\n    Summary.\n\n      detail\n    ') == 'Summary.\n\n  detail'
    assert doctrim('  one line  ') == 'one line'


def test_docstring_to_html_params_section():
    doc = 'Intro\nParameters:\n:param x: the x\n:param y: the y\nDone'
    html = docstring_to_html(doc)
    assert html.splitlines() == [
        '<p>Intro</p>',
        '<dl><dt><strong>Parameters:</strong></dt>',
        '<dd><strong>x</strong> → the x</dd>',
        '<dd><strong>y</strong> → the y</dd>',
        '</dl>',
        '<p>Done</p>',
    ]
    assert docstring_to_html('a\n\nb') == '<p>a</p>\n<br>\n<p>b</p>'
