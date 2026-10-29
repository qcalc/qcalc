# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import pytest

from qcore import Qty


def test_equality_and_ordering_across_offset_units():
    assert Qty('0 degC') == Qty('32 degF')
    assert Qty('0 degC') == Qty('273.15 K')
    assert hash(Qty('0 degC')) == hash(Qty('32 degF'))
    assert Qty('100 degC') > Qty('100 degF')
    assert Qty('0 degC') < Qty('33 degF')
    assert Qty('0 degC') <= Qty('32 degF')
    assert Qty('0 degC') >= Qty('32 degF')
    assert not Qty('0 degC') < Qty('32 degF')


def test_point_plus_point_converts_then_adds():
    result = Qty('20 degC') + Qty('68 degF')
    assert result.uom == 'degC'
    assert result.val == pytest.approx(40)
    assert ((Qty('20 degC') + Qty('30 degC')) / 2).val == pytest.approx(25)


def test_point_minus_point_is_interval_in_kelvin():
    for other, expected in (('20 degC', 10), ('68 degF', 10)):
        diff = Qty('30 degC') - Qty(other)
        assert diff.uom == 'K'
        assert diff.val == pytest.approx(expected)


def test_point_with_interval():
    assert (Qty('30 degC') + Qty('5 K')).val == pytest.approx(35)
    assert (Qty('30 degC') + Qty('5 K')).uom == 'degC'
    assert (Qty('30 degC') - Qty('5 K')).val == pytest.approx(25)
    assert (Qty('86 degF') + Qty('5 K')).val == pytest.approx(95)  # 5 K interval = 9 degF
    assert (Qty('5 K') + Qty('30 degC')).val == pytest.approx(35)
    assert (Qty('5 K') + Qty('30 degC')).uom == 'degC'


def test_interval_minus_point_is_rejected():
    with pytest.raises(TypeError):
        Qty('5 K') - Qty('30 degC')


def test_in_base_units_includes_offset():
    base = Qty('25 degC').in_base_units()
    assert base.val == pytest.approx(298.15)
    assert base.uom == 'K'


def test_plain_units_unchanged():
    assert (Qty('1 m') + Qty('50 cm')).val == pytest.approx(1.5)
    assert (Qty('1 m') - Qty('50 cm')).val == pytest.approx(0.5)
    assert Qty('1 m') > Qty('50 cm')
    assert Qty('100 cm') == Qty('1 m')
    with pytest.raises(TypeError):
        Qty('1 m') + Qty('1 s')
