import qsett

qsett.init()

from types import SimpleNamespace

import pytest

import qutil.mod_tree as mt
from catalog import tag_index
from qutil import TreeNode, create_category_node


def _leaf(name, tags, title=None):
    return TreeNode(name, name, title=title or name, tags=tags, is_leaf=True, node_type='c')


def _naive(root, request, selected, mode):
    nodes = [n for n in root.depth_first() if n.is_leaf and n.is_active and n.is_visible(request)]
    result = []
    for node in nodes:
        tags = {t.strip().lower() for t in node.tag_list if t.strip()}
        if (mode == 'or' and tags & set(selected)) or (mode == 'and' and set(selected) <= tags):
            result.append(node)
    return sorted(result, key=lambda nd: (nd.title.lower(), nd.name.lower()))


@pytest.fixture
def root(monkeypatch):
    monkeypatch.setattr(mt, 'is_debug', lambda: False)
    monkeypatch.setattr(mt, 'user_name', lambda request=None: 'bob')
    TreeNode.setup('admin', 'demo', 'personal')
    root = create_category_node('calculators', 'calculators', 'Cals')
    finance = create_category_node('fin', 'fin', 'Fin')
    admin = create_category_node('admin', 'admin', 'Admin')
    root.add_child(finance)
    root.add_child(admin)
    finance.add_child(_leaf('loan', 'money, Loan, rates'))
    finance.add_child(_leaf('tax', 'money, tax'))
    finance.add_child(_leaf('bmi', 'health'))
    admin.add_child(_leaf('secret', 'money, internal'))
    admin.add_child(_leaf('untagged', ''))
    inactive = _leaf('old', 'money')
    inactive.is_active = False
    finance.add_child(inactive)
    monkeypatch.setattr(tag_index.QCals, 'calc_root', root, raising=False)
    monkeypatch.setattr(tag_index, '_index', None)
    return root


def _request(is_staff):
    return SimpleNamespace(user=SimpleNamespace(is_staff=is_staff, is_active=True))


@pytest.mark.parametrize('is_staff', [False, True])
@pytest.mark.parametrize('mode', ['or', 'and'])
@pytest.mark.parametrize('selected', [[], ['money'], ['money', 'loan'], ['money', 'internal'], ['nope'], ['health', 'tax']])
def test_nodes_by_tags_matches_naive_scan(root, is_staff, mode, selected):
    request = _request(is_staff)
    view = tag_index.get_tag_view(request)
    expected = [] if not selected else _naive(root, request, selected, mode)
    assert [n.id for n in view.nodes_by_tags(selected, mode)] == [n.id for n in expected]


def test_tag_items_hide_restricted_tags_from_regular_users(root):
    names = {i['name']: i['count'] for i in tag_index.get_tag_view(_request(False)).tag_items}
    assert names == {'money': 2, 'health': 1, 'loan': 1, 'rates': 1, 'tax': 1}


def test_tag_items_include_restricted_tags_for_staff_and_sort_by_count(root):
    items = tag_index.get_tag_view(_request(True)).tag_items
    assert items[0] == {'name': 'money', 'count': 3}
    assert {'name': 'internal', 'count': 1} in items
    assert [i['name'] for i in items[1:]] == sorted(i['name'] for i in items[1:])


def test_staff_view_does_not_pollute_cached_counts(root):
    tag_index.get_tag_view(_request(True)).tag_items
    names = {i['name'] for i in tag_index.get_tag_view(_request(False)).tag_items}
    assert 'internal' not in names


def test_index_rebuilds_when_catalog_root_changes(root, monkeypatch):
    request = _request(False)
    assert tag_index.get_tag_view(request).nodes_by_tags(['newtag']) == []
    new_root = create_category_node('calculators', 'calculators', 'Cals')
    new_root.add_child(_leaf('fresh', 'newtag'))
    monkeypatch.setattr(tag_index.QCals, 'calc_root', new_root)
    assert [n.id for n in tag_index.get_tag_view(request).nodes_by_tags(['newtag'])] == ['fresh']


def test_search_text_follows_later_field_changes():
    node = TreeNode('x', 'Gold', title='Gold Price', desc='Spot', tags='metal')
    assert node.search_text() == 'gold gold price metal spot'
    node.desc = 'Live Quote'
    assert node.search_text() == 'gold gold price metal live quote'


def test_search_tag_is_case_insensitive_and_hides_restricted_calculators(root, monkeypatch):
    from catalog import views
    from django.test import RequestFactory

    monkeypatch.setattr(views, 'render', lambda request, template, context: context)

    def run(user, qt):
        request = RequestFactory().get('/catalog/search_tag/', {'qt': qt})
        request.user = user
        return [n.id for n in views.search_tag(request)['calc_data']]

    assert run(_request(False).user, 'MONEY') == ['loan', 'tax']
    assert run(_request(True).user, 'money') == ['loan', 'secret', 'tax']
    assert run(_request(False).user, '') == []


def test_clone_detached_does_not_carry_the_tree(root):
    original = root.get_node_by_id('loan')
    clone = original.clone_detached('f:loan')
    assert (clone.id, clone.name, clone.title, clone.tag_list) == ('f:loan', 'loan', 'loan', original.tag_list)
    assert clone.parent is None and clone.children == []
    assert clone._nodes_index is not original._nodes_index
    clone.data['x'] = 1
    assert 'x' not in original.data

    favorites = create_category_node('favorites', 'favorites', 'Favs')
    favorites.add_child(clone)
    assert favorites.get_node_by_id('f:loan') is clone
    assert root.get_node_by_id('f:loan') is None
    assert original.parent is not None and original.parent.id == 'fin'


def test_search_text_follows_later_edits(root):
    node = root.get_node_by_id('loan')
    assert 'money' in node.search_text()
    node.title = 'Mortgage'
    node.desc = 'Monthly Payment'
    assert 'mortgage' in node.search_text() and 'monthly payment' in node.search_text()


def test_filter_uses_search_text(root, monkeypatch):
    request = _request(False)
    monkeypatch.setattr(mt, 'match_any', lambda terms, text, fuzzy=False, semantic=False: terms[0] in text)
    assert [n.id for n in root.filter(['rates'], request, True)] == ['loan']
    root.get_node_by_id('bmi').desc = 'Rates of body fat'
    assert sorted(n.id for n in root.filter(['rates'], request, True)) == ['bmi', 'loan']


def test_search_tag_view_lists_visible_nodes_only(root):
    from django.test import RequestFactory
    from catalog import views

    def ids(is_staff, tag):
        request = RequestFactory().get('/catalog/search_tag/', {'qt': tag})
        request.user = SimpleNamespace(is_staff=is_staff, is_active=True)
        return views.search_tag(request).content.decode()

    assert 'secret' not in ids(False, ' Money ')
    assert 'loan' in ids(False, ' Money ')
    assert 'secret' in ids(True, 'money')
    assert ids(False, '').strip() == ''
