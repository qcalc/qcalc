# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty


def downtime_loss__info():
    return {
        'title': 'Downtime Loss Calculator',
        'desc': (
            'Estimate production and contribution-margin losses from planned '
            'and unplanned downtime.'
        ),
        'tags': 'business, production, downtime, loss',
        'layout': 'tb',
        'out1': 0.5,
    }


def downtime_loss(
    planned_downtime='2 hr/mo',
    unplanned_downtime='5 hr/mo',
    production_rate='120 unit/hr',
    contribution_margin='8 USD/unit',
    recovery_rate='0 pct',
    events_per_month='4 nos/mo',
    cost_per_event='150 USD/nos',
):
    q_planned = Qty(planned_downtime, 'hr/mo')
    q_unplanned = Qty(unplanned_downtime, 'hr/mo')
    q_rate = Qty(production_rate, 'unit/hr')
    q_margin = Qty(contribution_margin)
    q_recovery = Qty(recovery_rate, 'pct').val / 100.0
    q_events = Qty(events_per_month, 'nos/mo')
    q_cost_per_event = Qty(cost_per_event)

    to_cur = q_margin.uom.split('/')[0]
    margin_per_unit = Qty(contribution_margin, f'{to_cur}/unit')
    event_cost = Qty(cost_per_event, f'{to_cur}/nos')

    total_downtime = q_planned + q_unplanned
    planned_lost_production = q_planned * q_rate
    unplanned_lost_production = q_unplanned * q_rate
    lost_production = total_downtime * q_rate

    recovered_production = lost_production * q_recovery
    net_production_loss = lost_production - recovered_production

    planned_loss = planned_lost_production * margin_per_unit
    unplanned_loss = unplanned_lost_production * margin_per_unit
    net_margin_loss = net_production_loss * margin_per_unit
    monthly_event_cost = q_events * event_cost
    monthly_loss = net_margin_loss + monthly_event_cost
    annual_loss = monthly_loss * Qty(12, 'mo/yr')
    annual_unplanned_loss = (unplanned_loss + monthly_event_cost) * Qty(12, 'mo/yr')

    return {
        'Total Downtime': total_downtime,
        'Planned Production Loss': planned_lost_production,
        'Unplanned Production Loss': unplanned_lost_production,
        'Recovered Production': recovered_production,
        'Production Loss': lost_production,
        'Net Production Loss': net_production_loss,
        'Recovery Rate': Qty(q_recovery * 100, 'pct'),
        'Event Cost per Month': monthly_event_cost.to(f'{to_cur}/mo'),
        'Financial Loss': monthly_loss.to(f'{to_cur}/mo'),
        'Annual Financial Loss': annual_loss.to(f'{to_cur}/yr'),
        'Cost of Unplanned Downtime': (unplanned_loss + monthly_event_cost).to(f'{to_cur}/mo'),
        'Annual Cost of Unplanned Downtime': annual_unplanned_loss.to(f'{to_cur}/yr'),
        'Margin Loss Before Recovery': (lost_production * margin_per_unit).to(f'{to_cur}/mo'),
        'Margin Loss After Recovery': net_margin_loss.to(f'{to_cur}/mo'),
    }
