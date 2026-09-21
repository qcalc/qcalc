# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd

from calc import (
    QKeep,
    valid_numq,
    QData,
    publish_shared_dataset,
    get_shared_dataset,
)
import json
from qutil import find_matched_variables, addcal_button
from calculators.all.general.chart import pie_chart
from qcore import qhtml, qtable, Qty, _unit_tree, qformat_q, qformat_qstr

SHARED_RATES_TYPE = 'item_rates'
SHARED_RATES_KEY = 'rates_master'


def collect__input(_kwargs):  # | kwargs required
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


def cost__input(kwargs):
    # probably it is better to restrict invoking __input() during GET only
    items = kwargs.get('items')  # kwargs data available only during GET
    if isinstance(items, pd.DataFrame):  # can't have if items, truth value of df is ambiguous
        items['Quantity'] = items['Quantity'].apply(qformat_qstr)  # format data
        return {
            'items': items,
        }

    return {}


def cost__modify(arg_name, arg_value, _action):  # _action not used but required
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
            item_key = items['Item'].str.strip().str.casefold()
            rate_key = rates['Item'].str.strip().str.casefold()

            merged_df = items.merge(
                rates.assign(_item_key=rate_key),
                left_on=item_key,
                right_on='_item_key',
                how='left'
            )

            items['Unit Cost'] = merged_df['Unit Cost_y'].fillna(items['Unit Cost'])

            return items

        elif rates is None:
            raise Exception(
                'No shared rates loaded. Open [Schedule of Rates], click [Load], then apply again.'
            )

    return arg_value


def cost__info():
    return {
        'title': 'Calculate Cost',
        'consumes_data': {
            'dataset_type': SHARED_RATES_TYPE,
            'dataset_key': SHARED_RATES_KEY,
        },
        'inserts': {
            'form_bottom': addcal_button('rates', 'Schedule of Rates') +
                           '<button type="button" class="btn btn-info btncmd ml-2 cmd-rates" '
                           'name="apply_rate">Apply Rates</button>'
                           '<p><small class="text-muted ml-2">After [Apply Rates], click [Update] before [Calculate].</small></p>'
            # command_button() # not good for scripting
        },
        'step2': [
            {'step': 'chart', 'caption': 'Modify Chart', 'spec': {'field': 'Chart'}}
        ],
        'script': '''
$(document).ready(function() {
    $(".cmd-rates").on("click", function() {
        updateAllData($(this));
        cid = getCidOf($(this));
        qcalc_EnableTableUpdateAfterSwap(cid);
        updateExtra(cid, {
            "cmd":"__modify",
            "args":["@items"],
            "kwargs":{"@items":{
                "dataset_type":"item_rates",
                "dataset_key":"rates_master"
            }}
        });
        qcalc_FullFormSubmit(cid);
    });
});
        '''
    }


def cost(items: qtable = pd.DataFrame({'Item': ['Brick'], 'Quantity': ['1000 nos'], 'Unit Cost': ['0.10 UNC/nos']})):
    currecncy_used = find_matched_variables(items['Unit Cost'][0].lower(), _unit_tree['C'])[0]

    def cal_cost(row) -> Qty:
        row['Quantity'] = Qty(row['Quantity'])
        row['Unit Cost'] = Qty(row['Unit Cost'])
        item_cost = row['Quantity'] * row['Unit Cost']
        item_cost = item_cost.to(currecncy_used)
        return item_cost

    items2 = items.copy()  # to keep the source dataframe unchanged
    items2['Item Cost'] = items2.apply(cal_cost, axis=1)
    total_cost = Qty(sum([c.val for c in items2['Item Cost']]), currecncy_used)
    chart = pie_chart(labels=','.join(items2['Item']),
                      values=','.join(items2['Item Cost'].apply(lambda q: str(q.val))),
                      title="Cost Chart", show_pct=True)
    # | apply formatting as a last action, because formatted values may have commas
    items2['Quantity'] = items2['Quantity'].apply(qformat_q)
    items2['Unit Cost'] = items2['Unit Cost'].apply(qformat_q)
    items2['Item Cost'] = items2['Item Cost'].apply(qformat_q)
    return {'Item Costs': items2, 'Total Cost': total_cost, 'Chart': chart['chart']}


def rates__info():
    return {
        'title': 'Schedule of Rates',
        'calculate': 'Load',
        'single_instance': True,
        'single_instance_key': 'rates_master',
        'provides_data': {
            'dataset_type': SHARED_RATES_TYPE,
            'dataset_key': SHARED_RATES_KEY,
        },
    }


def rates(rate_schedule: qtable = pd.DataFrame({
    'Item': ['Brick', 'Sand', 'Cement'],
    'Price': [10.0, 2000.0, 500.0],
    'Currency': ['BDT', 'BDT', 'BDT'],
    'Price Per': [1, 100, 1],
    'Price Unit': ['ea', 'cft', 'bag']
})):
    def calprice(row):
        uprice = float(row['Price'].replace(',', '')) / float(row['Price Per'].replace(',', ''))
        p = f"{str(uprice)} {row['Currency']}/{row['Price Unit']}"
        return Qty(p)

    cost_schedule = pd.DataFrame({
        'Item': rate_schedule['Item'],
    })
    cost_schedule['Unit Cost'] = rate_schedule.apply(calprice, axis=1)
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
