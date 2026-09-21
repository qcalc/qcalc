# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""First-class optimization calculators with shared schema/default definitions.

Architecture notes:
- Each optimization model is exposed as its own calculator function and `__info` metadata function.
- `_FIELD_DEFS` is the single source of truth for field metadata and default values.
- Defaults are surfaced through `schema[field]['initial']` in each `__info` function.
- Calculator function signatures intentionally avoid inline default assignments; UI defaults come
    from `__info` schema only.
- Table defaults are declared via callables in `_FIELD_DEFS` and materialized per request to
    avoid shared mutable DataFrame instances across users/runs.
"""

import copy
import pandas as pd

from qcore import qtable, as_qtable
from .opt_registry import (
    solve_assignment_model,
    solve_blending_model,
    solve_capacity_model,
    solve_knapsack_model,
    solve_placement_model,
    solve_production_inventory_model,
    solve_project_model,
    solve_redundancy_model,
    solve_routing_model,
    solve_supplier_selection_model,
    solve_transport_model,
    solve_workforce_model,
)


def _default_supply():
    # Generic use: resource/source capacity limits for allocation or flow models.
    # Example use: plant capacity, warehouse stock, server throughput caps.
    return pd.DataFrame({'Source': ['P1', 'P2'], 'Capacity': [100, 125]})


def _default_demand():
    # Generic use: required demand or workload targets that must be met.
    # Example use: customer orders, department demand, service request volume.
    return pd.DataFrame({'Destination': ['C1', 'C2', 'C3'], 'Demand': [25, 95, 80]})


def _default_ship_cost():
    # Generic use: pairwise variable cost matrix between source and destination nodes.
    # Example use: shipping cost, transfer latency penalty, energy loss cost.
    return pd.DataFrame({
        'Source': ['P1', 'P1', 'P1', 'P2', 'P2', 'P2'],
        'Destination': ['C1', 'C2', 'C3', 'C1', 'C2', 'C3'],
        'Cost': [250, 325, 445, 275, 260, 460],
    })


def _default_agents():
    # Generic use: assignable resources with per-resource capacity constraints.
    # Example use: workers, machines, support teams, compute nodes.
    return pd.DataFrame({'Agent': ['A1', 'A2', 'A3'], 'Capacity': [1, 1, 1]})


def _default_tasks():
    # Generic use: work items or targets that need one-to-one assignment.
    # Example use: jobs, tickets, inspection points, deployment tasks.
    return pd.DataFrame({'Task': ['T1', 'T2', 'T3']})


def _default_assign_cost():
    # Generic use: assignment cost matrix from each resource to each work item.
    # Example use: labor cost, completion time, risk score, travel burden.
    return pd.DataFrame({
        'Agent': ['A1', 'A1', 'A1', 'A2', 'A2', 'A2', 'A3', 'A3', 'A3'],
        'Task': ['T1', 'T2', 'T3', 'T1', 'T2', 'T3', 'T1', 'T2', 'T3'],
        'Cost': [14, 5, 8, 2, 12, 6, 7, 8, 3],
    })


def _default_items():
    # Generic use: candidate options with value, weight, and optional quantity cap.
    # Example use: product mix, project portfolio, feature selection, cargo loading.
    return pd.DataFrame({
        'Item': ['I1', 'I2', 'I3', 'I4'],
        'Value': [12, 10, 20, 15],
        'Weight': [2, 1, 3, 2],
        'Max Qty': [1, 1, 1, 1],
    })


def _default_material_demand():
    # Generic use: per-item demand requirement that procurement must satisfy.
    # Example use: raw material plans, SKU replenishment, component needs.
    return pd.DataFrame({
        'Item': ['I1', 'I2', 'I3'],
        'Demand': [100, 80, 60],
    })


def _default_supplier_master():
    # Generic use: provider attributes including capacity and fixed activation cost.
    # Example use: supplier onboarding cost, contractor retainers, service tiers.
    return pd.DataFrame({
        'Supplier': ['S1', 'S2', 'S3'],
        'Capacity': [180, 160, 140],
        'Fixed Cost': [500, 650, 450],
        'Min Order': [0, 0, 0],
        'Risk': [4, 7, 3],
        'Quality': [82, 75, 88],
    })


def _default_supplier_item_cost():
    # Generic use: provider-item variable cost table with optional pairwise max limit.
    # Example use: contract pricing grids, lane rates, source-specific unit costs.
    return pd.DataFrame({
        'Supplier': ['S1', 'S1', 'S1', 'S2', 'S2', 'S2', 'S3', 'S3', 'S3'],
        'Item': ['I1', 'I2', 'I3', 'I1', 'I2', 'I3', 'I1', 'I2', 'I3'],
        'Unit Cost': [11, 13, 12, 10, 14, 13, 12, 12, 11],
        'Max Qty': [100, 80, 60, 100, 80, 60, 100, 80, 60],
    })


def _default_blend_materials():
    # Generic use: raw/input materials with costs, optional quantity bounds,
    # and composition columns for any constrained properties.
    return pd.DataFrame({
        'Material': ['A', 'B', 'C'],
        'Unit Cost': [0.50, 0.35, 0.70],
        'Min Qty': [0, 0, 0],
        'Max Qty': [400, None, None],
        'Protein %': [30, 15, 40],
        'Fiber %': [2, 4, 8],
    })


def _default_blend_specs():
    # Generic use: product-level property constraints.
    # Enter percentages as whole percent (e.g., 20) or fraction (e.g., 0.20).
    return pd.DataFrame({
        'Property': ['Protein', 'Fiber'],
        'Min %': [20, None],
        'Max %': [None, 5],
    })


def _default_capacity_object():
    # Generic use: capacity planning table balancing available and required quantities.
    # Example use: production lines, staffing blocks, cloud quota envelopes.
    return pd.DataFrame({
        'Resource': ['R1', 'R2', 'R3'],
        'Available': [120, 95, 80],
        'Required': [70, 60, 50],
        'Unit Cost': [5, 6, 7],
    })


def _default_routing_object():
    # Generic use: route graph edges with movement cost and optional capacity.
    # Example use: logistics lanes, network links, workflow transfer paths.
    return pd.DataFrame({
        'From': ['N1', 'N1', 'N2', 'N2', 'N3'],
        'To': ['N2', 'N3', 'N3', 'N4', 'N4'],
        'Cost': [4, 7, 3, 6, 2],
        'Capacity': [100, 80, 90, 70, 110],
    })


def _default_placement_object():
    # Generic use: entity-to-location placement scoring/cost matrix.
    # Example use: VM-to-host assignment, SKU-to-bin slotting, team-to-site placement.
    return pd.DataFrame({
        'Entity': ['E1', 'E1', 'E2', 'E2', 'E3', 'E3'],
        'Location': ['L1', 'L2', 'L1', 'L2', 'L1', 'L2'],
        'Score': [9, 7, 8, 6, 7, 9],
        'Cost': [5, 4, 6, 3, 4, 5],
    })


def _default_redundancy_object():
    # Generic use: primary/backup pairing inputs with resilience and cost factors.
    # Example use: failover design, supplier backup plans, spare-capacity strategy.
    return pd.DataFrame({
        'Primary': ['P1', 'P2', 'P3'],
        'Backup': ['B1', 'B2', 'B3'],
        'Coverage %': [99.0, 97.5, 98.8],
        'Extra Cost': [12, 9, 11],
    })


def _default_projects():
    # Generic use: project candidate table with value, cost, and optional resource usage.
    # Example use: capex pipeline, feature roadmap, portfolio intake decisions.
    return pd.DataFrame({
        'Project': ['P1', 'P2', 'P3', 'P4', 'P5'],
        'Value': [180, 130, 170, 115, 90],
        'Cost': [95, 75, 100, 55, 45],
        'Resource': [5, 4, 6, 3, 2],
        'Must Do': [0, 0, 0, 0, 0],
    })


def _default_project_rules():
    # Generic use: relation rules between project pairs.
    # Type supports 'depends_on' and 'excludes'.
    return pd.DataFrame({
        'From': ['P3', 'P2'],
        'To': ['P1', 'P4'],
        'Type': ['depends_on', 'excludes'],
    })


def _default_workforce_staff():
    # Generic use: available workers with assignment limits and per-shift cost.
    # Optional Skills uses comma-separated tags for skill-constrained shifts.
    return pd.DataFrame({
        'Worker': ['W1', 'W2', 'W3', 'W4'],
        'Max Shifts': [3, 2, 2, 1],
        'Cost per Shift': [100, 90, 95, 110],
        'Skills': ['packing,forklift', 'packing', 'quality', 'forklift,quality'],
    })


def _default_workforce_shift_demand():
    # Generic use: required staffing per shift with optional required skill.
    return pd.DataFrame({
        'Shift': ['Day-1', 'Day-2', 'Night-1'],
        'Required': [2, 2, 1],
        'Required Skill': ['packing', '', 'quality'],
    })


def _default_prodinv_item_master():
    # Generic use: item-level inventory economics.
    return pd.DataFrame({
        'Item': ['A', 'B'],
        'Initial Inventory': [20, 10],
        'Holding Cost': [1.5, 1.0],
        'Backlog Penalty': [12, 10],
    })


def _default_prodinv_demand():
    # Generic use: period demand by item.
    return pd.DataFrame({
        'Period': ['1', '1', '2', '2', '3', '3'],
        'Item': ['A', 'B', 'A', 'B', 'A', 'B'],
        'Demand': [50, 45, 55, 40, 60, 50],
    })


def _default_prodinv_production():
    # Generic use: period production economics and capacity by item.
    return pd.DataFrame({
        'Period': ['1', '1', '2', '2', '3', '3'],
        'Item': ['A', 'B', 'A', 'B', 'A', 'B'],
        'Unit Cost': [7.0, 6.5, 7.2, 6.6, 7.4, 6.8],
        'Max Production': [65, 55, 65, 55, 70, 60],
        'Setup Cost': [20, 15, 20, 15, 20, 15],
    })


_FIELD_DEFS = {
    # Transport model fields
    'supply': {
        'initial': _default_supply,
    },
    'demand': {
        'initial': _default_demand,
    },
    'ship_cost': {
        'initial': _default_ship_cost,
    },
    'flow_type': {
        'type': 'choice',
        'choices': {'continuous': 'Continuous', 'integer': 'Integer'},
        'initial': 'integer',
        'help_text': 'Quantity type for shipment flow variables.',
    },
    # Assignment model fields
    'agents': {
        'initial': _default_agents,
    },
    'tasks': {
        'initial': _default_tasks,
    },
    'assign_cost': {
        'initial': _default_assign_cost,
    },
    # Knapsack model fields
    'items': {
        'initial': _default_items,
    },
    'capacity_limit': {
        'initial': 5,
        'help_text': 'Knapsack capacity / budget limit',
    },
    'decision_type': {
        'type': 'choice',
        'choices': {'binary': 'Binary (0/1)', 'integer': 'Integer (0..Max Qty)'},
        'initial': 'binary',
        'help_text': 'Choose binary (0/1) or integer quantities up to Max Qty.',
    },
    # Supplier selection model fields
    'material_demand': {
        'initial': _default_material_demand,
    },
    'supplier_master': {
        'initial': _default_supplier_master,
    },
    'supplier_item_cost': {
        'initial': _default_supplier_item_cost,
    },
    'blend_materials': {
        'initial': _default_blend_materials,
        'help_text': (
            'Material table with Unit Cost, optional Min Qty/Max Qty, and one column per property '
            '(for example Protein %, Fiber %, Moisture %).'
        ),
    },
    'blend_specs': {
        'initial': _default_blend_specs,
        'help_text': (
            "Specification table with Property, Min %, Max %. "
            "Property names must match blend_materials property columns (ignoring trailing '%'). "
            "Percent entries are interpreted as whole-percent values (for example 20 means 20%, 0.5 means 0.5%)."
        ),
    },
    'batch_size': {
        'initial': 1000,
        'help_text': 'Target batch size in quantity units (for example kg).',
    },
    'blend_qty_type': {
        'type': 'choice',
        'choices': {'continuous': 'Continuous', 'integer': 'Integer'},
        'initial': 'continuous',
        'help_text': 'Quantity type for material decision variables.',
    },
    'max_suppliers': {
        'initial': 0,
        'help_text': 'Set 0 for no limit on number of suppliers.',
    },
    'material_qty_type': {
        'type': 'choice',
        'choices': {'continuous': 'Continuous', 'integer': 'Integer'},
        'initial': 'continuous',
        'help_text': 'Quantity type for material purchase variables.',
    },
    'budget_limit': {
        'initial': None,
        'help_text': 'Optional total spend cap including variable and fixed costs.',
    },
    'min_avg_quality': {
        'initial': None,
        'help_text': "Optional lower bound on demand-weighted average quality; requires 'Quality' in supplier_master.",
    },
    'max_avg_risk': {
        'initial': None,
        'help_text': "Optional upper bound on demand-weighted average risk; requires 'Risk' in supplier_master.",
    },
    # Shared display/output behavior
    'show_zero': {
        'type': 'choice',
        'choices': {False: 'No', True: 'Yes'},
        'initial': False,
        'help_text': 'Show zero-valued decisions in output',
    },
    # Capacity model fields
    'capacity_object': {
        'initial': _default_capacity_object,
        'help_text': 'Table of resources with available quantity, required quantity, and unit cost.',
    },
    # Routing model fields
    'routing_object': {
        'initial': _default_routing_object,
        'help_text': 'Table of route edges with source, destination, cost, and capacity.',
    },
    # Placement model fields
    'placement_object': {
        'initial': _default_placement_object,
        'help_text': 'Table of entity-location options with score and cost.',
    },
    # Redundancy model fields
    'redundancy_object': {
        'initial': _default_redundancy_object,
        'help_text': 'Table of primary-backup pair options with coverage and extra cost.',
    },
    'capacity_qty_type': {
        'type': 'choice',
        'choices': {'continuous': 'Continuous', 'integer': 'Integer'},
        'initial': 'continuous',
        'help_text': 'Quantity type for allocation variables.',
    },
    'shortage_penalty': {
        'initial': 1000,
        'help_text': 'Penalty per unit shortage in the objective.',
    },
    'source_node': {
        'initial': 'N1',
        'help_text': 'Source node id.',
    },
    'target_node': {
        'initial': 'N4',
        'help_text': 'Target node id.',
    },
    'demand_qty': {
        'initial': 10,
        'help_text': 'Required flow from source to target.',
    },
    'routing_flow_type': {
        'type': 'choice',
        'choices': {'continuous': 'Continuous', 'integer': 'Integer'},
        'initial': 'continuous',
        'help_text': 'Flow type for route variables.',
    },
    'objective_mode': {
        'type': 'choice',
        'choices': {
            'maximize_score': 'Maximize score (cost-aware)',
            'minimize_cost': 'Minimize cost (score-aware)',
        },
        'initial': 'maximize_score',
        'help_text': 'Primary optimization orientation.',
    },
    'location_capacity': {
        'initial': 2,
        'help_text': 'Maximum entities assignable to each location.',
    },
    'score_weight': {
        'initial': 1.0,
        'help_text': 'Weight applied to score in the blended objective.',
    },
    'min_avg_coverage': {
        'initial': 98.0,
        'help_text': 'Minimum average coverage percent target.',
    },
    'redundancy_budget_limit': {
        'initial': None,
        'help_text': 'Optional cap on total extra cost.',
    },
    # Project portfolio model fields
    'projects': {
        'initial': _default_projects,
        'help_text': 'Project table with Project, Value, Cost and optional Resource, Must Do columns.',
    },
    'project_rules': {
        'initial': _default_project_rules,
        'help_text': "Optional relation rules: Type in {'depends_on', 'excludes'}.",
    },
    'project_budget_limit': {
        'initial': 220,
        'help_text': 'Set empty for no budget cap on selected projects.',
    },
    'project_resource_limit': {
        'initial': None,
        'help_text': "Optional total resource cap; requires 'Resource' column in projects.",
    },
    'project_max_selected': {
        'initial': 0,
        'help_text': 'Set 0 for no upper limit on number of selected projects.',
    },
    'project_min_selected': {
        'initial': 0,
        'help_text': 'Set 0 for no lower limit on number of selected projects.',
    },
    # Workforce scheduling model fields
    'workforce_staff': {
        'initial': _default_workforce_staff,
        'help_text': 'Worker table with max shifts, cost per shift, and optional comma-separated skills.',
    },
    'workforce_shift_demand': {
        'initial': _default_workforce_shift_demand,
        'help_text': "Shift demand table with required headcount and optional 'Required Skill'.",
    },
    'allow_shortage': {
        'type': 'choice',
        'choices': {False: 'No', True: 'Yes'},
        'initial': True,
        'help_text': 'Allow unmet shift demand with penalty instead of infeasible solve.',
    },
    'shortage_penalty': {
        'initial': 1000,
        'help_text': 'Penalty cost per unit unmet shift demand when shortage is allowed.',
    },
    # Production-inventory planning model fields
    'prodinv_item_master': {
        'initial': _default_prodinv_item_master,
        'help_text': 'Item economics with initial inventory, holding cost, and backlog penalty.',
    },
    'prodinv_demand': {
        'initial': _default_prodinv_demand,
        'help_text': 'Period-wise demand table by item.',
    },
    'prodinv_production': {
        'initial': _default_prodinv_production,
        'help_text': 'Period-item production cost, capacity, and optional setup cost.',
    },
    'prodinv_qty_type': {
        'type': 'choice',
        'choices': {'continuous': 'Continuous', 'integer': 'Integer'},
        'initial': 'continuous',
        'help_text': 'Quantity type for production, inventory, and backlog variables.',
    },
    'prodinv_allow_backlog': {
        'type': 'choice',
        'choices': {False: 'No', True: 'Yes'},
        'initial': True,
        'help_text': 'Allow backlog carry-forward with penalty; disable to force demand-time fulfillment.',
    },
}


def _field_schema(name):
    spec = copy.deepcopy(_FIELD_DEFS[name])
    if 'initial' in spec and callable(spec['initial']):
        spec['initial'] = spec['initial']()
    return spec


def _schema_for(fields):
    return {field: _field_schema(field) for field in fields}


def optima_transport__info():
    return {
        'title': 'Optimization: Transportation',
        'desc': (
            'Minimize total shipping cost from sources to destinations under supply and demand constraints.'
            ' Use this for distribution, replenishment, and source-to-demand allocation problems.'
        ),
        'calculate': 'Solve',
        'schema': _schema_for(['supply', 'demand', 'ship_cost', 'flow_type', 'show_zero']),
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, transportation, linear programming',
    }


def optima_assignment__info():
    return {
        'title': 'Optimization: Assignment',
        'desc': (
            'Assign tasks to agents at minimum total cost under capacity constraints.'
            ' Use this for worker-task assignment, machine-job assignment, and ticket routing problems.'
        ),
        'calculate': 'Solve',
        'schema': _schema_for(['agents', 'tasks', 'assign_cost', 'show_zero']),
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, assignment, mixed integer programming',
    }


def optima_knapsack__info():
    return {
        'title': 'Optimization: Knapsack',
        'desc': (
            'Maximize value under a capacity limit with binary or integer item decisions.'
            ' Use this for budget selection, portfolio picking, and constrained mix-selection problems.'
        ),
        'calculate': 'Solve',
        'schema': _schema_for(['items', 'capacity_limit', 'decision_type', 'show_zero']),
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, knapsack, integer programming',
    }


def optima_supplier_selection__info():
    return {
        'title': 'Optimization: Supplier Selection',
        'desc': (
            'Minimize procurement cost with supplier capacities, optional budget, and risk/quality controls.'
            ' Use this for sourcing decisions, vendor mix planning, and cost-risk-quality trade-off problems.'
        ),
        'calculate': 'Solve',
        'schema': _schema_for([
            'material_demand',
            'supplier_master',
            'supplier_item_cost',
            'max_suppliers',
            'material_qty_type',
            'budget_limit',
            'min_avg_quality',
            'max_avg_risk',
            'show_zero',
        ]),
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, supplier selection, mixed integer programming',
    }


def optima_blending__info():
    return {
        'title': 'Optimization: Raw Material Mix',
        'desc': (
            'Minimize total blend cost while meeting batch-size and property specifications '
            'with optional min/max bounds per material. '
            'Use this for feed formulation, food blending, chemicals, alloys, fuels, and fertilizer mixes.'
        ),
        'calculate': 'Solve',
        'schema': _schema_for([
            'blend_materials',
            'blend_specs',
            'batch_size',
            'blend_qty_type',
            'show_zero',
        ]),
        'layout': 'lr',
        'out1': ['Summary', 'Optimal Mix', 'Property Compliance'],
        'tags': 'optimization, blending, product mix, linear programming',
    }


def optima_capacity__info():
    return {
        'title': 'Optimization: Capacity',
        'desc': (
            'Allocate limited capacity to required demand while minimizing cost and shortage penalties.'
            ' Use this for capacity planning, staffing plans, and shortfall-penalty balancing problems.'
        ),
        'calculate': 'Solve',
        'schema': _schema_for(['capacity_object', 'capacity_qty_type', 'shortage_penalty', 'show_zero']),
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
        'schema': _schema_for([
            'routing_object',
            'source_node',
            'target_node',
            'demand_qty',
            'routing_flow_type',
            'show_zero',
        ]),
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
        'schema': _schema_for([
            'placement_object',
            'objective_mode',
            'location_capacity',
            'score_weight',
            'show_zero',
        ]),
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
        'schema': _schema_for([
            'redundancy_object',
            'min_avg_coverage',
            'redundancy_budget_limit',
            'show_zero',
        ]),
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, redundancy, resilience, mixed integer programming',
    }


def optima_project__info():
    return {
        'title': 'Optimization: Project Portfolio',
        'desc': (
            'Select projects to maximize portfolio value under optional budget, resource, and relation constraints.'
            ' Use this for project intake, capex planning, and constrained portfolio selection problems.'
        ),
        'calculate': 'Solve',
        'schema': _schema_for([
            'projects',
            'project_rules',
            'project_budget_limit',
            'project_resource_limit',
            'project_max_selected',
            'project_min_selected',
            'show_zero',
        ]),
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, project portfolio, knapsack, mixed integer programming',
    }


def optima_workforce__info():
    return {
        'title': 'Optimization: Workforce Shift Scheduling',
        'desc': (
            'Assign workers to shifts at minimum labor cost with max-shift limits and optional skill matching.'
            ' Optionally allow shortages with penalty to keep the problem feasible under tight staffing.'
        ),
        'calculate': 'Solve',
        'schema': _schema_for([
            'workforce_staff',
            'workforce_shift_demand',
            'allow_shortage',
            'shortage_penalty',
            'show_zero',
        ]),
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table', 'Coverage Table', 'Worker Utilization'],
        'tags': 'optimization, workforce, scheduling, staffing, mixed integer programming',
    }


def optima_production_inventory__info():
    return {
        'title': 'Optimization: Production and Inventory Planning',
        'desc': (
            'Minimize total production, holding, setup, and optional backlog cost across multiple periods.'
            ' Use this for finite-capacity production planning and inventory balance decisions.'
        ),
        'calculate': 'Solve',
        'schema': _schema_for([
            'prodinv_item_master',
            'prodinv_demand',
            'prodinv_production',
            'prodinv_qty_type',
            'prodinv_allow_backlog',
            'show_zero',
        ]),
        'layout': 'lr',
        'out1': ['Summary', 'Decision Table'],
        'tags': 'optimization, production planning, inventory, lot sizing, linear programming',
    }


def optima_transport(
    supply: qtable,
    demand: qtable,
    ship_cost: qtable,
    flow_type,
    show_zero,
):
    supply = as_qtable(supply)
    demand = as_qtable(demand)
    ship_cost = as_qtable(ship_cost)
    return solve_transport_model(
        supply=supply,
        demand=demand,
        ship_cost=ship_cost,
        flow_type=flow_type,
        show_zero=show_zero,
    )


def optima_assignment(
    agents: qtable,
    tasks: qtable,
    assign_cost: qtable,
    show_zero,
):
    agents = as_qtable(agents)
    tasks = as_qtable(tasks)
    assign_cost = as_qtable(assign_cost)
    return solve_assignment_model(
        agents=agents,
        tasks=tasks,
        assign_cost=assign_cost,
        show_zero=show_zero,
    )


def optima_knapsack(
    items: qtable,
    capacity_limit,
    decision_type,
    show_zero,
):
    items = as_qtable(items)
    return solve_knapsack_model(
        items=items,
        capacity_limit=capacity_limit,
        decision_type=decision_type,
        show_zero=show_zero,
    )


def optima_supplier_selection(
    material_demand: qtable,
    supplier_master: qtable,
    supplier_item_cost: qtable,
    max_suppliers,
    material_qty_type,
    budget_limit,
    min_avg_quality,
    max_avg_risk,
    show_zero,
):
    material_demand = as_qtable(material_demand)
    supplier_master = as_qtable(supplier_master)
    supplier_item_cost = as_qtable(supplier_item_cost)
    return solve_supplier_selection_model(
        material_demand=material_demand,
        supplier_master=supplier_master,
        supplier_item_cost=supplier_item_cost,
        max_suppliers=max_suppliers,
        material_qty_type=material_qty_type,
        budget_limit=budget_limit,
        min_avg_quality=min_avg_quality,
        max_avg_risk=max_avg_risk,
        show_zero=show_zero,
    )


def optima_blending(
    blend_materials: qtable,
    blend_specs: qtable,
    batch_size,
    blend_qty_type,
    show_zero,
):
    blend_materials = as_qtable(blend_materials)
    blend_specs = as_qtable(blend_specs)
    return solve_blending_model(
        blend_materials=blend_materials,
        blend_specs=blend_specs,
        batch_size=batch_size,
        blend_qty_type=blend_qty_type,
        show_zero=show_zero,
    )


def optima_capacity(
    capacity_object: qtable,
    capacity_qty_type,
    shortage_penalty,
    show_zero,
):
    capacity_object = as_qtable(capacity_object)
    return solve_capacity_model(
        capacity_object=capacity_object,
        capacity_qty_type=capacity_qty_type,
        shortage_penalty=shortage_penalty,
        show_zero=show_zero,
    )


def optima_routing(
    routing_object: qtable,
    source_node,
    target_node,
    demand_qty,
    routing_flow_type,
    show_zero,
):
    routing_object = as_qtable(routing_object)
    return solve_routing_model(
        routing_object=routing_object,
        source_node=source_node,
        target_node=target_node,
        demand_qty=demand_qty,
        routing_flow_type=routing_flow_type,
        show_zero=show_zero,
    )


def optima_placement(
    placement_object: qtable,
    objective_mode,
    location_capacity,
    score_weight,
    show_zero,
):
    placement_object = as_qtable(placement_object)
    return solve_placement_model(
        placement_object=placement_object,
        objective_mode=objective_mode,
        location_capacity=location_capacity,
        score_weight=score_weight,
        show_zero=show_zero,
    )


def optima_redundancy(
    redundancy_object: qtable,
    min_avg_coverage,
    redundancy_budget_limit,
    show_zero,
):
    redundancy_object = as_qtable(redundancy_object)
    return solve_redundancy_model(
        redundancy_object=redundancy_object,
        min_avg_coverage=min_avg_coverage,
        redundancy_budget_limit=redundancy_budget_limit,
        show_zero=show_zero,
    )


def optima_project(
    projects: qtable,
    project_rules: qtable,
    project_budget_limit,
    project_resource_limit,
    project_max_selected,
    project_min_selected,
    show_zero,
):
    projects = as_qtable(projects)
    project_rules = as_qtable(project_rules)
    return solve_project_model(
        projects=projects,
        project_rules=project_rules,
        project_budget_limit=project_budget_limit,
        project_resource_limit=project_resource_limit,
        project_max_selected=project_max_selected,
        project_min_selected=project_min_selected,
        show_zero=show_zero,
    )


def optima_workforce(
    workforce_staff: qtable,
    workforce_shift_demand: qtable,
    allow_shortage,
    shortage_penalty,
    show_zero,
):
    workforce_staff = as_qtable(workforce_staff)
    workforce_shift_demand = as_qtable(workforce_shift_demand)
    return solve_workforce_model(
        workforce_staff=workforce_staff,
        workforce_shift_demand=workforce_shift_demand,
        allow_shortage=allow_shortage,
        shortage_penalty=shortage_penalty,
        show_zero=show_zero,
    )


def optima_production_inventory(
    prodinv_item_master: qtable,
    prodinv_demand: qtable,
    prodinv_production: qtable,
    prodinv_qty_type,
    prodinv_allow_backlog,
    show_zero,
):
    prodinv_item_master = as_qtable(prodinv_item_master)
    prodinv_demand = as_qtable(prodinv_demand)
    prodinv_production = as_qtable(prodinv_production)
    return solve_production_inventory_model(
        prodinv_item_master=prodinv_item_master,
        prodinv_demand=prodinv_demand,
        prodinv_production=prodinv_production,
        prodinv_qty_type=prodinv_qty_type,
        prodinv_allow_backlog=prodinv_allow_backlog,
        show_zero=show_zero,
    )
