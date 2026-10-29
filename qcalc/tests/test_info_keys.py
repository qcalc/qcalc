# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett
import pytest

qsett.init()

from calc import QCals
from calc.mod_prefs import PREF_OPTIONS
from calc.views_info_meta import q1141_read_func_meta
from calculators.all.general.author.mod_mycal_validation import INFO_SCHEMA, INFO_VALIDATOR
from qutil.mod_code_info import build_info
from qutil.mod_info_keys import (
    ALL_INFO_KEYS,
    INFO_KEYS,
    INFO_OVERRIDE_KEYS,
    INTERNAL_KEYS,
    LEGACY_KEYS,
    PUBLIC_KEYS,
)

# Behavior before the registry existed, kept literally so that a change is a conscious one.
GENERATED_KEYS = (
    'title', 'desc', 'calculate', 'layout', 'interactive',
    'input_columns', 'output_columns', 'input_blocks', 'output_blocks',
    'showhide', 'anyof', 'autofill', 'related', 'images', 'onsubmit', 'script', 'inserts',
    'step2', 'single_instance', 'single_instance_key', 'provides_data', 'consumes_data',
    'schema', 'kins', 'tags', 'proper', 'remember', 'table_out_all', 'fargs',
)
INTERNAL = {'name', 'help', 'clean', 'template', 'qsel2', 'qlist', 'table_in', 'table_out', 'xpr', 'url', 'loop', 'cost'}
LEGACY = {'row', 'col', 'inp1', 'out1'}
OVERRIDABLE = {
    'title', 'desc', 'calculate', 'schema', 'interactive', 'autofill', 'related', 'showhide', 'anyof', 'row', 'col',
    'layout', 'inp1', 'out1', 'input_columns', 'output_columns', 'input_blocks', 'output_blocks', 'onsubmit',
    'script', 'kins', 'tags', 'xpr', 'url', 'loop', 'step2', 'cost', 'single_instance', 'single_instance_key',
    'provides_data', 'consumes_data', 'inserts', 'table_out_all', 'proper', 'remember',
}
PUBLIC = {key for key, spec in INFO_KEYS.items() if spec.kind == 'public'}
# key found in a library calculator but used by nothing
IGNORED_LIBRARY_KEYS = {'initial'}


def test_registry_matches_previous_behavior():
    assert PUBLIC_KEYS == GENERATED_KEYS
    assert set(INTERNAL_KEYS) == INTERNAL
    assert set(LEGACY_KEYS) == LEGACY
    assert set(INFO_OVERRIDE_KEYS) == OVERRIDABLE


def test_mycal_validation_accepts_every_public_key_and_inp1_out1_only():
    accepted = set(INFO_SCHEMA['properties'])

    assert accepted == PUBLIC | {'inp1', 'out1'}
    assert not accepted & set(INTERNAL_KEYS)
    assert accepted <= ALL_INFO_KEYS


def test_mycal_validation_accepts_the_formerly_missing_keys():
    info = {
        'step2': [{'step': 'run', 'func': 'bmr', 'caption': 'Calculate BMR', 'spec': {'weight': 'weight'}},
                  {'step': 'run', 'spec': '~Volume'}],
        'single_instance': True,
        'single_instance_key': 'rates_master',
        'provides_data': {'dataset_type': 't', 'dataset_key': 'k'},
        'consumes_data': {'dataset_type': 't', 'dataset_key': 'k'},
        'remember': False,
        'table_out_all': True,
        'api': True,
        'fargs': {'t': 300},
    }

    assert not list(INFO_VALIDATOR.iter_errors(info))


@pytest.mark.parametrize('bad', [
    {'remember': 'no'},
    {'table_out_all': 1},
    {'step2': [{'caption': 'x'}]},
    {'single_instance_key': 5},
    {'provides_data': 'k'},
    {'xpr': True},
])
def test_mycal_validation_still_rejects_bad_values_and_internal_keys(bad):
    assert list(INFO_VALIDATOR.iter_errors(bad))


def test_generated_info_passes_mycal_validation():
    result = build_info('def calc(x=1.0)', hints={
        'interactive': True, 'remember': False, 'table_out_all': True,
        'extra': "{'step2': [{'step': 'run'}], 'single_instance': True}",
    })

    assert not list(INFO_VALIDATOR.iter_errors(result.spec))


def test_internal_keys_are_not_generated():
    for key in INTERNAL_KEYS:
        assert key not in PUBLIC_KEYS


def test_every_key_of_the_request_info_is_classified(monkeypatch):
    monkeypatch.setattr(QCals, 'run_func_info', classmethod(lambda cls, func_id, scope='qpots': {}))
    info = q1141_read_func_meta('bmi')['info']

    assert set(info) <= ALL_INFO_KEYS


def test_every_overridable_key_has_a_default_in_the_request_info(monkeypatch):
    monkeypatch.setattr(QCals, 'run_func_info', classmethod(lambda cls, func_id, scope='qpots': {}))
    info = q1141_read_func_meta('bmi')['info']

    assert set(INFO_OVERRIDE_KEYS) <= set(info)


def test_calculator_level_preferences_are_public_keys():
    for key, option in PREF_OPTIONS.items():
        if option.get('calc'):
            assert INFO_KEYS[key].kind == 'public'
            assert INFO_KEYS[key].override


def test_library_calculators_use_only_classified_info_keys():
    unknown = {}
    for func_id in QCals.qc_list:
        try:
            info = QCals.run_func_info(func_id)
        except Exception:
            continue
        for key in set(info) - ALL_INFO_KEYS - IGNORED_LIBRARY_KEYS:
            unknown.setdefault(key, []).append(func_id)

    assert not unknown, f'Unclassified __info keys (add them to qutil/mod_info_keys.py): {unknown}'


@pytest.mark.parametrize('key', sorted(INTERNAL))
def test_internal_keys_never_come_from_the_author_unless_overridable(key):
    assert (key in INFO_OVERRIDE_KEYS) == (key in {'xpr', 'url', 'loop', 'cost'})
