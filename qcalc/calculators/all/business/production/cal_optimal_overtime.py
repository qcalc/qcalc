# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty, QChart


def optimal_overtime__info():
    return {
        'title': 'Optimization: Optimal Overtime Level',
        'desc': (
            'Find overtime hours that minimize total production-related cost '
            'with overtime efficiency deterioration and shortfall penalty.'
        ),
        'tags': 'business, production, overtime, optimization, nonlinear',
        'layout': 'tb',
        'inp1': 0.5,
        'out1': '~Optimization Chart, ~Overtime Scenarios',
    }


def _scenario_row(
    overtime_hours,
    required_units,
    normal_production,
    production_rate,
    max_overtime_hours,
    efficiency_deterioration,
    normal_labor_cost,
    overtime_hourly_cost,
    shortfall_penalty,
    fixed_production_cost,
    to_cur,
):
    if max_overtime_hours > 0:
        efficiency = 1.0 - efficiency_deterioration * (overtime_hours / max_overtime_hours) ** 2
    else:
        efficiency = 1.0
    efficiency = max(0.0, efficiency)

    overtime_rate = production_rate * efficiency
    overtime_production = overtime_hours * overtime_rate
    total_production = normal_production + overtime_production
    shortfall = max(0.0, required_units - total_production)

    overtime_cost = overtime_hours * overtime_hourly_cost
    shortfall_cost = shortfall * shortfall_penalty
    total_cost = normal_labor_cost + overtime_cost + shortfall_cost + fixed_production_cost

    return {
        'Overtime Hours': Qty(overtime_hours, 'hr/mo'),
        'Efficiency Factor': efficiency,
        'Overtime Production': Qty(overtime_production, 'unit/mo'),
        'Total Production': Qty(total_production, 'unit/mo'),
        'Production Shortfall': Qty(shortfall, 'unit/mo'),
        'Overtime Labor Cost': Qty(overtime_cost, f'{to_cur}/mo'),
        'Shortfall Cost': Qty(shortfall_cost, f'{to_cur}/mo'),
        'Total Cost': Qty(total_cost, f'{to_cur}/mo'),
    }


def optimal_overtime(
    required_production='2000 unit/mo',
    available_normal_hours='160 hr/mo',
    maximum_overtime_hours='50 hr/mo',
    production_rate='10 unit/hr',
    normal_hourly_cost='8 USD/hr',
    overtime_hourly_cost='12 USD/hr',
    shortfall_penalty='5 USD/unit',
    fixed_production_cost='1000 USD/mo',
    efficiency_deterioration=0.30,
    optimization_points: int = 200,
    scenario_points: int = 10,
):
    q_required = Qty(required_production, 'unit/mo')
    required_units = float(q_required.val)

    q_normal_hours = Qty(available_normal_hours, 'hr/mo')
    available_normal_hrs = max(0.0, float(q_normal_hours.val))

    q_max_overtime = Qty(maximum_overtime_hours, 'hr/mo')
    max_overtime_hrs = max(0.0, float(q_max_overtime.val))

    q_rate = Qty(production_rate, 'unit/hr')
    rate_unit_per_hr = max(0.0, float(q_rate.val))

    q_normal_cost = Qty(normal_hourly_cost)
    to_cur = q_normal_cost.uom.split('/')[0]
    normal_cost_per_hr = float(Qty(normal_hourly_cost, f'{to_cur}/hr').val)
    overtime_cost_per_hr = float(Qty(overtime_hourly_cost, f'{to_cur}/hr').val)
    shortfall_cost_per_unit = float(Qty(shortfall_penalty, f'{to_cur}/unit').val)
    fixed_cost_per_mo = float(Qty(fixed_production_cost, f'{to_cur}/mo').val)

    if rate_unit_per_hr <= 0:
        return 'Production rate must be greater than zero.'

    normal_hours_used = min(available_normal_hrs, required_units / rate_unit_per_hr)
    normal_production = normal_hours_used * rate_unit_per_hr
    normal_labor_cost = normal_hours_used * normal_cost_per_hr

    optimization_points = max(2, int(optimization_points))
    scenario_points = max(2, int(scenario_points))

    best = None
    for i in range(optimization_points):
        overtime_hours = max_overtime_hrs * i / (optimization_points - 1)
        row = _scenario_row(
            overtime_hours=overtime_hours,
            required_units=required_units,
            normal_production=normal_production,
            production_rate=rate_unit_per_hr,
            max_overtime_hours=max_overtime_hrs,
            efficiency_deterioration=float(efficiency_deterioration),
            normal_labor_cost=normal_labor_cost,
            overtime_hourly_cost=overtime_cost_per_hr,
            shortfall_penalty=shortfall_cost_per_unit,
            fixed_production_cost=fixed_cost_per_mo,
            to_cur=to_cur,
        )
        cost_val = float(row['Total Cost'].val)
        if best is None or cost_val < best['cost']:
            best = {'cost': cost_val, 'row': row}

    scenario_data = []
    overtime_xvals = []
    total_cost_y = []
    overtime_cost_y = []
    shortfall_cost_y = []
    for i in range(scenario_points):
        overtime_hours = max_overtime_hrs * i / (scenario_points - 1)
        row = _scenario_row(
            overtime_hours=overtime_hours,
            required_units=required_units,
            normal_production=normal_production,
            production_rate=rate_unit_per_hr,
            max_overtime_hours=max_overtime_hrs,
            efficiency_deterioration=float(efficiency_deterioration),
            normal_labor_cost=normal_labor_cost,
            overtime_hourly_cost=overtime_cost_per_hr,
            shortfall_penalty=shortfall_cost_per_unit,
            fixed_production_cost=fixed_cost_per_mo,
            to_cur=to_cur,
        )
        overtime_xvals.append(overtime_hours)
        total_cost_y.append(float(row['Total Cost'].val))
        overtime_cost_y.append(float(row['Overtime Labor Cost'].val))
        shortfall_cost_y.append(float(row['Shortfall Cost'].val))
        scenario_data.append([
            row['Overtime Hours'],
            row['Efficiency Factor'],
            row['Overtime Production'],
            row['Total Production'],
            row['Production Shortfall'],
            row['Overtime Labor Cost'],
            row['Shortfall Cost'],
            row['Total Cost'],
        ])

    optimal = best['row']
    produced_val = float(optimal['Total Production'].val)
    unit_cost = (best['cost'] / produced_val) if produced_val > 0 else None

    chart = QChart(xtype=float)
    chart.render_lines(
        xvals=overtime_xvals,
        yvalsm=[total_cost_y, overtime_cost_y, shortfall_cost_y],
        xlabel='Overtime Hours (hr/mo)',
        ylabels=['Total Cost', 'Overtime Labor Cost', 'Shortfall Cost'],
        ylabel=f'Cost ({to_cur}/mo)',
        title='Optimal Overtime Cost Curve',
    )

    return {
        'Optimal Overtime': optimal['Overtime Hours'],
        'Normal Production': Qty(normal_production, 'unit/mo'),
        'Overtime Production': optimal['Overtime Production'],
        'Total Production': optimal['Total Production'],
        'Production Shortfall': optimal['Production Shortfall'],
        'Overtime Efficiency Factor': optimal['Efficiency Factor'],
        'Normal Labor Cost': Qty(normal_labor_cost, f'{to_cur}/mo'),
        'Overtime Labor Cost': optimal['Overtime Labor Cost'],
        'Shortfall Cost': optimal['Shortfall Cost'],
        'Total Cost': optimal['Total Cost'],
        'Cost per Unit Produced': Qty(unit_cost, f'{to_cur}/unit'),
        'Optimization Chart': chart,
        'Overtime Scenarios': {
            'columns': [
                'Overtime Hours',
                'Efficiency Factor',
                'Overtime Production',
                'Total Production',
                'Production Shortfall',
                'Overtime Labor Cost',
                'Shortfall Cost',
                'Total Cost',
            ],
            'data': scenario_data,
        },
    }
