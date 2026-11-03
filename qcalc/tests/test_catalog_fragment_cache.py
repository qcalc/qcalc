import qsett

qsett.init()

from pathlib import Path

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory
from django.utils.safestring import mark_safe

import qutil.mod_tree as mt
from calc import QCals
from catalog import fragment_cache, views
from qutil import TreeNode, create_category_node


class _Fav:
    def __init__(self, data):
        self.data = data

    def getp(self, default=None):
        return self.data or default


def _leaf(name, title):
    return TreeNode(name, name, title=title, desc=f'{title} desc', is_leaf=True, node_type='c')


@pytest.fixture
def catalog(monkeypatch):
    monkeypatch.setattr(mt, 'is_debug', lambda: False)
    monkeypatch.setattr(fragment_cache, 'is_debug', lambda: False)
    TreeNode.setup('admin', 'demo', 'personal')
    root = create_category_node('calculators', 'calculators', 'Cals')
    fin = create_category_node('fin', 'fin', 'Fin')
    admin = create_category_node('fin-admin', 'admin', 'Admin')
    root.add_child(fin)
    fin.add_child(_leaf('loan', 'Loan'))
    fin.add_child(_leaf('tax', 'Tax'))
    fin.add_child(admin)
    admin.add_child(_leaf('secret', 'Secret'))
    root.update_all_descendant_leafs_count()
    monkeypatch.setattr(QCals, 'calc_root', root, raising=False)
    monkeypatch.setattr(QCals, 'catalog_version', QCals.catalog_version + 1)
    fragment_cache._fragments.clear()
    fragment_cache._state.update(version=None, has_personal={})
    monkeypatch.setattr(views, 'QFav', _Fav({}))
    monkeypatch.setattr(views.ut, 'q1139_request_init', lambda request: None)
    return root


def _get(view, path, user, **kwargs):
    request = RequestFactory().get(path + '?part=1')
    request.user = user
    return view(request, **kwargs).content.decode()


def _staff():
    return User(username='boss', is_staff=True, is_active=True)


def test_page_shows_only_what_the_viewer_may_see(catalog):
    anon = _get(views.calc_dir, '/catalog/calc/fin/', AnonymousUser(), category='fin')
    staff = _get(views.calc_dir, '/catalog/calc/fin/', _staff(), category='fin')
    assert 'Loan' in anon and 'Tax' in anon and 'Secret' not in anon and '(1)' not in anon
    assert 'Secret' in staff or 'fin-admin' in staff
    assert '(1)' in staff


def test_cached_page_matches_uncached_template(catalog, monkeypatch):
    monkeypatch.setattr(views, 'QFav', _Fav({'loan': [0]}))
    for user in (AnonymousUser(), _staff()):
        for _ in range(2):  # miss, then hit
            cached = _get(views.calc_dir, '/catalog/calc/fin/', user, category='fin')

        node = catalog.get_node_by_id('fin')
        request = RequestFactory().get('/catalog/calc/fin/?part=1')
        request.user = user
        legacy = views.ut.get_page(request, 'gen-catalog-calc.html', {
            "calc_navigation": mark_safe(views.calc_navigation(node.title, node.get_ancestor_ids_titles(), 'calc')),
            "calc_data": node.children, "category": node, "request": request,
            "favorite_dict": {'loan': [0]}, "cat": 'calc', "title": "Standard Calculator Catalog",
            "show_fav_variants": False, "fav_var_data": None,
        }, 'fin').content.decode()
        assert cached == legacy


def test_fragment_is_rendered_once_per_visibility_class(catalog, monkeypatch):
    calls = []
    real = fragment_cache.render_to_string
    monkeypatch.setattr(fragment_cache, 'render_to_string',
                        lambda *a, **k: calls.append(a[0]) or real(*a, **k))
    for _ in range(3):
        _get(views.calc_dir, '/catalog/calc/fin/', AnonymousUser(), category='fin')
    _get(views.calc_dir, '/catalog/calc/fin/', _staff(), category='fin')
    assert calls.count('catalog-calc-categories.html') == 2


def test_catalog_change_invalidates_fragments(catalog):
    before = _get(views.calc_dir, '/catalog/calc/fin/', AnonymousUser(), category='fin')
    catalog.get_node_by_id('fin').add_child(_leaf('fresh', 'Fresh one'))
    assert 'Fresh one' not in _get(views.calc_dir, '/catalog/calc/fin/', AnonymousUser(), category='fin')
    QCals.bump_catalog_version()
    after = _get(views.calc_dir, '/catalog/calc/fin/', AnonymousUser(), category='fin')
    assert 'Fresh one' in after and 'Fresh one' not in before


def test_favorites_are_applied_per_user_without_touching_the_cache(catalog, monkeypatch):
    anon = AnonymousUser()
    plain = _get(views.calc_dir, '/catalog/calc/fin/', anon, category='fin')
    assert 'icon-star-full2' not in plain

    monkeypatch.setattr(views, 'QFav', _Fav({'loan': [0], 'tax': [5]}))
    starred = _get(views.calc_dir, '/catalog/calc/fin/', anon, category='fin')
    assert starred.count('icon-star-full2') == 1  # loan only; tax has only a variant favorite
    assert starred.count('icon-star-empty3') == 1

    monkeypatch.setattr(views, 'QFav', _Fav({}))
    assert _get(views.calc_dir, '/catalog/calc/fin/', anon, category='fin') == plain


def test_tree_page_applies_favorites(catalog, monkeypatch):
    monkeypatch.setattr(views, 'QFav', _Fav({'tax': [0]}))
    html = _get(views.calc_tree, '/catalog/calc/', AnonymousUser())
    assert 'Loan' in html and html.count('icon-star-full2') == 1 and 'Secret' not in html


def test_personal_trees_are_not_shared(catalog):
    catalog.get_node_by_id('fin').add_child(create_category_node('personal', 'personal', 'Personal'))
    QCals.bump_catalog_version()
    fragment_cache._fragments.clear()
    _get(views.calc_dir, '/catalog/calc/fin/', AnonymousUser(), category='fin')
    assert fragment_cache._fragments == {}


def test_qty_pages_match_uncached_templates(catalog, monkeypatch):
    qty = create_category_node('units', 'units', 'Units')
    length = create_category_node('length', 'length', 'Length')
    qty.add_child(length)
    unit = TreeNode('ft', 'ft', title='Foot', desc='a foot', is_leaf=True, node_type='u')
    length.add_child(unit)
    qty.update_all_descendant_leafs_count()
    monkeypatch.setattr(QCals, 'qty_root', qty, raising=False)
    monkeypatch.setattr(views, 'get_help_path', lambda scat, qty=False: Path('missing-help.html'))
    monkeypatch.setattr(views, 'cur_loader', type('L', (), {'timestamp': staticmethod(lambda: 1)}))

    user = AnonymousUser()
    cached = _get(views.qty_dir, '/catalog/qty/length/', user, category='length')
    request = RequestFactory().get('/catalog/qty/length/?part=1')
    request.user = user
    legacy = views.ut.get_page(request, 'gen-catalog-qty.html', {
        "qty_navigation": mark_safe(views.qty_navigation('Length', length.get_ancestor_ids_titles())),
        "qty_data": length.children, "category": length, "request": request,
        "help_html": "nohelp_qty.html",
    }, 'length').content.decode()
    assert 'Foot' in cached and cached == legacy

    tree = _get(views.qty_tree, '/catalog/qty/', user)
    assert 'Foot' in tree and 'Length' in tree
