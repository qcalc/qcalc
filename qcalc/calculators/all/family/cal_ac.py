# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, qfl


def ac_running_cost__info():
    return {
        'title': 'AC Running Cost',
        'desc': (
            'Estimate air-conditioner energy use and electricity cost from '
            'rated power, daily use, average operating load, and an effective '
            'electricity rate.'
        ),
        'schema': {
            'power': {
                'label': 'Rated electrical power',
                'help_text': 'Enter the AC electrical consumption, for example 1.2 kW or 1200 W.',
            },
            'usage': {
                'help_text': 'Enter AC usage with a time basis, for example 8 hr/day or 150 hr/mo.',
            },
            'electricity_rate': {
                'label': 'Electricity rate',
                'help_text': 'Enter the effective price of electricity, for example 0.12 USD/kWh.',
            },
            'operating_factor': {
                'label': 'Average operating load',
                'help_text': 'Fraction of rated power used on average; enter a value from 0 to 1.',
                'attrs': {'min': '0', 'max': '1', 'step': '0.01'},
            },
            'days': {
                'label': 'Calculation period',
                'help_text': 'Enter the number of days for the period cost and energy estimate.',
            },
        },
        'calculate': 'Estimate',
    }


def ac_running_cost(
    power='1.2 kW',
    usage='8 hr/day',
    electricity_rate='0.12 USD/kWh',
    operating_factor: qfl = 0.75,
    days='30 day',
):
    power_kw = Qty(power).to('kW').val
    usage_hr_per_day = Qty(usage).to('hr/day').val
    rate_q = Qty(electricity_rate)
    days_value = Qty(days).to('day').val

    if power_kw is None or power_kw < 0:
        raise ValueError('Rated electrical power must be non-negative.')
    if usage_hr_per_day is None or usage_hr_per_day < 0:
        raise ValueError('Daily usage must be non-negative.')
    if rate_q.val is None or rate_q.val < 0:
        raise ValueError('Electricity rate must be non-negative.')
    if days_value is None or days_value <= 0:
        raise ValueError('Calculation period must be greater than zero.')
    if operating_factor < 0 or operating_factor > 1:
        raise ValueError('Average operating load must be between 0 and 1.')

    currency = (rate_q * Qty('1 kWh')).uom
    rate_per_kwh = rate_q.to(f'{currency}/kWh').val
    average_power_kw = power_kw * operating_factor
    energy_per_day_kwh = average_power_kw * usage_hr_per_day
    energy_for_period_kwh = energy_per_day_kwh * days_value
    energy_per_month_kwh = energy_per_day_kwh * 30
    energy_per_year_kwh = energy_per_day_kwh * 365

    cost_per_day_value = energy_per_day_kwh * rate_per_kwh
    period_cost_value = energy_for_period_kwh * rate_per_kwh
    monthly_cost_value = energy_per_month_kwh * rate_per_kwh
    yearly_cost_value = energy_per_year_kwh * rate_per_kwh

    return {
        'Average Power Consumption': Qty(average_power_kw, 'kW'),
        'Energy per Hour': Qty(average_power_kw, 'kWh/hr'),
        'Energy for Period': Qty(energy_for_period_kwh, 'kWh'),
        'Cost per Period': Qty(period_cost_value, currency),
        'Energy and Cost by Period': {
            'columns': ['Metric', 'Day', 'Month', 'Year'],
            'data': [
                [
                    'Energy',
                    Qty(energy_per_day_kwh, 'kWh/day'),
                    Qty(energy_per_month_kwh, 'kWh'),
                    Qty(energy_per_year_kwh, 'kWh'),
                ],
                [
                    'Cost',
                    Qty(cost_per_day_value, f'{currency}/day'),
                    Qty(monthly_cost_value, f'{currency}/mo'),
                    Qty(yearly_cost_value, f'{currency}/yr'),
                ],
            ],
        },
    }