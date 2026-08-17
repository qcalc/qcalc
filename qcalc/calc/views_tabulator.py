# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.http import JsonResponse
from django.shortcuts import render
from django.apps import apps
import json
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods
from qutil import is_loggedin, fid2owner, user_name
from django.views.decorators.cache import never_cache


@never_cache
def scroll_input(request, scope, item_id, cid):
    qryset = get_input_data(request, scope, item_id, jresp=False)
    return render(request, 'input_scroller.html',
                  {'scope': scope, 'item_id': item_id, 'qryset': qryset, 'cid': cid})


def tabulate_input(request, scope, item_id, cid):
    cal_id, cal_name, cal_owner = fid2owner(item_id)
    is_owner = (user_name(request) == cal_owner)
    return render(request, 'input_tabulator.html',
                  {'scope': scope, 'item_id': item_id, 'cid': cid, 'is_owner': is_owner})


def tabulate_stuff(request, scope, item_id, cid):
    # is_staff is used to restrict creating public calculator only to staff users.
    # restriction is here: function stuff_columns() in stuff_tabulator.html
    # Non-staff users can only create private calculator.
    # All users can share their private calculators with others by sharing the access_token.
    is_staff = 'y' if request.user.is_staff else 'n'
    return render(request, 'stuff_tabulator.html',
                  {'scope': scope, 'item_id': item_id, 'cid': cid, 'is_staff': is_staff})


def get_input_data(request, scope, item_id, jresp=True):  # used in input_tabulator
    # | get the variant or example 'input' records of an item_id (cal_id) from MyInput
    myinputs = apps.get_model('calc', 'MyInput').objects
    item_data = []
    items = []
    if scope == 'examples':
        # | Apply explicit ordering to avoid Paginator warning
        if item_id == '-all-':
            items = myinputs.filter(object_id='input', is_example=True).order_by('id')
        else:
            items = myinputs.filter(object_id='input', item_id=item_id, is_example=True).order_by('id')
    elif scope == 'variants' and is_loggedin(request):
        if item_id == '-all-':
            items = myinputs.filter(user=request.user, object_id='input', is_example=False).order_by('id')
        else:
            items = myinputs.filter(user=request.user, object_id='input', item_id=item_id,
                                            is_example=False).order_by('id')
    elif scope == 'update' and is_loggedin(request):
        if item_id == '-all-':
            items = myinputs.filter(user=request.user, object_id='input').order_by('id')
        else:
            items = myinputs.filter(user=request.user, object_id='input', item_id=item_id).order_by('id')

    for item in items:
        i_data = {
            'id': item.id,
            'owner': item.user.username,
            'object_id': item.object_id,
            'item_id': item.item_id,
            'variant_id': item.variant_id,
            'description': item.description,
            'is_shared': item.is_shared,
            'is_example': item.is_example,
            'access_token': item.access_token,
        }
        if item_id == '-all-':
            i_data.update({
                'item': item.item,  # JSONField
                'changed_on': item.changed_on,
            })
        item_data.append(i_data)
    if not jresp: return item_data
    return JsonResponse({
        'items': item_data,
    })


def get_stuff_data(request, scope, item_id, jresp=True):  # used in stuff_tabulator
    # | get the 'input' records of an item_id (cal_id) from MyStuff
    mystuffs = apps.get_model('calc', 'MyStuff').objects

    # Apply explicit ordering to avoid Paginator warning
    item_data = []
    if scope == 'mycal' and is_loggedin(request):
        user = request.user

        if item_id == '-all-':
            items = mystuffs.filter(user=user, object_id='mycal').order_by('id')
        else:
            items = mystuffs.filter(user=user, object_id='mycal', item_id=item_id).order_by('id')

        for item in items:
            # print('y' if item.user.is_staff else 'n')
            i_data = {
                'id': item.id,
                'owner': item.user.username,
                'object_id': item.object_id,
                'item_id': item.item_id,
                'is_public': item.is_public,
                'is_staff': 'y' if item.user.is_staff else 'n',
            }
            if item_id == '-all-':
                i_data.update({
                    'changed_on': item.changed_on,
                })
            item_data.append(i_data)
    if not jresp: return item_data
    return JsonResponse({
        'items': item_data,
    })


def get_fav_data(fav_dict: dict) -> dict:  # , jresp=True
    # | get 'input' records of all favorites in fav_dict from MyInput
    myinputs = apps.get_model('calc', 'MyInput').objects
    item_data = {}
    for item_id in fav_dict:
        # items=model.objects.filter(object_id='input', item_id=item_id) # item_id's are unique within 'input'
        input_id_list = fav_dict[item_id]
        items = myinputs.filter(object_id='input', id__in=input_id_list)  # id's are unique
        input_data_list = []
        for item in items:
            i_data = {
                'id': item.id,
                'owner': item.user.username,
                'object_id': item.object_id,
                'item_id': item.item_id,
                'variant_id': item.variant_id,
                'description': item.description,
                'is_shared': item.is_shared,
                'access_token': item.access_token,
            }
            input_data_list.append(i_data)

        item_data[item_id] = input_data_list

    # if jresp: return JsonResponse(item_data)
    return item_data


@require_POST
def update_input(request, id):  # used in input_tabulator
    myinputs = apps.get_model('calc', 'MyInput').objects
    item = myinputs.get(pk=id)

    # Update item with new data
    data = json.loads(request.body)
    for field, value in data.items():
        setattr(item, field, value)
    item.save()
    return JsonResponse({"success": True, "item": item.pk})


@require_http_methods(["DELETE"])
def delete_input(_request, id):  # used in input_tabulator
    myinputs = apps.get_model('calc', 'MyInput').objects
    item = myinputs.get(pk=id)
    try:
        item.delete()
        success = True
    except myinputs.model.DoesNotExist:
        success = False
    return JsonResponse({"success": success})


@require_POST
def update_stuff(request, id):  # used in stuff_tabulator
    mystuffs = apps.get_model('calc', 'MyStuff').objects
    item = mystuffs.get(pk=id)

    # Update item with new data
    data = json.loads(request.body)
    for field, value in data.items():
        setattr(item, field, value)
    item.save()
    return JsonResponse({"success": True, "item": item.pk})


@require_http_methods(["DELETE"])
def delete_stuff(_request, id):  # used in stuff_tabulator
    mystuffs = apps.get_model('calc', 'MyStuff').objects
    item = mystuffs.get(pk=id)
    if item:
        item.delete()
        return JsonResponse({"success": True})

    return JsonResponse({'success': False, 'error': 'Record not found'}, status=404)
