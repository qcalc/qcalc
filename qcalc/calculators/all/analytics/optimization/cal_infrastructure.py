# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qcore import as_qtable, qtable
from qutil.mod_runtime_validate import validate_schema_if_needed

from calc import (
    field_show_zero,
    table_capacity_object,
    table_placement_object,
    table_redundancy_object,
    table_routing_object,
)
from calc import safe_objective_value, solver, slack_table


def optima_capacity(
    capacity_object: qtable,
    capacity_qty_type,
    shortage_penalty,
    show_zero,
):
    validate_schema_if_needed('optima_capacity')
    capacity_object = as_qtable(capacity_object)

    resources = capacity_object['Resource'].astype(str).tolist()
    available = dict(zip(capacity_object['Resource'].astype(str), pd.to_numeric(capacity_object['Available'])))
    required = dict(zip(capacity_object['Resource'].astype(str), pd.to_numeric(capacity_object['Required'])))
    unit_cost = dict(zip(capacity_object['Resource'].astype(str), pd.to_numeric(capacity_object['Unit Cost'])))

    var_type = pulp.LpInteger if str(capacity_qty_type).lower() == 'integer' else pulp.LpContinuous
    penalty = float(shortage_penalty)

    prob = pulp.LpProblem('optima_capacity', pulp.LpMinimize)
    alloc = pulp.LpVariable.dicts('Alloc', resources, lowBound=0, cat=var_type)
    short = pulp.LpVariable.dicts('Short', resources, lowBound=0, cat=var_type)

    prob += pulp.lpSum(float(unit_cost[r]) * alloc[r] + penalty * short[r] for r in resources)

    for r in resources:
        prob += alloc[r] <= float(available[r]), f'available_{r}'
        prob += alloc[r] + short[r] == float(required[r]), f'required_{r}'

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    decision_rows = []
    total_alloc = 0.0
    total_short = 0.0
    total_required = 0.0
    for r in resources:
        req = float(required[r])
        avl = float(available[r])
        qty = float(alloc[r].value() or 0)
        sh = float(short[r].value() or 0)
        total_alloc += qty
        total_short += sh
        total_required += req
        if show_zero or qty > 0 or sh > 0:
            decision_rows.append({
                'Resource': r,
                'Required': round(req, 6),
                'Available': round(avl, 6),
                'Allocated': round(qty, 6),
                'Shortage': round(sh, 6),
                'Unit Cost': round(float(unit_cost[r]), 6),
            })

    fulfillment_pct = (total_alloc / total_required * 100.0) if total_required else 0.0

    return {
        'Summary': pd.DataFrame([{
            'Model': 'Capacity',
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Total Required': round(total_required, 6),
            'Total Allocated': round(total_alloc, 6),
            'Total Shortage': round(total_short, 6),
            'Fulfillment %': round(fulfillment_pct, 4),
        }]),
        'Decision Table': pd.DataFrame(decision_rows),
        'Constraint Slack': slack_table(prob),
    }


def optima_routing(
    routing_object: qtable,
    source_node,
    target_node,
    demand_qty,
    routing_flow_type,
    show_zero,
):
    validate_schema_if_needed('optima_routing')
    routing_object = as_qtable(routing_object)

    edges = [(str(r['From']), str(r['To'])) for _, r in routing_object.iterrows()]
    cost = {(str(r['From']), str(r['To'])): float(r['Cost']) for _, r in routing_object.iterrows()}
    capacity = {(str(r['From']), str(r['To'])): float(r['Capacity']) for _, r in routing_object.iterrows()}

    nodes = sorted({n for edge in edges for n in edge})
    source = str(source_node)
    target = str(target_node)
    demand = float(demand_qty)

    if source == target:
        raise Exception('source_node and target_node must be different')
    if source not in nodes:
        raise Exception(f'source_node not found in routing_object nodes: {source}')
    if target not in nodes:
        raise Exception(f'target_node not found in routing_object nodes: {target}')
    if demand <= 0:
        raise Exception('demand_qty must be greater than zero')

    var_type = pulp.LpInteger if str(routing_flow_type).lower() == 'integer' else pulp.LpContinuous

    prob = pulp.LpProblem('optima_routing', pulp.LpMinimize)
    flow = pulp.LpVariable.dicts('Flow', edges, lowBound=0, cat=var_type)

    prob += pulp.lpSum(cost[edge] * flow[edge] for edge in edges)

    for edge in edges:
        prob += flow[edge] <= float(capacity[edge]), f'cap_{edge[0]}_{edge[1]}'

    for n in nodes:
        out_flow = pulp.lpSum(flow[e] for e in edges if e[0] == n)
        in_flow = pulp.lpSum(flow[e] for e in edges if e[1] == n)
        if n == source:
            prob += out_flow - in_flow == demand, f'node_{n}'
        elif n == target:
            prob += in_flow - out_flow == demand, f'node_{n}'
        else:
            prob += out_flow - in_flow == 0, f'node_{n}'

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    decision_rows = []
    total_flow = 0.0
    for edge in edges:
        val = float(flow[edge].value() or 0)
        total_flow += val
        if show_zero or val > 0:
            cap = float(capacity[edge])
            decision_rows.append({
                'From': edge[0],
                'To': edge[1],
                'Flow': round(val, 6),
                'Capacity': round(cap, 6),
                'Utilization %': round((val / cap * 100.0) if cap else 0, 4),
                'Unit Cost': round(float(cost[edge]), 6),
            })

    return {
        'Summary': pd.DataFrame([{
            'Model': 'Routing',
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Source': source,
            'Target': target,
            'Demand Qty': round(demand, 6),
            'Total Edge Flow': round(total_flow, 6),
        }]),
        'Decision Table': pd.DataFrame(decision_rows),
        'Constraint Slack': slack_table(prob),
    }


def optima_placement(
    placement_object: qtable,
    objective_mode,
    location_capacity,
    score_weight,
    show_zero,
):
    validate_schema_if_needed('optima_placement')
    placement_object = as_qtable(placement_object)

    entities = placement_object['Entity'].astype(str).unique().tolist()
    locations = placement_object['Location'].astype(str).unique().tolist()

    pair_score = {}
    pair_cost = {}
    for _, r in placement_object.iterrows():
        pair = (str(r['Entity']), str(r['Location']))
        pair_score[pair] = float(r['Score'])
        pair_cost[pair] = float(r['Cost'])

    pairs = list(pair_score.keys())
    if not pairs:
        raise Exception('placement_object must contain at least one entity-location row')

    for e in entities:
        if not any(pair[0] == e for pair in pairs):
            raise Exception(f'No placement row found for entity: {e}')

    cap = int(location_capacity)
    if cap <= 0:
        raise Exception('location_capacity must be greater than zero')

    sw = float(score_weight)
    mode = str(objective_mode).strip().lower()

    prob = pulp.LpProblem(
        'optima_placement',
        pulp.LpMaximize if mode == 'maximize_score' else pulp.LpMinimize,
    )
    x = pulp.LpVariable.dicts('Place', pairs, lowBound=0, upBound=1, cat=pulp.LpBinary)

    blended = pulp.lpSum((sw * pair_score[p] - pair_cost[p]) * x[p] for p in pairs)
    if mode == 'maximize_score':
        prob += blended
    else:
        # Minimize cost while still encouraging higher score via `score_weight`.
        prob += -blended

    for e in entities:
        e_pairs = [p for p in pairs if p[0] == e]
        prob += pulp.lpSum(x[p] for p in e_pairs) == 1, f'entity_{e}'

    for loc in locations:
        l_pairs = [p for p in pairs if p[1] == loc]
        prob += pulp.lpSum(x[p] for p in l_pairs) <= cap, f'location_{loc}'

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    decision_rows = []
    total_score = 0.0
    total_cost = 0.0
    for p in pairs:
        selected = int(round(float(x[p].value() or 0)))
        score = float(pair_score[p])
        cost = float(pair_cost[p])
        if selected:
            total_score += score
            total_cost += cost
        if show_zero or selected > 0:
            decision_rows.append({
                'Entity': p[0],
                'Location': p[1],
                'Selected': selected,
                'Score': round(score, 6),
                'Cost': round(cost, 6),
            })

    return {
        'Summary': pd.DataFrame([{
            'Model': 'Placement',
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Objective Mode': mode,
            'Location Capacity': cap,
            'Total Score': round(total_score, 6),
            'Total Cost': round(total_cost, 6),
        }]),
        'Decision Table': pd.DataFrame(decision_rows),
        'Constraint Slack': slack_table(prob),
    }


def optima_redundancy(
    redundancy_object: qtable,
    min_avg_coverage,
    redundancy_budget_limit,
    show_zero,
):
    validate_schema_if_needed('optima_redundancy')
    redundancy_object = as_qtable(redundancy_object)

    rows = []
    for idx, r in redundancy_object.iterrows():
        rows.append({
            'id': int(idx),
            'Primary': str(r['Primary']),
            'Backup': str(r['Backup']),
            'Coverage': float(r['Coverage %']),
            'ExtraCost': float(r['Extra Cost']),
        })

    if not rows:
        raise Exception('redundancy_object must contain at least one primary-backup row')

    primaries = sorted({r['Primary'] for r in rows})

    for p in primaries:
        if not any(r['Primary'] == p for r in rows):
            raise Exception(f'No redundancy rows found for primary: {p}')

    prob = pulp.LpProblem('optima_redundancy', pulp.LpMinimize)
    y = pulp.LpVariable.dicts('Select', [r['id'] for r in rows], lowBound=0, upBound=1, cat=pulp.LpBinary)

    total_extra_cost = pulp.lpSum(r['ExtraCost'] * y[r['id']] for r in rows)
    prob += total_extra_cost

    for p in primaries:
        p_rows = [r for r in rows if r['Primary'] == p]
        prob += pulp.lpSum(y[r['id']] for r in p_rows) == 1, f'primary_{p}'

    min_cov = None if min_avg_coverage in ('', None) else float(min_avg_coverage)
    if min_cov is not None:
        prob += (
            pulp.lpSum(r['Coverage'] * y[r['id']] for r in rows)
            >= min_cov * pulp.lpSum(y[r['id']] for r in rows),
            'min_avg_coverage',
        )

    budget = None if redundancy_budget_limit in ('', None) else float(redundancy_budget_limit)
    if budget is not None:
        prob += total_extra_cost <= budget, 'budget_limit'

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    decision_rows = []
    total_coverage = 0.0
    selected_count = 0
    total_cost = 0.0
    for r in rows:
        selected = int(round(float(y[r['id']].value() or 0)))
        if selected:
            selected_count += 1
            total_coverage += float(r['Coverage'])
            total_cost += float(r['ExtraCost'])
        if show_zero or selected > 0:
            decision_rows.append({
                'Primary': r['Primary'],
                'Backup': r['Backup'],
                'Selected': selected,
                'Coverage %': round(float(r['Coverage']), 6),
                'Extra Cost': round(float(r['ExtraCost']), 6),
            })

    avg_coverage = (total_coverage / selected_count) if selected_count else 0.0

    return {
        'Summary': pd.DataFrame([{
            'Model': 'Redundancy',
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Selected Pairs': int(selected_count),
            'Average Coverage %': round(avg_coverage, 6),
            'Total Extra Cost': round(total_cost, 6),
        }]),
        'Decision Table': pd.DataFrame(decision_rows),
        'Constraint Slack': slack_table(prob),
    }


def optima_capacity__info():
    return {
        'title': 'Optimization: Capacity',
        'desc': (
            'Allocate limited capacity to required demand while minimizing cost and shortage penalties.'
            ' Use this for capacity planning, staffing plans, and shortfall-penalty balancing problems.'
        ),
        'calculate': 'Solve',
        'schema': {
            'capacity_object': table_capacity_object('capacity_object'),
            'capacity_qty_type': {
                'type': 'choice',
                'choices': {'continuous': 'Continuous', 'integer': 'Integer'},
                'initial': 'continuous',
                'help_text': 'Quantity type for allocation/shortage variables. Use the same quantity unit basis as Available and Required.',
            },
            'shortage_penalty': {'initial': 1000, 'help_text': 'Penalty per one unit shortage in the same quantity units as Required.'},
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, capacity planning, linear programming',
    }


def optima_routing__info():
    return {
        'title': 'Optimization: Routing',
        'desc': (
            'Find minimum-cost flow from a source node to a target node over constrained edges.'
            ' Use this for network pathing, lane selection, and constrained transfer-flow problems.'
        ),
        'calculate': 'Solve',
        'schema': {
            'routing_object': table_routing_object('routing_object'),
            'source_node': {'initial': 'N1', 'help_text': 'Source node id.'},
            'target_node': {'initial': 'N4', 'help_text': 'Target node id.'},
            'demand_qty': {'initial': 10, 'help_text': 'Required flow from source to target. Use the same quantity units as edge Capacity in routing_object.'},
            'routing_flow_type': {
                'type': 'choice',
                'choices': {'continuous': 'Continuous', 'integer': 'Integer'},
                'initial': 'continuous',
                'help_text': 'Flow type for route variables. Values are interpreted in the same quantity units as demand_qty and edge Capacity.',
            },
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, routing, network flow, linear programming',
    }


def optima_placement__info():
    return {
        'title': 'Optimization: Placement',
        'desc': (
            'Assign entities to locations with a blended score and cost objective under location capacity limits.'
            ' Use this for slotting, host-placement, and entity-to-site assignment problems.'
        ),
        'calculate': 'Solve',
        'schema': {
            'placement_object': table_placement_object('placement_object'),
            'objective_mode': {
                'type': 'choice',
                'choices': {
                    'maximize_score': 'Maximize score (cost-aware)',
                    'minimize_cost': 'Minimize cost (score-aware)',
                },
                'initial': 'maximize_score',
                'help_text': 'Primary optimization orientation.',
            },
            'location_capacity': {'initial': 2, 'help_text': 'Maximum entities assignable to each location.'},
            'score_weight': {'initial': 1.0, 'help_text': 'Weight applied to score in the blended objective.'},
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, placement, assignment, mixed integer programming',
    }


def optima_redundancy__info():
    return {
        'title': 'Optimization: Redundancy',
        'desc': (
            'Select backup pairings with minimum extra cost while meeting optional average coverage targets.'
            ' Use this for backup design, failover planning, and resilience-cost optimization problems.'
        ),
        'calculate': 'Solve',
        'schema': {
            'redundancy_object': table_redundancy_object('redundancy_object'),
            'min_avg_coverage': {'initial': 98.0, 'help_text': 'Minimum average coverage percent target on a 0-100 scale (for example 98 means 98%).'},
            'redundancy_budget_limit': {'initial': None, 'help_text': 'Optional cap on total extra cost.'},
            'show_zero': field_show_zero(),
        },
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, redundancy, resilience, mixed integer programming',
    }








