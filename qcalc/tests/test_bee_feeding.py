# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qsett

qsett.init()

import pytest

from calc.mod_hookctx import HookContext
from calculators.all.agriculture.cal_bee_feeding import (
    bee_feeding,
    bee_feeding__info,
    bee_feeding__input,
)


def test_changing_feed_type_resets_the_rate_to_a_compatible_default():
    info = bee_feeding__info()

    assert info['reload'] == {'feed_type': {'fields': ['feeding_rate_per_colony']}}
    assert bee_feeding__input(HookContext(resolved={'feed_type': 'syrup'})) == {
        'feeding_rate_per_colony': '0.5 L/unit/day',
    }
    assert bee_feeding__input(HookContext(resolved={'feed_type': 'dry'})) == {
        'feeding_rate_per_colony': '0.5 kg/unit/day',
    }


def test_posted_feed_type_determines_the_default_during_a_form_reload():
    ctx = HookContext(
        is_post=True,
        posted={'feed_type': ['dry']},
        resolved={'feed_type': 'syrup'},
    )

    assert bee_feeding__input(ctx)['feeding_rate_per_colony'] == '0.5 kg/unit/day'


def test_dry_sugar_with_otherwise_default_arguments_calculates_without_incompatible_units():
    result = bee_feeding(feed_type='dry')

    assert result['Feed Type'] == 'Dry sugar'
    assert result['Total Dry Sugar'].val == pytest.approx(250.0)
    assert result['Total Dry Sugar'].uom == 'kg'
    assert result['Sugar'].val == pytest.approx(250.0)
    assert result['Water'].val == 0


def test_stale_rendered_syrup_default_uses_the_dry_sugar_default():
    result = bee_feeding(feed_type='dry', feeding_rate_per_colony='0.5 L/day/unit')

    assert result['Total Dry Sugar'].val == pytest.approx(250.0)


def test_dry_sugar_rejects_a_nondefault_volume_rate():
    with pytest.raises(TypeError, match='Incompatible units'):
        bee_feeding(feed_type='dry', feeding_rate_per_colony='1 L/unit/day')
