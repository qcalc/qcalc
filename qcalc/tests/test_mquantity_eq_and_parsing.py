import locale

import pytest

from qcore import Qty
from qcore.qc_mquantity import MeasureQuantity as MQ


def test_base_class_equality_never_raises():
    a = MQ('1 m')
    assert (a == MQ('1 s')) is False
    assert (a != MQ('1 s')) is True
    assert (a == 'abc') is False
    assert (a == None) is False  # noqa: E711
    assert a not in [MQ('1 s'), 'x', None]
    assert a == MQ('100 cm')
    assert MQ('0 degC') == MQ('32 degF')


def test_ordering_still_rejects_incompatible_units():
    with pytest.raises(TypeError):
        MQ('1 m') < MQ('1 s')
    with pytest.raises(TypeError):
        Qty('1 m') < Qty('1 s')


def test_base_class_is_hashable_and_consistent_with_equality():
    assert hash(MQ('1 m')) == hash(MQ('100 cm'))
    assert len({MQ('1 m'), MQ('100 cm'), MQ('1 s')}) == 2


def test_qty_equality_unchanged():
    assert Qty('1 m') == Qty('100 cm')
    assert Qty('1 m') != Qty('1 s')
    assert Qty('1 m') != 'abc'
    assert Qty('@m') == Qty('@m')
    assert Qty('@m') != Qty('0 m')


@pytest.mark.parametrize('text, expected', [
    ('1000 m', 1000.0), ('1.5 m', 1.5), ('1e3 m', 1000.0), ('.5 m', 0.5), ('-2.5e-3 m', -0.0025),
])
def test_number_parsing(text, expected):
    assert Qty(text).val == pytest.approx(expected)


def test_number_parsing_ignores_process_locale():
    previous = locale.setlocale(locale.LC_NUMERIC)
    for name in ('de_DE.UTF-8', 'German_Germany.1252', 'fr_FR.UTF-8', 'French_France.1252'):
        try:
            locale.setlocale(locale.LC_NUMERIC, name)
            break
        except locale.Error:
            continue
    else:
        pytest.skip('no comma-decimal locale installed')
    try:
        assert locale.localeconv()['decimal_point'] == ','
        assert Qty('1.5 m').val == 1.5
        assert Qty('1000.5 m').val == 1000.5
    finally:
        locale.setlocale(locale.LC_NUMERIC, previous)
