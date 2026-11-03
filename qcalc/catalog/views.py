# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.shortcuts import render
from django.views.decorators.cache import cache_control
from qutil import HtmxHttpRequest, q1139_request_init, not_found
import qutil as ut
from calc import QSearch, search_result_nodes
from django.utils.safestring import mark_safe
from calc import QCals, UCals, QFav, get_help_path, QInput

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from calc.views_tabulator import get_fav_data
from catalog.tag_index import get_tag_view, normalize_tag_list
from catalog.fragment_cache import cached_fragment, apply_favorites
from calc import cur_loader
from calc.mod_ucals import get_personal_tree


def show_page(request: HtmxHttpRequest, **kwargs):
    pname = kwargs.get('pname', '')
    if pname == 'tree':
        return calc_tree(request)
    elif pname == 'search':
        return search_catalog(request)
    else:
        return ut.show_modal(request, "Show Page", f"Page {pname} not found")


def calc_navigation(title, parents, cat='calc'):
    paths = []
    for pid, ptitle in parents:  # | parent[0]=id, parent[1]=title
        paths.append(f'''<a href="/catalog/{cat}/{pid}" hx-get="/catalog/{cat}/{pid}?part=1"
hx-target="closest .calc" hx-swap="outerHTML">{ptitle}</a>''')
    paths.append(title)
    return ' > '.join(paths)


def _shared_calc_dir(request: HtmxHttpRequest, scat, root, cat, title):
    ut.q1139_request_init(request)
    node = root.get_node_by_id(scat)
    if not node:
        return not_found(request)

    def fragment_context():
        return {
            "calc_navigation": mark_safe(calc_navigation(node.title, node.get_ancestor_ids_titles(), cat)),
            "calc_data": node.children,
            "category": node,
            "request": request,
            "favorite_dict": {},  # per-user stars are applied after caching
            "cat": cat,
            "show_fav_variants": False,
            "fav_var_data": None,
        }

    html = cached_fragment(request, root, (cat, 'dir', node.id), 'catalog-calc-categories.html', fragment_context)
    context = {
        "content_html": mark_safe(apply_favorites(html, QFav.getp({}))),
        "category": node,
        "request": request,
        "cat": cat,
        "title": title,
    }
    return ut.get_page(request, 'gen-catalog-calc.html', context, scat)


def calc_dir(request: HtmxHttpRequest, **kwargs):
    return _shared_calc_dir(request, kwargs['category'].lower(), QCals.calc_root, 'calc',
                            "Standard Calculator Catalog")


def pcalc_dir(request: HtmxHttpRequest, **kwargs):
    return _shared_calc_dir(request, kwargs['category'].lower(), QCals.pcalc_root, 'pcalc',
                            "Public Calculator Catalog")


def _personal_context(request, fav_dict, **extra):
    return {
        "request": request,
        "favorite_dict": fav_dict,
        "cat": 'user',
        "title": "Personal Calculator Catalog",
        "show_fav_variants": True,
        "fav_var_data": get_fav_data(fav_dict),
        **extra,
    }


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def ucalc_dir(request: HtmxHttpRequest, **kwargs):
    scat = kwargs['category'].lower()
    ut.q1139_request_init(request)
    node = get_personal_tree().get_node_by_id(scat)
    if not node:
        return not_found(request)

    context = _personal_context(
        request, QFav.getp({}),
        calc_navigation=mark_safe(calc_navigation(node.title, node.get_ancestor_ids_titles(), 'user')),
        calc_data=node.children,
        category=node,
    )
    return ut.get_page(request, 'gen-catalog-calc.html', context, scat)


def _shared_calc_tree(request: HtmxHttpRequest, root, cat, title, page):
    ut.q1139_request_init(request)

    def fragment_context():
        return {
            "calc_data": root.children,
            "request": request,
            "favorite_dict": {},  # per-user stars are applied after caching
            "cat": cat,
            "show_fav_variants": False,
            "fav_var_data": None,
        }

    html = cached_fragment(request, root, (cat, 'tree'), 'include-tree-node-calc.html', fragment_context)
    context = {
        "tree_html": mark_safe(apply_favorites(html, QFav.getp({}))),
        "request": request,
        "cat": cat,
        "title": title,
    }
    return ut.get_page(request, 'tree.html', context, page)


def calc_tree(request: HtmxHttpRequest):
    return _shared_calc_tree(request, QCals.calc_root, 'calc', "Standrad Calculator Catalog", 'calc_tree')


def pcalc_tree(request: HtmxHttpRequest):
    return _shared_calc_tree(request, QCals.pcalc_root, 'pcalc', "Public Calculator Catalog", 'pcalc_tree')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def ucalc_tree(request: HtmxHttpRequest):
    ut.q1139_request_init(request)
    context = _personal_context(request, QFav.getp({}), calc_data=get_personal_tree().children)
    return ut.get_page(request, 'tree.html', context, 'ucalc_tree')


def _currency_stamp():
    # the quantity tree prints the currency rate date, so a rate refresh must produce a new fragment
    try:
        return cur_loader.timestamp()
    except Exception:
        return None


def qty_tree(request: HtmxHttpRequest):
    def fragment_context():
        return {"qty_data": QCals.qty_root.children}

    html = cached_fragment(request, QCals.qty_root, ('qty', 'tree', _currency_stamp()),
                           'include-tree-node-qty.html', fragment_context)
    return ut.get_page(request, 'treeq.html', {"tree_html": mark_safe(html)}, 'qty_tree')


def qty_navigation(title, parents):
    paths = []
    for parent in parents:
        paths.append(f'''<a href="/catalog/qty/{parent[0]}" hx-get="/catalog/qty/{parent[0]}?part=1"
hx-target="closest .calc" hx-swap="outerHTML">{parent[1]}</a>''')
    paths.append(title)
    return ' > '.join(paths)


def qty_dir(request: HtmxHttpRequest, **kwargs):
    scat = kwargs['category'].lower()
    node = QCals.qty_root.get_node_by_id(scat)
    if not node:
        return not_found(request)

    def fragment_context():
        help_path = get_help_path(scat, qty=True)
        return {
            "qty_navigation": mark_safe(qty_navigation(node.title, node.get_ancestor_ids_titles())),
            "qty_data": node.children,
            "category": node,
            "request": request,
            "help_html": help_path.as_posix() if help_path.exists() else "nohelp_qty.html",
        }

    html = cached_fragment(request, QCals.qty_root, ('qty', 'dir', node.id),
                           'catalog-qty-categories.html', fragment_context)
    context = {"content_html": mark_safe(html), "category": node, "request": request}
    return ut.get_page(request, 'gen-catalog-qty.html', context, scat)


def search_catalog(request: HtmxHttpRequest, scope='cx', idonly=False):
    sterm = request.GET.get('q', 'help').strip()
    # sterm = sterm if len(sterm) > 1 else 'help'
    template = 'gen-catalog-search.html'
    q1139_request_init(request)
    results = QSearch.perform_search(sterm, idonly)
    calc_nodes, pcalc_nodes, unit_nodes = search_result_nodes(results, scope)
    context = {
        "calc_data": calc_nodes,
        "pcalc_data": pcalc_nodes,
        "category": {'title': ''},
        "cat": 'calc',
        "help_html": '',
        "qty_data": unit_nodes,
        "search": True,
    }
    return ut.get_page(request, template, context, 'search')


def tag_browser(request: HtmxHttpRequest):
    q1139_request_init(request)
    mode = request.GET.get('mode', 'or').strip().lower()
    mode = 'or' if mode == 'or' else 'and'

    filter_text = request.GET.get('q', '').strip().lower()
    selected_tags = normalize_tag_list(request.GET.getlist('qt'))
    tag_view = get_tag_view(request)
    tag_items = tag_view.tag_items

    if filter_text:
        tag_items = [item for item in tag_items if filter_text in item['name']]

    calc_nodes = tag_view.nodes_by_tags(selected_tags, mode)

    defa_page_size = 25
    try:
        page_size = int(request.GET.get('page_size', defa_page_size))
    except (TypeError, ValueError):
        page_size = defa_page_size
    if page_size not in (10, 25, 50, 100, 250):
        page_size = defa_page_size

    try:
        page = int(request.GET.get('page', 1))
    except (TypeError, ValueError):
        page = 1

    total_rows = len(tag_items)
    total_pages = (total_rows + page_size - 1) // page_size if total_rows > 0 else 1
    page = max(1, min(page, total_pages))

    start_index = (page - 1) * page_size
    end_index = min(start_index + page_size, total_rows)
    paged_tag_items = tag_items[start_index:end_index]
    page_tag_names = [item['name'] for item in paged_tag_items]

    context = {
        'title': 'Tag Browser',
        'tag_items': paged_tag_items,
        'page_tag_names': page_tag_names,
        'selected_tags': selected_tags,
        'selected_count': len(selected_tags),
        'mode': mode,
        'filter_text': request.GET.get('q', '').strip(),
        'calc_data': calc_nodes,
        'page': page,
        'page_size': page_size,
        'page_size_options': [10, 25, 50, 100, 250],
        'total_rows': total_rows,
        'total_pages': total_pages,
        'start_row': start_index + 1 if total_rows > 0 else 0,
        'end_row': end_index,
        'category': {'title': ''},
        'cat': 'calc',
        'help_html': '',
        'search': True,
    }
    return ut.get_page(request, 'gen-catalog-tags.html', context, 'tag_browser')


def search_tag(request: HtmxHttpRequest):
    tags = normalize_tag_list([request.GET.get('qt') or ''])
    nodes = get_tag_view(request).nodes_by_tags(tags)
    context = {"calc_data": nodes}
    template = 'search-tag.html'
    return render(request, template, context)


def search_unit(request: HtmxHttpRequest):
    # check if a unit is being searched
    sterm = request.GET.get('qu').strip()  # dont lowercase yet
    # Unit abbreviations like "sec" are valid query terms even if they look like stop words.
    nodes = QCals.qty_root.search_nodes(sterm, request.user, exclude_stop_words=False)
    context = {"qty_data": nodes}
    template = 'search-unit.html'
    return render(request, template, context)


@csrf_exempt
@require_POST
def toggle_share(request):
    try:
        func_id = request.POST.get('func_id')
        input_id = int(request.POST.get('input_id'))
        var = QInput.get_var_info(input_id)
        token = var.access_token if var else ''
        action = request.POST.get('action')

        request.token = token
        request.is_public = True

        if action == 'delete':
            QInput.delete_shared_cal(func_id)
            token_state = False
        elif action == "add" and token:
            request.ufunc_dict = {}
            checked = QInput.save_shared_cal(func_id, token, check_only=False)
            token_state = (checked != "0")
        else:  # display
            token_state = QInput.is_shared_cal(func_id)

        request.token_state = token_state
        # | the request object is not passed to the template context by default when using render_to_string
        icon_html = render_to_string(
            'share_icon_social.html',
            {'func_id': func_id, 'input_id': input_id, 'action': "delete" if token_state else "add"},
            request=request
        )
        return HttpResponse(mark_safe(icon_html))
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
@require_POST
def toggle_favorite(request):
    try:
        func_id = request.POST.get('func_id')
        input_id = int(request.POST.get('input_id'))
        fav_state = request.POST.get('fav_state') == "1"
        mode = request.POST.get("mode")  # i = icon, s = button and icon

        var_input_list = QFav.getp1(func_id, [])
        if not fav_state and input_id not in var_input_list:
            var_input_list.append(input_id)
        elif fav_state and input_id in var_input_list:
            var_input_list.remove(input_id)

        if len(var_input_list) > 0:
            QFav.setp1(func_id, var_input_list)
        else:
            QFav.delp1(func_id)

        icon_html = render_to_string(
            'favorite_icon.html' if mode == 'i' else 'favorite_icon_social.html',
            {'func_id': func_id, 'input_id': input_id, 'fav_state': not fav_state}
        )
        return HttpResponse(mark_safe(icon_html))
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
