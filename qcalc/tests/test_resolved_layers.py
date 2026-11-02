# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

from calc.views_form_data import q11425_form_data_resolve_layers as resolve


FARGS = {'quantity': 'L', 'mode': 'u2u', 'from_unit': ['ft'], 'note': None}


def test_the_arguments_are_returned_unchanged_without_other_layers():
    assert resolve(FARGS, {}, {}) == FARGS


def test_remembered_values_replace_the_arguments_and_url_values_replace_remembered_values():
    resolved = resolve(FARGS, {'quantity': 'M', 'mode': 'q2q'}, {'quantity': 'T'})

    assert resolved == {'quantity': 'T', 'mode': 'q2q', 'from_unit': ['ft'], 'note': None}


def test_a_dash_keeps_the_value_of_the_lower_layers():
    resolved = resolve(FARGS, {'quantity': 'M'}, {'quantity': '-', 'mode': '-'})

    assert resolved['quantity'] == 'M'
    assert resolved['mode'] == 'u2u'


def test_two_dashes_empty_the_field_and_three_dashes_empty_the_fields_not_in_the_url():
    resolved = resolve(FARGS, {'mode': 'q2q'}, {'quantity': 'M', 'from_unit': '--', '---': ''})

    assert resolved['quantity'] == 'M'  # | specified in the url, so not emptied by ---
    assert resolved['from_unit'] == ''
    assert resolved['mode'] == '' and resolved['note'] == ''


def test_values_that_are_not_text_are_taken_as_they_are():
    table = object()

    resolved = resolve(FARGS, {}, {'note': table, 'quantity': 5})

    assert resolved['note'] is table
    assert resolved['quantity'] == 5


def test_url_values_of_unknown_fields_are_ignored():
    assert 'other' not in resolve(FARGS, {}, {'other': 'x'})


def test_the_arguments_are_not_changed():
    fargs = dict(FARGS)

    resolve(fargs, {'quantity': 'M'}, {'mode': '--'})

    assert fargs == FARGS
