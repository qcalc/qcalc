# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import qsett

qsett.init()

from calculators.all.business.production import production_mix_profit


def test_production_mix_profit_unitized_headers_numeric_cells():
    result = production_mix_profit()

    assert isinstance(result, dict)
    assert result['Optimization Status'] == 'Optimal'

    mix = result['Optimal Production Mix']
    machine_time_idx = mix['columns'].index('Machine Time per Unit')
    first_row_machine_time = mix['data'][0][machine_time_idx]

    assert first_row_machine_time.uom == 'hr/unit'


def test_production_mix_profit_rejects_non_numeric_cell_when_header_has_unit():
    products = {
        'columns': [
            'Product',
            'Selling Price | USD/unit',
            'Variable Cost | USD/unit',
            'Machine Time | min/unit',
            'Labor Time | min/unit',
            'Max Demand | unit/mo',
            'Current Production Quantity | unit/mo',
            'Max Ramp Change | unit/mo',
        ],
        'data': [
            ['A', 50, 30, '5 min/unit', 3, 7500, 4200, 1200],
            ['B', 80, 48, 7, 4, 5000, 2600, 900],
        ],
    }

    result = production_mix_profit(products=products)

    assert isinstance(result, str)
    assert 'Expected unitless numeric value' in result
    assert 'Machine Time | min/unit' in result


def test_production_mix_profit_legacy_headers_with_cell_units_still_work():
    products = {
        'columns': [
            'Product',
            'Selling Price',
            'Variable Cost',
            'Machine Time',
            'Labor Time',
            'Max Demand',
            'Current Production Quantity',
            'Max Ramp Change',
        ],
        'data': [
            ['A', '50 USD/unit', '30 USD/unit', '5 min/unit', '3 min/unit', '7500 unit/mo', '4200 unit/mo', '1200 unit/mo'],
            ['B', '80 USD/unit', '48 USD/unit', '7 min/unit', '4 min/unit', '5000 unit/mo', '2600 unit/mo', '900 unit/mo'],
            ['C', '110 USD/unit', '60 USD/unit', '15 min/unit', '8 min/unit', '2000 unit/mo', '900 unit/mo', '500 unit/mo'],
        ],
    }

    result = production_mix_profit(products=products)

    assert isinstance(result, dict)
    assert result['Optimization Status'] == 'Optimal'
