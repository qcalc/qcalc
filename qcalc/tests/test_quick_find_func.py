# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import pytest

from calc import QCals
from calc.qcatalog import mod_qcals, mod_ucals
from qutil import create_category_node, TreeNode


@pytest.fixture
def names(monkeypatch):
    monkeypatch.setattr(QCals, 'qc_list', sorted(['bmi', 'bond', 'Conv', 'convert', 'zeta'], key=str.lower),
                        raising=False)
    monkeypatch.setattr(mod_qcals.QThread, 'get_req', classmethod(lambda cls: None))  # | standard list only


@pytest.mark.parametrize('query, expected', [
    ('conv', 'Conv'),  # | exact match ignoring case wins over the longer 'convert'
    ('CONV', 'Conv'),
    ('Conve', 'convert'),
    ('Z', 'zeta'),
    ('bm', 'bmi'),
    ('b', None),  # | ambiguous prefix
    ('nothing', None),
])
def test_quick_find_func_ignores_case_and_returns_the_stored_id(names, query, expected):
    assert QCals.quick_find_func(query) == expected


class _Meta:
    def __init__(self, lists):
        self.lists = lists

    def getp1(self, key, default=None):
        return self.lists.get(key, default)


@pytest.fixture
def user_lists(monkeypatch):
    def make(uc=(), sc=()):
        monkeypatch.setattr(QCals, 'qc_list', [], raising=False)
        monkeypatch.setattr(mod_qcals.QThread, 'get_req', classmethod(lambda cls: object()))
        monkeypatch.setattr(mod_qcals.PubCals, 'cal_list', [])
        monkeypatch.setattr(mod_qcals, 'QMeta', _Meta({'uc_list': sorted(uc, key=str.lower),
                                                       'sc_list': sorted(sc, key=str.lower)}))
    return make


@pytest.mark.parametrize('query, expected', [
    ('addlen', 'addlen-user'),  # | the name alone is exact although the id carries the owner
    ('Addlen', 'addlen-user'),
    ('addlen2', 'Addlen2-user'),
    ('addlen-user', 'addlen-user'),
    ('addlen-us', 'addlen-user'),
    ('add', None),  # | prefix of both
    ('user', None),  # | the owner is not a prefix
])
def test_user_calculator_name_is_an_exact_match(user_lists, query, expected):
    user_lists(uc=['addlen-user', 'Addlen2-user'])
    assert QCals.quick_find_func(query) == expected


def test_same_name_from_two_owners_in_one_list_is_ambiguous(user_lists):
    user_lists(sc=['addlen-bob', 'addlen-amy'])
    assert QCals.quick_find_func('addlen') is None
    assert QCals.quick_find_func('addlen-bob') == 'addlen-bob'


def test_own_calculator_wins_over_the_same_name_shared_with_me(user_lists):
    user_lists(uc=['addlen-user'], sc=['addlen-bob'])
    assert QCals.quick_find_func('addlen') == 'addlen-user'


def test_personal_search_finds_own_calculators_ignoring_case(monkeypatch):
    root = create_category_node('personal', 'personal', 'Personal')
    created = create_category_node('created', 'created', 'Created by Me')
    root.add_child(created)
    for cal_id in ('addlen-user', 'Addlen2-user', 'bmi-user'):
        created.add_child(TreeNode(nid=cal_id, name=cal_id, title=cal_id, is_leaf=True, node_type='c'))
    monkeypatch.setattr(mod_ucals, 'get_personal_tree', lambda: root)

    assert [n.id for n in mod_ucals.search_personal_nodes('*ADDLEN*')] == ['addlen-user', 'Addlen2-user']
    assert [n.id for n in mod_ucals.search_personal_nodes('*user*')] == ['addlen-user', 'Addlen2-user', 'bmi-user']
    assert mod_ucals.search_personal_nodes('*nothing*') == []
