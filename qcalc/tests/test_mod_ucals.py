# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import copy
from types import SimpleNamespace

import qsett

qsett.init()

import pytest

import calc.mod_ucals as mu
from calc.mod_ucals import UCals, get_uc_list, register_shared_cal, unregister_shared_cal
from qcore import qerror, qinfo
from qutil import create_category_node, TreeNode
from qutil.mod_tree import dict_to_tree

OWNER = 'bob'
CODE = (
    "def mycal(a=1):\n"
    "    return a\n"
    "\n"
    "def mycal__info():\n"
    "    return {'title': 'My calculator'}\n"
)


class _Store:
    """In-memory stand-in for the per-user QMeta, QMyCal and QFav stores."""

    def __init__(self, data=None):
        self.data = dict(data or {})
        self.cleared = []

    def getp1(self, key, default=None):
        return copy.deepcopy(self.data.get(key, default))

    def setp1(self, key, value):
        self.data[key] = copy.deepcopy(value)

    def delp1(self, key):
        return self.data.pop(key, None) is not None

    def getp(self, default=None):
        return copy.deepcopy(self.data) if self.data else default

    def clear(self, key=''):
        self.cleared.append(key)


@pytest.fixture
def env(monkeypatch):
    env = SimpleNamespace(meta=_Store(), mycal=_Store(), fav=_Store(), mem=_Store(), owner=OWNER, executed=[])
    monkeypatch.setattr(mu, 'QMeta', env.meta)
    monkeypatch.setattr(mu, 'QMyCal', env.mycal)
    monkeypatch.setattr(mu, 'QFav', env.fav)
    monkeypatch.setattr(mu, 'QMem', env.mem)
    monkeypatch.setattr(mu, 'user_name', lambda request=None: env.owner)

    def safe_exec(code):
        env.executed.append(code)
        return {}

    qcals = SimpleNamespace(
        safe_exec=safe_exec,
        func_title_desc_tags=lambda func_id, scope='': (f'Title {func_id}', f'Desc {func_id}', 'tag1'),
        calc_root=create_category_node('qcalc', 'qcalc', 'Standard'),
        pcalc_root=create_category_node('public', 'public', 'Public'),
        add_catagories_to_node=lambda parent, name, uname: parent,
        build_func_dict=lambda items, catalog, package, funcs, cals: None,
    )
    monkeypatch.setattr(mu, 'QCals', qcals)
    env.qcals = qcals
    return env


def _leaf(nid, **kw):
    node = TreeNode(nid=nid, name=nid, title=kw.get('title', nid), desc='', tags='', is_leaf=True, node_type='c')
    return node


def _tree_ids(tree_dict):
    tree = dict_to_tree(tree_dict)
    ids = set()

    def walk(node):
        ids.add(node.id)
        for child in node.children:
            walk(child)

    walk(tree)
    tree.delete_tree()
    return ids


# lists and code --------------------------------------------------------------------------------------------------

def test_the_list_of_created_calculators_defaults_to_empty(env):
    assert get_uc_list() == []

    env.meta.setp1('uc_list', ['a-bob'])

    assert get_uc_list() == ['a-bob']


def test_the_code_of_a_calculator_is_read_from_the_owners_store(env):
    env.mycal.setp1('mycal-bob', CODE)

    assert UCals().get_code('mycal') == CODE


def test_the_code_of_an_unknown_calculator_is_empty(env):
    assert UCals().get_code('nothing') == ''


# edit ------------------------------------------------------------------------------------------------------------

def test_a_new_calculator_is_registered_with_its_code_and_tree_node(env):
    results = UCals().edit_cal('', CODE)

    assert env.meta.getp1('uc_list') == ['mycal-bob']
    assert env.meta.getp1('uc_dict') == {'mycal-bob': 'created'}
    assert env.mycal.getp1('mycal-bob') == CODE
    assert 'mycal() is defined' in results
    assert "Run the calculator using 'mycal'" in results
    assert 'mycal-bob' in _tree_ids(env.meta.getp1('uc_tree'))
    assert env.executed == [CODE]  # | the code is validated by running it
    assert env.mem.cleared == ['mycal-bob']  # | remembered input of the old version is dropped


def test_the_tree_node_carries_the_title_description_and_tags(env):
    UCals().edit_cal('mycal', CODE)

    node = dict_to_tree(env.meta.getp1('uc_tree')).get_node_by_id('mycal-bob')

    assert node.title == 'Title mycal-bob'
    assert node.desc == 'Desc mycal-bob'
    assert node.tags == 'tag1'
    assert node.is_leaf is True


def test_editing_an_existing_calculator_does_not_register_it_twice(env):
    cals = UCals()
    cals.edit_cal('mycal', CODE)

    cals.edit_cal('mycal', CODE.replace('a=1', 'a=2'))

    assert env.meta.getp1('uc_list') == ['mycal-bob']
    assert 'a=2' in env.mycal.getp1('mycal-bob')
    ids = _tree_ids(env.meta.getp1('uc_tree'))
    assert sorted(i for i in ids if i.startswith('mycal')) == ['mycal-bob']


def test_the_list_of_created_calculators_stays_sorted(env):
    cals = UCals()
    cals.edit_cal('', CODE.replace('mycal', 'zeta'))
    cals.edit_cal('', CODE.replace('mycal', 'alpha'))

    assert env.meta.getp1('uc_list') == ['alpha-bob', 'zeta-bob']


def test_code_without_an_info_function_is_rejected(env):
    with pytest.raises(Exception, match=r'Meta __info\(\) not found'):
        UCals().edit_cal('', 'x = 1\n')

    assert env.meta.getp1('uc_list') is None


def test_a_name_that_does_not_match_the_code_is_rejected(env):
    with pytest.raises(Exception, match="mismatches with determind name 'mycal'"):
        UCals().edit_cal('other', CODE)

    assert env.mycal.getp1('other-bob') is None


def test_invalid_code_is_not_stored(env):
    def boom(code):
        raise RuntimeError('bad code')

    env.qcals.safe_exec = boom

    with pytest.raises(RuntimeError, match='bad code'):
        UCals().edit_cal('mycal', CODE)

    assert env.meta.getp1('uc_list') is None
    assert env.mycal.getp1('mycal-bob') is None


def test_a_failing_title_lookup_does_not_fail_the_edit(env):
    def fail(func_id, scope=''):
        raise RuntimeError('no title')

    env.qcals.func_title_desc_tags = fail

    results = UCals().edit_cal('mycal', CODE)

    assert "Run the calculator using 'mycal'" in results
    assert env.meta.getp1('uc_list') == ['mycal-bob']


# delete ----------------------------------------------------------------------------------------------------------

def test_a_deleted_calculator_is_removed_from_all_stores_and_the_tree(env):
    cals = UCals()
    cals.edit_cal('mycal', CODE)

    result = cals.del_cal('mycal')

    assert isinstance(result, qinfo)
    assert 'mycal deleted' in str(result)
    assert env.meta.getp1('uc_list') == []
    assert env.meta.getp1('uc_dict') == {}
    assert env.mycal.getp1('mycal-bob') is None
    assert 'mycal-bob' not in _tree_ids(env.meta.getp1('uc_tree'))


def test_deleting_an_unknown_calculator_is_an_error(env):
    result = UCals().del_cal('ghost')

    assert isinstance(result, qerror)
    assert 'ghost not found' in str(result)


def test_a_failure_while_deleting_is_reported_as_an_error(env):
    cals = UCals()
    cals.edit_cal('mycal', CODE)
    env.meta.setp1('uc_dict', {})  # | inconsistent state: the id is missing in the dict

    result = cals.del_cal('mycal')

    assert isinstance(result, qerror)
    assert 'could not be deleted' in str(result)


def test_deleting_with_an_empty_stored_tree_still_removes_the_calculator(env):
    env.meta.setp1('uc_list', ['mycal-bob'])
    env.meta.setp1('uc_dict', {'mycal-bob': 'created'})
    env.mycal.setp1('mycal-bob', CODE)

    result = UCals().del_cal('mycal')

    assert isinstance(result, qinfo)
    assert env.meta.getp1('uc_list') == []
    assert env.meta.getp1('uc_dict') == {}
    assert env.mycal.getp1('mycal-bob') is None


# tree ------------------------------------------------------------------------------------------------------------

def test_the_tree_holds_the_created_and_shared_branches(env):
    cals = UCals()
    cals.edit_cal('mycal', CODE)
    register_shared_cal('other-amy', 'tok')

    tree = UCals().get_tree()

    assert tree.get_node_by_id('created') is not None
    assert tree.get_node_by_id('mycal-bob') is not None
    assert tree.get_node_by_id('shared') is not None
    assert tree.get_node_by_id('other-amy') is not None
    assert tree.get_node_by_id('mycal-bob').uname == OWNER
    assert tree.get_node_by_id('favorites') is None


def test_the_tree_is_rebuilt_without_duplicating_branches(env):
    cals = UCals()
    cals.edit_cal('mycal', CODE)

    cals.get_tree()
    tree = cals.get_tree()

    assert [c.id for c in tree.children].count('created') == 1


def test_favorites_are_copies_of_the_calculators_found_under_a_prefixed_id(env):
    env.qcals.calc_root.add_child(_leaf('gold'))
    env.qcals.pcalc_root.add_child(_leaf('pub-amy'))
    UCals().edit_cal('mycal', CODE)
    env.fav.setp1('gold', 1)
    env.fav.setp1('pub-amy', 1)
    env.fav.setp1('mycal-bob', 1)
    env.fav.setp1('missing', 1)

    tree = UCals().get_tree()

    favorites = tree.get_node_by_id('favorites')
    assert favorites is not None
    assert sorted(c.id for c in favorites.children) == ['f:gold', 'f:mycal-bob', 'f:pub-amy']
    assert all(c.uname == favorites.uname for c in favorites.children)
    assert env.qcals.calc_root.get_node_by_id('gold').id == 'gold'  # | the original is untouched


def test_the_tree_of_a_user_without_calculators_has_only_the_root(env):
    tree = UCals().get_tree()

    assert tree.id == 'personal'
    assert tree.children == []


# shared calculators ----------------------------------------------------------------------------------------------

def test_a_shared_calculator_is_registered_in_the_lists_and_the_tree(env):
    register_shared_cal('other-amy__info', 'tok')

    assert env.meta.getp1('sc_list') == ['other-amy']
    assert env.meta.getp1('sc_dict') == {'other-amy': 'shared'}
    ids = _tree_ids(env.meta.getp1('sc_tree'))
    assert 'other-amy' in ids
    assert 'shared' in ids


def test_registering_a_shared_calculator_again_keeps_the_lists_unique(env):
    register_shared_cal('other-amy', 'tok')
    register_shared_cal('other-amy', 'tok')

    assert env.meta.getp1('sc_list') == ['other-amy']
    assert env.meta.getp1('sc_dict') == {'other-amy': 'shared'}


def test_registering_a_shared_calculator_again_keeps_the_stored_tree_loadable(env):
    register_shared_cal('other-amy', 'tok')
    register_shared_cal('other-amy', 'tok')

    assert _tree_ids(env.meta.getp1('sc_tree')) == {'shared', 'other-amy'}


def test_registering_a_shared_calculator_again_refreshes_its_title(env):
    register_shared_cal('other-amy', 'tok')
    env.qcals.func_title_desc_tags = lambda func_id, scope='': ('New title', 'New desc', 'new')

    register_shared_cal('other-amy', 'tok')

    node = dict_to_tree(env.meta.getp1('sc_tree')).get_node_by_id('other-amy')
    assert (node.title, node.desc, node.tags) == ('New title', 'New desc', 'new')


def test_unregistering_with_an_empty_stored_tree_still_removes_the_calculator(env):
    env.meta.setp1('sc_list', ['other-amy'])
    env.meta.setp1('sc_dict', {'other-amy': 'shared'})

    result = unregister_shared_cal('other-amy')

    assert isinstance(result, qinfo)
    assert env.meta.getp1('sc_list') == []
    assert env.meta.getp1('sc_dict') == {}


def test_shared_calculators_are_kept_sorted(env):
    register_shared_cal('b-amy', 'tok')
    register_shared_cal('a-amy', 'tok')

    assert env.meta.getp1('sc_list') == ['a-amy', 'b-amy']


def test_registering_survives_a_failing_title_lookup(env):
    def fail(func_id, scope=''):
        raise RuntimeError('no title')

    env.qcals.func_title_desc_tags = fail

    register_shared_cal('other-amy', 'tok')

    assert env.meta.getp1('sc_list') == ['other-amy']
    assert 'other-amy' not in _tree_ids(env.meta.getp1('sc_tree'))


def test_an_unregistered_calculator_is_removed_from_the_lists_and_the_tree(env):
    register_shared_cal('other-amy', 'tok')
    register_shared_cal('more-amy', 'tok')

    result = unregister_shared_cal('other-amy')

    assert isinstance(result, qinfo)
    assert env.meta.getp1('sc_list') == ['more-amy']
    assert env.meta.getp1('sc_dict') == {'more-amy': 'shared'}
    ids = _tree_ids(env.meta.getp1('sc_tree'))
    assert 'other-amy' not in ids
    assert 'more-amy' in ids


def test_unregistering_an_unknown_shared_calculator_is_an_error(env):
    result = unregister_shared_cal('ghost-amy')

    assert isinstance(result, qerror)
    assert 'ghost not found' in str(result)


# private and shared catalog creation -----------------------------------------------------------------------------

def test_the_private_catalog_places_each_calculator_under_its_category(env):
    cals = UCals()
    cals.uctg_dict = {'ucals.bob': 'bob', 'ucals.amy': 'amy'}
    cals.uc_dict = {'mine-bob': 'ucals.bob', 'hers-amy': 'ucals.amy'}
    request = SimpleNamespace()

    cals.create_catalog_calc_private(request)

    ids = _tree_ids(env.meta.getp1('uc_tree'))
    assert {'created', 'mine-bob', 'hers-amy'} <= ids
    assert request.ufunc_dict == {}
    assert cals.calc_root.get_node_by_id('created') is not None


def test_the_private_catalog_skips_calculators_whose_title_cannot_be_read(env):
    def fail(func_id, scope=''):
        if func_id == 'bad-bob':
            raise RuntimeError('broken')
        return 't', 'd', ''

    env.qcals.func_title_desc_tags = fail
    cals = UCals()
    cals.uctg_dict = {'ucals.bob': 'bob'}
    cals.uc_dict = {'good-bob': 'ucals.bob', 'bad-bob': 'ucals.bob'}

    cals.create_catalog_calc_private(SimpleNamespace())

    ids = _tree_ids(env.meta.getp1('uc_tree'))
    assert 'good-bob' in ids
    assert 'bad-bob' not in ids


def test_the_shared_catalog_is_not_created_when_nothing_is_shared(env):
    cals = UCals()
    cals.sctg_dict = {}
    request = SimpleNamespace()

    cals.create_catalog_calc_shared(request)

    assert env.meta.getp1('sc_tree') is None
    assert not hasattr(request, 'token')


def test_the_shared_catalog_lists_the_shared_calculators(env):
    cals = UCals()
    cals.sctg_dict = {'scals.amy': 'amy'}
    cals.sc_dict = {'her-amy': 'scals.amy'}
    request = SimpleNamespace()

    cals.create_catalog_calc_shared(request)

    ids = _tree_ids(env.meta.getp1('sc_tree'))
    assert {'shared', 'her-amy'} <= ids
    assert request.token == ''
    assert request.ufunc_dict == {}
