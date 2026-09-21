# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import math

from qcore import Qty, QChart


def discount_opt__info():
    return {
        'title': 'Sales Discount Optimization',
        'desc': (
            'Find the discount that maximizes profit using a saturating '
            'conversion response, with capacity and margin-floor constraints.'
        ),
        'schema': {
            'discount_sensitivity': {
                'label': 'Sensitivity Factor (k)',
                'help_text': 'Dimensionless (not %). Suggested range: 3 to 20. Higher values make conversion rise faster at low discount.'
            },
            'minimum_discount': {
                'help_text': 'More than or equal to 0 pct, for baseline policy checks.'
            },
            'maximum_discount': {
                'help_text': 'Less than 100 pct.'
            },
            'optimization_points': {
                'help_text': 'Search resolution for optimization. Suggested range: 101 to 501.'
            },
            'scenario_points': {
                'help_text': 'Display resolution for scenario table/charts. Suggested range: 8 to 25.'
            },
        },
        'tags': 'business, sales, discount, optimization, nonlinear',
        'layout': 'tb',
        'inp1': 0.5,
        'out1': '~*Chart',
    }


def _conversion_rate(discount_frac, cr0, cr_max, sensitivity):
    return cr0 + (cr_max - cr0) * (1.0 - math.exp(-sensitivity * discount_frac))


def _scenario_at_discount(
    discount_frac,
    prospects,
    list_price,
    unit_cost,
    cr0,
    cr_max,
    sensitivity,
    sales_cost_per_prospect,
    max_fulfillable_units,
    min_unit_margin,
    to_cur,
):
    conversion = _conversion_rate(discount_frac, cr0, cr_max, sensitivity)
    conversion = max(0.0, min(cr_max, conversion))

    demand_units = prospects * conversion
    sold_units = min(demand_units, max_fulfillable_units)
    net_price = list_price * (1.0 - discount_frac)
    unit_margin = net_price - unit_cost

    margin_feasible = unit_margin >= min_unit_margin - 1e-12
    capacity_limited = demand_units > max_fulfillable_units + 1e-12

    revenue = sold_units * net_price
    gross_contribution = sold_units * unit_margin
    sales_cost_total = prospects * sales_cost_per_prospect
    total_profit = gross_contribution - sales_cost_total

    return {
        'Discount': Qty(discount_frac * 100.0, 'pct'),
        'Conversion Rate': Qty(conversion * 100.0, 'pct'),
        'Demand Units': Qty(demand_units, 'unit/mo'),
        'Sold Units': Qty(sold_units, 'unit/mo'),
        'Net Price': Qty(net_price, f'{to_cur}/unit'),
        'Unit Margin': Qty(unit_margin, f'{to_cur}/unit'),
        'Revenue': Qty(revenue, f'{to_cur}/mo'),
        'Gross Contribution': Qty(gross_contribution, f'{to_cur}/mo'),
        'Sales Cost Total': Qty(sales_cost_total, f'{to_cur}/mo'),
        'Total Profit': Qty(total_profit, f'{to_cur}/mo'),
        'Capacity Limited': capacity_limited,
        'Margin Feasible': margin_feasible,
    }


def discount_opt(
    number_of_prospects='10000 nos/mo',
    list_price='50 USD/unit',
    unit_cost='30 USD/unit',
    base_conversion_rate='5 pct',
    maximum_conversion_rate='20 pct',
    discount_sensitivity=10.0,
    sales_cost_per_prospect='1.5 USD/nos',
    current_discount='15 pct',
    minimum_discount='0 pct',
    maximum_discount='35 pct',
    maximum_fulfillable_units='2000 unit/mo',
    minimum_unit_margin='5 USD/unit',
    optimization_points: int = 201,
    scenario_points: int = 11,
):
    prospects = max(0.0, float(Qty(number_of_prospects, 'nos/mo').val))

    q_price = Qty(list_price)
    to_cur = q_price.uom.split('/')[0]
    price_per_unit = float(Qty(list_price, f'{to_cur}/unit').val)
    cost_per_unit = float(Qty(unit_cost, f'{to_cur}/unit').val)

    cr0 = float(Qty(base_conversion_rate, 'pct').val) / 100.0
    cr_max = float(Qty(maximum_conversion_rate, 'pct').val) / 100.0
    sensitivity = float(discount_sensitivity)

    cost_per_prospect = float(Qty(sales_cost_per_prospect, f'{to_cur}/nos').val)
    current_d = float(Qty(current_discount, 'pct').val) / 100.0
    min_d = float(Qty(minimum_discount, 'pct').val) / 100.0
    max_d = float(Qty(maximum_discount, 'pct').val) / 100.0

    max_units = max(0.0, float(Qty(maximum_fulfillable_units, 'unit/mo').val))
    min_margin = float(Qty(minimum_unit_margin, f'{to_cur}/unit').val)

    if price_per_unit <= 0:
        return 'List price must be greater than zero.'
    if cr0 < 0 or cr0 > 1 or cr_max < 0 or cr_max > 1 or cr_max < cr0:
        return 'Conversion rates must satisfy 0 <= base <= maximum <= 100%.'
    if sensitivity < 0:
        return 'Discount sensitivity must be non-negative.'
    if min_d < 0 or max_d < 0 or min_d > max_d or max_d >= 1:
        return 'Discount range must satisfy 0% <= minimum <= maximum < 100%.'

    optimization_points = max(2, int(optimization_points))
    scenario_points = max(2, int(scenario_points))

    best = None
    feasible_count = 0
    for i in range(optimization_points):
        d = min_d + (max_d - min_d) * i / (optimization_points - 1)
        row = _scenario_at_discount(
            discount_frac=d,
            prospects=prospects,
            list_price=price_per_unit,
            unit_cost=cost_per_unit,
            cr0=cr0,
            cr_max=cr_max,
            sensitivity=sensitivity,
            sales_cost_per_prospect=cost_per_prospect,
            max_fulfillable_units=max_units,
            min_unit_margin=min_margin,
            to_cur=to_cur,
        )

        if row['Margin Feasible']:
            feasible_count += 1
            profit_val = float(row['Total Profit'].val)
            if best is None or profit_val > best['profit']:
                best = {'profit': profit_val, 'row': row, 'discount': d}

    if best is None:
        return {
            'Optimization Status': 'No feasible solution',
            'Message': (
                'No discount level satisfies the minimum unit margin in the '
                'selected range. Reduce minimum margin or narrow max discount.'
            ),
            'Margin-Feasible Trial Points': feasible_count,
        }

    scenario_rows = []
    chart_x = []
    chart_profit = []
    chart_gross = []
    chart_sales_cost = []
    chart_conversion = []
    chart_unit_margin = []
    chart_demand_units = []
    chart_sold_units = []
    for i in range(scenario_points):
        d = min_d + (max_d - min_d) * i / (scenario_points - 1)
        row = _scenario_at_discount(
            discount_frac=d,
            prospects=prospects,
            list_price=price_per_unit,
            unit_cost=cost_per_unit,
            cr0=cr0,
            cr_max=cr_max,
            sensitivity=sensitivity,
            sales_cost_per_prospect=cost_per_prospect,
            max_fulfillable_units=max_units,
            min_unit_margin=min_margin,
            to_cur=to_cur,
        )

        chart_x.append(d * 100.0)
        chart_profit.append(float(row['Total Profit'].val))
        chart_gross.append(float(row['Gross Contribution'].val))
        chart_sales_cost.append(float(row['Sales Cost Total'].val))
        chart_conversion.append(float(row['Conversion Rate'].val))
        chart_unit_margin.append(float(row['Unit Margin'].val))
        chart_demand_units.append(float(row['Demand Units'].val))
        chart_sold_units.append(float(row['Sold Units'].val))

        scenario_rows.append([
            row['Discount'],
            row['Conversion Rate'],
            row['Demand Units'],
            row['Sold Units'],
            row['Net Price'],
            row['Unit Margin'],
            row['Revenue'],
            row['Gross Contribution'],
            row['Sales Cost Total'],
            row['Total Profit'],
            row['Capacity Limited'],
            row['Margin Feasible'],
        ])

    zero_row = _scenario_at_discount(
        discount_frac=0.0,
        prospects=prospects,
        list_price=price_per_unit,
        unit_cost=cost_per_unit,
        cr0=cr0,
        cr_max=cr_max,
        sensitivity=sensitivity,
        sales_cost_per_prospect=cost_per_prospect,
        max_fulfillable_units=max_units,
        min_unit_margin=min_margin,
        to_cur=to_cur,
    )
    current_row = _scenario_at_discount(
        discount_frac=current_d,
        prospects=prospects,
        list_price=price_per_unit,
        unit_cost=cost_per_unit,
        cr0=cr0,
        cr_max=cr_max,
        sensitivity=sensitivity,
        sales_cost_per_prospect=cost_per_prospect,
        max_fulfillable_units=max_units,
        min_unit_margin=min_margin,
        to_cur=to_cur,
    )

    optimal = best['row']
    optimal_discount = best['discount']
    optimal_profit = float(optimal['Total Profit'].val)
    current_profit = float(current_row['Total Profit'].val)
    zero_profit = float(zero_row['Total Profit'].val)

    boundary_warning = (abs(optimal_discount - min_d) <= 1e-12) or (abs(optimal_discount - max_d) <= 1e-12)
    margin_floor_active = abs(float(optimal['Unit Margin'].val) - min_margin) <= 1e-8

    chart = QChart(xtype=float)
    chart.render_lines(
        xvals=chart_x,
        yvalsm=[chart_profit, chart_gross, chart_sales_cost],
        xlabel='Discount (%)',
        ylabels=['Total Profit', 'Gross Contribution', 'Sales Cost Total'],
        ylabel=f'Amount ({to_cur}/mo)',
        title='Discount Optimization Profit Curve',
    )

    chart_conv_margin = QChart(xtype=float)
    chart_conv_margin.render_lines(
        xvals=chart_x,
        yvalsm=[chart_conversion, chart_unit_margin],
        xlabel='Discount (%)',
        ylabels=['Conversion Rate (%)', f'Unit Margin ({to_cur}/unit)'],
        ylabel='Value',
        title='Conversion vs Unit Margin',
    )

    chart_demand_capacity = QChart(xtype=float)
    chart_demand_capacity.render_lines(
        xvals=chart_x,
        yvalsm=[chart_demand_units, chart_sold_units],
        xlabel='Discount (%)',
        ylabels=['Demand Units', 'Sold Units (Capped)'],
        ylabel='Units (unit/mo)',
        title='Demand vs Capacity-Capped Sales',
    )

    return {
        'Optimization Status': 'Optimal (grid search)',
        'Recommended Discount': optimal['Discount'],
        'Current Discount': current_row['Discount'],
        'Profit Lift vs Current Discount': Qty(optimal_profit - current_profit, f'{to_cur}/mo'),
        'Profit at Current Discount': current_row['Total Profit'],
        'Profit at Optimal Discount': optimal['Total Profit'],
        'Profit Lift % vs Current Discount': Qty((optimal_profit - current_profit) / current_profit * 100 if current_profit > 0 else 0.0, 'pct'),
        'Expected Conversion Rate': optimal['Conversion Rate'],
        'Expected Units Sold (Demand)': optimal['Demand Units'],
        'Expected Units Sold (Capped)': optimal['Sold Units'],
        'Net Selling Price': optimal['Net Price'],
        'Unit Contribution Margin': optimal['Unit Margin'],
        'Revenue': optimal['Revenue'],
        'Gross Contribution': optimal['Gross Contribution'],
        'Sales Cost Total': optimal['Sales Cost Total'],
        'Profit per Prospect': Qty(optimal_profit / prospects if prospects > 0 else 0.0, f'{to_cur}/nos'),
        'Profit at Zero Discount': zero_row['Total Profit'],
        'Profit Lift vs Zero Discount': Qty(optimal_profit - zero_profit, f'{to_cur}/mo'),
        'Capacity-Limited at Optimum': optimal['Capacity Limited'],
        'Margin-Floor Active at Optimum': margin_floor_active,
        'Boundary Warning': boundary_warning,
        'Optimization Chart': chart,
        'Conversion vs Margin Chart': chart_conv_margin,
        'Demand vs Capacity Chart': chart_demand_capacity,
        'Discount Scenarios': {
            'columns': [
                'Discount',
                'Conversion Rate',
                'Demand Units',
                'Sold Units (Capped)',
                'Net Price',
                'Unit Margin',
                'Revenue',
                'Gross Contribution',
                'Sales Cost Total',
                'Total Profit',
                'Capacity Limited',
                'Margin Feasible',
            ],
            'data': scenario_rows,
        },
    }