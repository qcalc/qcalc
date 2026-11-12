# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import qsett

qsett.init()

import pandas as pd
import pytest
import qvars
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from calc import QData, QCost, default_rate_schedule
from calc.mod_hookctx import HookContext
from calc.mod_shared_data import publish_shared_dataset, get_shared_dataset
from calculators.all.engineering.estimation import building_cost_detailed, brickwork, ccwork, plaster
from calculators.all.general.utility import (
    SHARED_RATES_KEY,
    SHARED_RATES_TYPE,
    cost__input,
    cost__modify,
    rates,
    rates__input,
)
from calculators.all.analytics import (
    compare,
    SHARED_SCENARIO_KEY,
    SHARED_SCENARIO_TYPE,
)
from calculators.all.analytics import (
    scenario__modify,
)
from qcore import Qty
from qutil.timed_thread import QThread


def _make_request(path='/', method='get', data=None):
    rf = RequestFactory()
    data = data or {}
    req = rf.post(path, data=data) if method == 'post' else rf.get(path, data=data)
    SessionMiddleware(lambda r: None).process_request(req)
    req.session.save()
    req.user = AnonymousUser()
    return req


@pytest.fixture(autouse=True)
def _stub_super_user(monkeypatch):
    monkeypatch.setattr(qvars, 'super_user', type('_FakeUser', (), {'username': 'super'})())


@pytest.fixture(autouse=True)
def _thread_req_cleanup():
    QThread.set_req(None)
    yield
    QThread.set_req(None)


def _shared_action():
    return {
        'dataset_type': SHARED_RATES_TYPE,
        'dataset_key': SHARED_RATES_KEY,
    }


def test_publish_and_read_shared_dataset_dataframe():
    req = _make_request()
    QThread.set_req(req)
    QData.clear()

    payload = pd.DataFrame({'Item': ['Brick'], 'Unit Cost': ['10 BDT/ea']})
    meta = publish_shared_dataset(
        dataset_type=SHARED_RATES_TYPE,
        dataset_key=SHARED_RATES_KEY,
        payload=payload,
        producer_func='rates',
    )

    record = get_shared_dataset(dataset_type=SHARED_RATES_TYPE, dataset_key=SHARED_RATES_KEY)

    assert record is not None
    assert meta['dataset_key'] == SHARED_RATES_KEY
    assert meta['dataset_type'] == SHARED_RATES_TYPE
    assert isinstance(record['payload'], pd.DataFrame)
    assert record['payload'].iloc[0]['Item'] == 'Brick'


def test_cost_input_formats_items_for_display():
    req = _make_request()
    QThread.set_req(req)
    QData.clear()

    items = pd.DataFrame({'Item': ['Brick'], 'Quantity': ['100 nos'], 'Unit Cost': ['0.10 UNC/nos']})
    defaults = cost__input(HookContext(var_url_kwargs={'items': items}))

    assert 'items' in defaults
    assert 'shared_item_rates_version' not in defaults


def test_cost_modify_applies_shared_rates():
    req = _make_request(method='post')
    QThread.set_req(req)
    QData.clear()

    schedule = pd.DataFrame({
        'Item': ['Brick'],
        'Price': ['10'],
        'Currency': ['BDT'],
        'Price Per': ['1'],
        'Price Unit': ['ea'],
    })
    rates(schedule)

    items = pd.DataFrame({'Item': ['Brick'], 'Quantity': ['100 nos'], 'Unit Cost': ['0.10 UNC/nos']})
    updated = cost__modify(HookContext(), 'items', items, _shared_action())

    assert isinstance(updated.loc[0, 'Unit Cost'], Qty)


def test_cost_modify_uses_latest_rates_after_reload():
    req = _make_request(method='post')
    QThread.set_req(req)
    QData.clear()

    schedule = pd.DataFrame({
        'Item': ['Brick'],
        'Price': ['10'],
        'Currency': ['BDT'],
        'Price Per': ['1'],
        'Price Unit': ['ea'],
    })
    rates(schedule)
    schedule2 = pd.DataFrame({
        'Item': ['Brick'],
        'Price': ['15'],
        'Currency': ['BDT'],
        'Price Per': ['1'],
        'Price Unit': ['ea'],
    })
    rates(schedule2)

    items = pd.DataFrame({'Item': ['Brick'], 'Quantity': ['100 nos'], 'Unit Cost': ['0.10 UNC/nos']})
    updated = cost__modify(HookContext(), 'items', items, _shared_action())

    assert isinstance(updated.loc[0, 'Unit Cost'], Qty)
    assert abs(updated.loc[0, 'Unit Cost'].val - 15.0) < 1e-9
    assert updated.loc[0, 'Unit Cost'].uom == 'BDT/ea'


def test_cost_modify_falls_back_to_legacy_rates_and_backfills_shared_registry():
    req = _make_request(method='post')
    QThread.set_req(req)
    QData.clear()

    legacy_rates = pd.DataFrame({'Item': ['Brick'], 'Unit Cost': [Qty('11 BDT/ea')]})
    QData.setp1('rates', legacy_rates)

    items = pd.DataFrame({'Item': ['Brick'], 'Quantity': ['100 nos'], 'Unit Cost': ['0.10 UNC/nos']})
    updated = cost__modify(HookContext(), 'items', items, _shared_action())

    assert isinstance(updated.loc[0, 'Unit Cost'], Qty)
    shared = get_shared_dataset(dataset_type=SHARED_RATES_TYPE, dataset_key=SHARED_RATES_KEY)
    assert isinstance(shared, dict)
    assert shared.get('payload') is not None


def test_saved_rates_survive_a_new_data_session_and_prefill_rates_input():
    QThread.set_req(_make_request(method='post'))
    QData.clear()
    schedule = pd.DataFrame({'Item': ['Brick'], 'Price': ['12'], 'Currency': ['BDT'],
                             'Price Per': ['1'], 'Price Unit': ['ea']})
    rates(schedule)

    QData.clear()  # shared dataset gone, the saved schedule remains
    assert rates__input(HookContext())['rate_schedule'].loc[0, 'Price'] == '12'
    items = pd.DataFrame({'Item': ['Brick'], 'Quantity': ['100 nos'], 'Unit Cost': ['0.10 UNC/nos']})
    updated = cost__modify(HookContext(), 'items', items, _shared_action())
    assert abs(updated.loc[0, 'Unit Cost'].val - 12.0) < 1e-9


def test_qcost_prices_saved_rates_reports_missing_and_compounds_overheads():
    QThread.set_req(_make_request(method='post'))
    QData.clear()
    rates(pd.DataFrame({'Item': ['Cement'], 'Price': ['500'], 'Currency': ['BDT'],
                        'Price Per': ['1'], 'Price Unit': ['bag']}))

    cost = QCost()
    cost.add_all({'Cement': Qty(10, 'bag'), 'Gold': Qty(1, 'kg')})
    cost.overhead('Markup', '10 pct')
    cost.overhead('Contingency', '5 pct')

    assert cost.missing == ['Gold'] and not cost.default
    assert cost.total.val == pytest.approx(5000 * 1.1 * 1.05)  # contingency applies after markup
    assert cost.rows()['data'][0][-1].endswith('%') and 'Cost Notes' in cost.results()


def test_qcost_from_result_uses_a_spec_and_groups_mandays_as_labour():
    QThread.set_req(_make_request(method='post'))
    QData.clear()
    result = {'Cement': Qty(10, 'bag'), 'Skilled Labour': Qty(2, 'manday'), 'Work Volume': Qty(5, 'cft'),
              'Total': Qty(99, 'BDT'), 'Note': 'text'}

    cost = QCost.from_result(result, '~Work Volume')  # default rates, Total (a currency) and text are never priced

    assert [x.name for x in cost.lines] == ['Cement', 'Skilled Labour']
    assert cost.group('Labour').val == pytest.approx(2 * 1200)
    assert cost.results(per=result['Work Volume'], per_label='Volume')['Cost per Volume'].uom == 'BDT/cft'


def test_estimation_calculators_can_price_their_own_outputs():
    QThread.set_req(_make_request(method='post'))
    QData.clear()
    for calc in (brickwork, ccwork, plaster):
        out = calc(include_cost=True)
        assert out['Total Cost'].val == pytest.approx(out['Material Cost'].val + out['Labour Cost'].val)
        assert 'Cost Breakdown' in out and 'Cost Notes' in out  # defaults used, so the user is told
        assert 'Cost Chart' in out
        assert 'Cost Notes' not in calc()  # off by default

    cost = QCost.from_result({'Cement': Qty(10, 'bag'), 'Sand': Qty(5, 'cft')})
    cost.overhead('Contingency', '5 pct')
    assert 'Cost Chart' not in cost.results(chart=False)
    out = cost.results()
    assert out['Cost Chart'].chtype == 'pie_chart'  # reopenable with step2 Modify Chart
    assert out['Cost Chart'].data['labels'] == 'Cement,Sand,Contingency'


def test_building_cost_detailed_cost_is_a_normal_result_that_follows_rates():
    QThread.set_req(_make_request(method='post'))
    QData.clear()
    out = building_cost_detailed(include_cost=True)
    names = [row[0] for row in out['Cost Breakdown']['data']]
    assert len(names) == len(set(names))  # Brick (with soling) is priced once
    assert out['Total Cost'].val == pytest.approx(out['Material Cost'].val + out['Labour Cost'].val)
    assert 'Cost Breakdown' in out and 'Cost per Area' in out

    rates(default_rate_schedule().assign(Price=lambda d: d['Price'] * 2))
    assert building_cost_detailed(include_cost=True)['Total Cost'].val == pytest.approx(2 * out['Total Cost'].val)


def test_compare_publishes_shared_scenario_dataset():
    req = _make_request()
    QThread.set_req(req)
    QData.clear()

    out = compare(
        xpr='x + y',
        inputs={
            'columns': ['Variable', 'V1', 'V2', 'V3'],
            'data': [['x', 1, 2, 3], ['y', 2, 3, 4]],
        },
        show='table',
    )

    record = get_shared_dataset(dataset_type=SHARED_SCENARIO_TYPE, dataset_key=SHARED_SCENARIO_KEY)

    assert 'table' in out
    assert isinstance(record, dict)
    assert isinstance(record['payload'], dict)
    assert record['payload']['columns'][0] == 'Variation'


def test_scenario_input_and_modify_can_consume_compare_shared_dataset():
    req = _make_request(method='post')
    QThread.set_req(req)
    QData.clear()

    compare(
        xpr='x + y',
        inputs={
            'columns': ['Variable', 'V1', 'V2', 'V3'],
            'data': [['x', 10, 20, 30], ['y', 1, 2, 3]],
        },
        show='table',
    )

    updated = scenario__modify(
        HookContext(),
        'scenarios',
        {'columns': ['Variation'], 'data': [['old']]},
        {
            'dataset_type': SHARED_SCENARIO_TYPE,
            'dataset_key': SHARED_SCENARIO_KEY,
        },
    )

    assert isinstance(updated, dict)
    assert updated['columns'][0] == 'Variation'
    assert len(updated['data']) == 3
