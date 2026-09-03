# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.shortcuts import render, redirect
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


def calc_dir(request: HtmxHttpRequest, **kwargs):
    template = 'gen-catalog-calc.html'
    ut.q1139_request_init(request)
    scat = kwargs['category'].lower()
    node = QCals.calc_root.get_node_by_id(scat)
    if not node:
        return not_found(request)

    parents = node.get_ancestor_ids_titles()
    cat = 'calc'
    navigation = calc_navigation(node.title, parents, cat)
    fav_dict = QFav.getp({})
    context = {
        "calc_navigation": mark_safe(navigation),
        "calc_data": node.children,
        "category": node,
        "request": request,
        "favorite_dict": fav_dict,
        "cat": cat,
        "title": "Standard Calculator Catalog",
        "show_fav_variants": False,
        "fav_var_data": None  # get_fav_data(fav_dict, jresp=False)
    }
    return ut.get_page(request, template, context, scat)


def pcalc_dir(request: HtmxHttpRequest, **kwargs):
    template = 'gen-catalog-calc.html'
    ut.q1139_request_init(request)
    scat = kwargs['category'].lower()
    node = QCals.pcalc_root.get_node_by_id(scat)
    if not node:
        return not_found(request)

    parents = node.get_ancestor_ids_titles()
    cat = 'pcalc'
    navigation = calc_navigation(node.title, parents, cat)
    fav_dict = QFav.getp({})
    context = {
        "calc_navigation": mark_safe(navigation),
        "calc_data": node.children,
        "category": node,
        "request": request,
        "favorite_dict": fav_dict,
        "cat": cat,
        "title": "Public Calculator Catalog",
        "show_fav_variants": False,
        "fav_var_data": None
    }
    return ut.get_page(request, template, context, scat)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def ucalc_dir(request: HtmxHttpRequest, **kwargs):
    scat = kwargs['category'].lower()
    ut.q1139_request_init(request)
    uc = UCals()
    uc.get_tree()
    node = uc.calc_root.get_node_by_id(scat)
    if not node:
        return not_found(request)

    template = 'gen-catalog-calc.html'
    parents = node.get_ancestor_ids_titles()
    cat = 'user'
    navigation = calc_navigation(node.title, parents, cat)
    fav_dict = QFav.getp({})
    context = {
        "calc_navigation": mark_safe(navigation),
        "calc_data": node.children,
        "category": node,
        "request": request,
        "favorite_dict": fav_dict,
        "cat": cat,
        "title": "Personal Calculator Catalog",
        "show_fav_variants": True,
        "fav_var_data": get_fav_data(fav_dict)  # , jresp=False
    }
    return ut.get_page(request, template, context, scat)


def calc_tree(request: HtmxHttpRequest):
    template = 'tree.html'
    ut.q1139_request_init(request)
    fav_dict = QFav.getp({})
    context = {
        "calc_data": QCals.calc_root.children,
        "request": request,
        "favorite_dict": fav_dict,
        "cat": "calc",
        "title": "Standrad Calculator Catalog",
        "show_fav_variants": False,
        "fav_var_data": None  # get_fav_data(fav_dict, jresp=False)
    }
    return ut.get_page(request, template, context, 'calc_tree')


def pcalc_tree(request: HtmxHttpRequest):
    template = 'tree.html'
    ut.q1139_request_init(request)
    fav_dict = QFav.getp({})
    context = {
        "calc_data": QCals.pcalc_root.children,
        "request": request,
        "favorite_dict": fav_dict,
        "cat": "pcalc",
        "title": "Public Calculator Catalog",
        "show_fav_variants": False,
        "fav_var_data": None
    }
    return ut.get_page(request, template, context, 'pcalc_tree')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def ucalc_tree(request: HtmxHttpRequest):
    template = 'tree.html'
    ut.q1139_request_init(request)
    uc = UCals()
    uc.get_tree()
    fav_dict = QFav.getp({})
    context = {
        "calc_data": uc.calc_root.children,
        "request": request,
        "favorite_dict": fav_dict,
        "cat": "user",
        "title": "Personal Calculator Catalog",
        "show_fav_variants": True,
        "fav_var_data": get_fav_data(fav_dict)  # , jresp=False
    }
    return ut.get_page(request, template, context, 'ucalc_tree')


def qty_tree(request: HtmxHttpRequest):
    template = 'treeq.html'
    context = {"qty_data": QCals.qty_root.children}
    return ut.get_page(request, template, context, 'qty_tree')





def qty_ulist(request: HtmxHttpRequest):
    lmt = request.GET.get('quantity', 'L').upper()
    mode = request.GET.get('mode', 'u2u').lower()
    val = request.GET.get('value', 1)
    url = f'/calc/add/?path=conv2/quantity/{lmt}/mode/{mode}/value/{val}/unit_cost/-/__info/{lmt}/---/'
    return redirect(url)


def qty_navigation(title, parents):
    paths = []
    for parent in parents:
        paths.append(f'''<a href="/catalog/qty/{parent[0]}" hx-get="/catalog/qty/{parent[0]}?part=1"
hx-target="closest .calc" hx-swap="outerHTML">{parent[1]}</a>''')
    paths.append(title)
    return ' > '.join(paths)


def qty_dir(request: HtmxHttpRequest, **kwargs):
    template = 'gen-catalog-qty.html'
    scat = kwargs['category'].lower()
    node = QCals.qty_root.get_node_by_id(scat)
    if not node:
        return not_found(request)
    parents = node.get_ancestor_ids_titles()
    navigation = qty_navigation(node.title, parents)
    context = {
        "qty_navigation": mark_safe(navigation),
        "qty_data": node.children,
        "category": node,
        "request": request,
    }
    help_path = get_help_path(scat, qty=True)
    context['help_html'] = help_path.as_posix() if help_path.exists() else "nohelp_qty.html"
    return ut.get_page(request, template, context, scat)


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


def search_func(request: HtmxHttpRequest):  # | not used
    sterm = request.GET.get('qf').strip()
    nodes = QCals.calc_root.search_nodes(sterm, request.user)
    context = {"calc_data": nodes}
    template = 'search-func.html'
    return render(request, template, context)


def search_pfunc(request: HtmxHttpRequest):  # | not used
    sterm = request.GET.get('qf').strip()
    nodes = QCals.pcalc_root.search_nodes(sterm, request.user)
    context = {"calc_data": nodes}
    template = 'search-func.html'
    return render(request, template, context)


def search_tag(request: HtmxHttpRequest):
    sterm = request.GET.get('qt').strip()
    nodes = QCals.calc_root.search_nodes_by_tag(sterm)
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
