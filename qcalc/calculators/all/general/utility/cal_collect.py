# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd

from calc import (
    QKeep,
    valid_numq,
    QData,
    publish_shared_dataset,
    get_shared_dataset,
    QCost,
    default_rate_schedule,
    save_rates,
    load_rates,
)
import json
from qutil import action_button, addcal_button, action_script
from qcore import qhtml, qtable, qformat_q

SHARED_RATES_TYPE = 'item_rates'
SHARED_RATES_KEY = 'rates_master'


def collect__input(_ctx):
    keeps = QKeep.getp({})
    keeps.pop('count', None)
    kept_vals = [] if len(keeps) == 0 else list(keeps.values())
    # | kept_keys = list(keeps.keys())
    return {
        'output': pd.DataFrame({"SL": list(range(1, len(kept_vals) + 1)), "Value": kept_vals})
    }


def collect__info():
    return {
        'title': 'Output Collection',
        'calculate': 'Aggregate',
    }


def collect(output: qtable = pd.DataFrame({"SL": [1, 2], "Value": [
    '{"x": 10, "y": "15", "z":"3 ft"}',
    '{"x": 20, "y": "10", "z":"2 ft", "t":"15"}'
]}), clear=False):
    a = {}
    error = []
    if clear:
        values = []
    else:
        values = output['Value'].tolist()

    cnt = len(values)
    # | update collection if edited from qtable
    QKeep.clear()
    for i, val in enumerate(values):
        QKeep.setp1(i + 1, val)
        QKeep.setp1('count', cnt)

    for i in range(cnt):
        b = json.loads(values[i])
        union = set(a).union(set(b))
        inter = set(a).intersection(b)
        diff = union.difference(inter)
        c = {}
        for key in inter:
            va = a[key] if i > 0 else valid_numq(a[key])
            vb = valid_numq(b[key])
            if va and vb:
                try:
                    c[key] = va + vb
                except Exception as e:
                    c[key] = va
                    error.append(f'{key}:{va}+{vb}:{e}')
        for key in diff:
            if key in a:
                vab = a[key] if i > 0 else valid_numq(a[key])
            else:
                vab = valid_numq(b[key])

            if vab:
                c[key] = vab
        a = c
    return {"Result": a, "Error": error,
            "Count": qhtml(f'<span id="cart-count" hx-swap-oob="true" '
                           f'class="badge bg-primary badge-pill ml-auto">'
                           f'{cnt}</span>{cnt}')
            }


def cost__input(ctx):
    # probably it is better to restrict invoking __input() during GET only
    items = ctx.var_url('items')  # var_url data available only during GET
    if isinstance(items, pd.DataFrame):  # can't have if items, truth value of df is ambiguous
        # | no thousands separator: Quantity is read back by cost() and Qty() can't parse commas
        items['Quantity'] = items['Quantity'].apply(lambda q: qformat_q(q, thousands_separator=False))
        return {
            'items': items,
        }

    return {}


def cost__modify(_ctx, arg_name, arg_value, _action):  # _action not used but required
    if arg_name == 'items':
        items = arg_value
        action = _action if isinstance(_action, dict) else {}
        dataset_type = action.get('dataset_type', SHARED_RATES_TYPE)
        dataset_key = action.get('dataset_key', SHARED_RATES_KEY)
        shared_record = get_shared_dataset(dataset_type=dataset_type, dataset_key=dataset_key)

        if isinstance(shared_record, dict):
            rates = shared_record.get('payload')
        else:
            # backward compatibility for old sessions that only have legacy rates
            rates = QData.getp1('rates')
            if isinstance(rates, pd.DataFrame):
                publish_shared_dataset(
                    dataset_type=dataset_type,
                    dataset_key=dataset_key,
                    payload=rates,
                    producer_func='rates',
                )
                shared_record = get_shared_dataset(dataset_type=dataset_type, dataset_key=dataset_key)
                rates = shared_record.get('payload') if isinstance(shared_record, dict) else None

        if isinstance(rates, pd.DataFrame):
            qcost = QCost.from_unit_costs(rates)
        else:  # new session: use the schedule saved in the account
            qcost = QCost(use_defaults=False)
        if not qcost.has_rates:
            raise Exception(
                'No rates saved. Open [Schedule of Rates], click [Load], then apply again.'
            )
        return qcost.fill_rates(items)

    return arg_value


def cost__info():
    return {
        'title': 'Calculate Cost',
        'kins': 'rates',
        'consumes_data': {
            'dataset_type': SHARED_RATES_TYPE,
            'dataset_key': SHARED_RATES_KEY,
        },
        'inserts': {
            'form_bottom': addcal_button('rates', 'Schedule of Rates') +
                           action_button('apply_rate', 'Apply Rates', 'cmd-rates') +
                           '<p><small class="text-muted ml-2">After [Apply Rates], click [Update] before [Calculate].</small></p>'
            # callback_button() # not good for scripting
        },
        'step2': [
            {'step': 'chart', 'caption': 'Modify Chart', 'spec': {'field': 'Cost Chart'}}
        ],
        'script': action_script(
            button_name='apply_rate',
            cmd='__modify',
            args=['items'],
            kwargs={
                'items': {
                    'dataset_type': SHARED_RATES_TYPE,
                    'dataset_key': SHARED_RATES_KEY,
                },
            },
            sync_table_data=True,
            enable_table_update_after_swap=True,
        ),
    }


def cost(items: qtable = pd.DataFrame({'Item': ['Brick'], 'Quantity': ['1000 nos'], 'Unit Cost': ['0.10 UNC/nos']})):
    qcost = QCost.from_frame(items)
    items2 = qcost.frame(costs=True)
    # | apply formatting as a last action, because formatted values may have commas
    for column in ('Quantity', 'Unit Cost', 'Item Cost'):
        items2[column] = items2[column].apply(qformat_q)
    return {'Item Costs': items2, 'Total Cost': qcost.total, 'Cost Chart': qcost.chart()}


def rates__info():
    return {
        'title': 'Schedule of Rates',
        'desc': 'Your rates are saved to your account when you click Load, so cost calculations can use them later.',
        'calculate': 'Load',
        'single_instance': True,
        'single_instance_key': 'rates_master',
        'provides_data': {
            'dataset_type': SHARED_RATES_TYPE,
            'dataset_key': SHARED_RATES_KEY,
        },
    }


def rates__input(_ctx):
    saved = load_rates()
    return {} if saved is None else {'rate_schedule': saved}


def rates(rate_schedule: qtable = default_rate_schedule()):
    cost_schedule = QCost(schedule=rate_schedule).unit_costs()
    save_rates(rate_schedule)
    publish_shared_dataset(
        dataset_type=SHARED_RATES_TYPE,
        dataset_key=SHARED_RATES_KEY,
        payload=cost_schedule,
        producer_func='rates',
    )
    QData.setp1('rates', cost_schedule)
    return {
        'cost_schedule': cost_schedule,
    }
