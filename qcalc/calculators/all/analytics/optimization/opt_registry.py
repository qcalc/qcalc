# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from .opt_templates.assignment import solve_assignment
from .opt_templates.blending import solve_blending
from .opt_templates.infrastructure import (
    solve_capacity,
    solve_placement,
    solve_redundancy,
    solve_routing,
)
from .opt_templates.knapsack import solve_knapsack
from .opt_templates.production_inventory import solve_production_inventory_planning
from .opt_templates.project import solve_project
from .opt_templates.supplier_selection import solve_supplier_selection
from .opt_templates.transport import solve_transport
from .opt_templates.workforce import solve_workforce_scheduling


def solve_transport_model(**payload):
    return solve_transport(
        payload['supply'],
        payload['demand'],
        payload['ship_cost'],
        payload.get('flow_type', 'integer'),
        payload.get('show_zero', False),
    )


def solve_assignment_model(**payload):
    return solve_assignment(
        payload['agents'],
        payload['tasks'],
        payload['assign_cost'],
        payload.get('show_zero', False),
    )


def solve_knapsack_model(**payload):
    return solve_knapsack(
        payload['items'],
        payload['capacity_limit'],
        payload.get('decision_type', 'binary'),
        payload.get('show_zero', False),
    )


def solve_supplier_selection_model(**payload):
    return solve_supplier_selection(
        payload['material_demand'],
        payload['supplier_master'],
        payload['supplier_item_cost'],
        payload.get('max_suppliers', 0),
        payload.get('material_qty_type', 'continuous'),
        payload.get('budget_limit'),
        payload.get('min_avg_quality'),
        payload.get('max_avg_risk'),
        payload.get('show_zero', False),
    )


def solve_blending_model(**payload):
    return solve_blending(
        payload['blend_materials'],
        payload['blend_specs'],
        payload['batch_size'],
        payload.get('blend_qty_type', 'continuous'),
        payload.get('show_zero', False),
    )


def solve_capacity_model(**payload):
    return solve_capacity(
        payload['capacity_object'],
        payload.get('capacity_qty_type', 'continuous'),
        payload.get('shortage_penalty', 1000),
        payload.get('show_zero', False),
    )


def solve_routing_model(**payload):
    return solve_routing(
        payload['routing_object'],
        payload['source_node'],
        payload['target_node'],
        payload.get('demand_qty', 10),
        payload.get('routing_flow_type', 'continuous'),
        payload.get('show_zero', False),
    )


def solve_placement_model(**payload):
    return solve_placement(
        payload['placement_object'],
        payload.get('objective_mode', 'maximize_score'),
        payload.get('location_capacity', 2),
        payload.get('score_weight', 1.0),
        payload.get('show_zero', False),
    )


def solve_redundancy_model(**payload):
    return solve_redundancy(
        payload['redundancy_object'],
        payload.get('min_avg_coverage', 98.0),
        payload.get('redundancy_budget_limit'),
        payload.get('show_zero', False),
    )


def solve_project_model(**payload):
    return solve_project(
        payload['projects'],
        payload.get('project_rules'),
        payload.get('project_budget_limit'),
        payload.get('project_resource_limit'),
        payload.get('project_max_selected', 0),
        payload.get('project_min_selected', 0),
        payload.get('show_zero', False),
    )


def solve_workforce_model(**payload):
    return solve_workforce_scheduling(
        payload['workforce_staff'],
        payload['workforce_shift_demand'],
        payload.get('allow_shortage', True),
        payload.get('shortage_penalty', 1000),
        payload.get('show_zero', False),
    )


def solve_production_inventory_model(**payload):
    return solve_production_inventory_planning(
        payload['prodinv_item_master'],
        payload['prodinv_demand'],
        payload['prodinv_production'],
        payload.get('prodinv_qty_type', 'continuous'),
        payload.get('prodinv_allow_backlog', True),
        payload.get('show_zero', False),
    )


MODEL_SOLVERS = {
    'transport': solve_transport_model,
    'assignment': solve_assignment_model,
    'knapsack': solve_knapsack_model,
    'supplier_selection': solve_supplier_selection_model,
    'blending': solve_blending_model,
    'capacity': solve_capacity_model,
    'routing': solve_routing_model,
    'placement': solve_placement_model,
    'redundancy': solve_redundancy_model,
    'project': solve_project_model,
    'workforce': solve_workforce_model,
    'production_inventory': solve_production_inventory_model,
}


def solve_model(model_type, **payload):
    mode = (model_type or '').strip().lower()
    handler = MODEL_SOLVERS.get(mode)
    if handler is None:
        raise Exception(
            "Unknown model_type. Use 'transport', 'assignment', 'knapsack', 'supplier_selection', 'blending', "
            "'capacity', 'routing', 'placement', 'redundancy', 'project', 'workforce', or 'production_inventory'."
        )
    return handler(**payload)
