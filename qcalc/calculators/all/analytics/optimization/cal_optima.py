# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""First-class optimization calculators with shared schema/default definitions.

Architecture notes:
- Each optimization model is exposed as its own calculator function and `__info` metadata function.
- Public `table_*` builders are the source of truth for reusable table field metadata and defaults.
- Defaults are surfaced through `schema[field]['initial']` in each `__info` function.
- Calculator function signatures intentionally avoid inline default assignments; UI defaults come
    from `__info` schema only.
"""

import json
import pandas as pd
from django.core.exceptions import ValidationError

from qcore import as_qtable
from qutil import require_columns


def _coerce_table_for_validation(value, field_name):
    """Convert posted table payload into a DataFrame for schema validators."""
    if isinstance(value, str):
        text = value.strip()
        if text in {'', 'null', 'None'}:
            return pd.DataFrame()
        try:
            parsed = json.loads(text)
        except Exception as e:
            raise ValidationError(f"Invalid table payload for {field_name}") from e
        value = parsed

    try:
        return as_qtable(value)
    except Exception as e:
        raise ValidationError(f"Invalid table payload for {field_name}") from e


def table_columns_validator(field_name, required_cols, optional_cols=None):
    optional_cols = optional_cols or []

    def _validator(value):
        table = _coerce_table_for_validation(value, field_name)
        try:
            require_columns(
                table,
                field_name,
                list(required_cols),
                optional_cols=list(optional_cols),
            )
        except Exception as e:
            raise ValidationError(str(e)) from e

    return _validator


def field_show_zero():
    return {
        'type': 'choice',
        'choices': {False: 'No', True: 'Yes'},
        'initial': False,
        'help_text': 'Show zero-valued decisions in output',
    }


def table_blend_materials(field_name):
    return {
        'initial': pd.DataFrame({
            'Material': ['A', 'B', 'C'],
            'Unit Cost': [0.50, 0.35, 0.70],
            'Min Qty': [0, 0, 0],
            'Max Qty': [400, None, None],
            'Protein %': [30, 15, 40],
            'Fiber %': [2, 4, 8],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Material', 'Unit Cost'],
                optional_cols=['Min Qty', 'Max Qty'],
            )
        ],
        'help_text': (
            'Material table with Unit Cost, optional Min Qty/Max Qty, and one column per property '
            '(for example Protein %, Fiber %, Moisture %).'
        ),
    }


def table_blend_specs(field_name):
    return {
        # Generic use: product-level property constraints.
        # Enter percentages as whole percent (e.g., 20) or fraction (e.g., 0.20).
        'initial': pd.DataFrame({
            'Property': ['Protein', 'Fiber'],
            'Min %': [20, None],
            'Max %': [None, 5],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Property', 'Min %', 'Max %'],
            )
        ],
        'help_text': (
            "Specification table with Property, Min %, Max %. "
            "Property names must match blend_materials property columns (ignoring trailing '%'). "
            "Percent entries are interpreted as whole-percent values (for example 20 means 20%, 0.5 means 0.5%)."
        ),
    }


def table_supply(field_name):
    # Generic use: resource/source capacity limits for allocation or flow models.
    # Example use: plant capacity, warehouse stock, server throughput caps.
    return {
        'initial': pd.DataFrame({'Source': ['P1', 'P2'], 'Capacity': [100, 125]}),
        'validators': [table_columns_validator(field_name, required_cols=['Source', 'Capacity'])],
        'help_text': 'Source capacity table. Capacity must use the same quantity unit basis as demand and flow decisions.',
    }


def table_demand(field_name):
    # Generic use: required demand or workload targets that must be met.
    # Example use: customer orders, department demand, service request volume.
    return {
        'initial': pd.DataFrame({'Destination': ['C1', 'C2', 'C3'], 'Demand': [25, 95, 80]}),
        'validators': [table_columns_validator(field_name, required_cols=['Destination', 'Demand'])],
        'help_text': 'Demand table by destination. Demand must use the same quantity unit basis as supply capacity and flow decisions.',
    }


def table_ship_cost(field_name):
    # Generic use: pairwise variable cost matrix between source and destination nodes.
    # Example use: shipping cost, transfer latency penalty, energy loss cost.
    return {
        'initial': pd.DataFrame({
            'Source': ['P1', 'P1', 'P1', 'P2', 'P2', 'P2'],
            'Destination': ['C1', 'C2', 'C3', 'C1', 'C2', 'C3'],
            'Cost': [250, 325, 445, 275, 260, 460],
        }),
        'validators': [table_columns_validator(field_name, required_cols=['Source', 'Destination', 'Cost'])],
        'help_text': 'Shipping cost per unit flow for each Source-Destination pair. Cost is interpreted per one quantity unit.',
    }


def table_agents(field_name):
    # Generic use: assignable resources with per-resource capacity constraints.
    # Example use: workers, machines, support teams, compute nodes.
    return {
        'initial': pd.DataFrame({'Agent': ['A1', 'A2', 'A3'], 'Capacity': [1, 1, 1]}),
        'validators': [table_columns_validator(field_name, required_cols=['Agent', 'Capacity'])],
        'help_text': 'Agent capacity table. Capacity is maximum number of tasks assignable to each agent.',
    }


def table_tasks(field_name):
    # Generic use: work items or targets that need one-to-one assignment.
    # Example use: jobs, tickets, inspection points, deployment tasks.
    return {
        'initial': pd.DataFrame({'Task': ['T1', 'T2', 'T3']}),
        'validators': [table_columns_validator(field_name, required_cols=['Task'])],
        'help_text': 'Task list. Each task requires exactly one assignment in the standard assignment model.',
    }


def table_assign_cost(field_name):
    # Generic use: assignment cost matrix from each resource to each work item.
    # Example use: labor cost, completion time, risk score, travel burden.
    return {
        'initial': pd.DataFrame({
            'Agent': ['A1', 'A1', 'A1', 'A2', 'A2', 'A2', 'A3', 'A3', 'A3'],
            'Task': ['T1', 'T2', 'T3', 'T1', 'T2', 'T3', 'T1', 'T2', 'T3'],
            'Cost': [14, 5, 8, 2, 12, 6, 7, 8, 3],
        }),
        'validators': [table_columns_validator(field_name, required_cols=['Agent', 'Task', 'Cost'])],
        'help_text': 'Assignment cost per Agent-Task pair. Cost is compared across feasible assignment combinations.',
    }


def table_items(field_name):
    # Generic use: candidate options with value, weight, and optional quantity cap.
    # Example use: product mix, project portfolio, feature selection, cargo loading.
    return {
        'initial': pd.DataFrame({
            'Item': ['I1', 'I2', 'I3', 'I4'],
            'Value': [12, 10, 20, 15],
            'Weight': [2, 1, 3, 2],
            'Max Qty': [1, 1, 1, 1],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Item', 'Value', 'Weight'],
                optional_cols=['Max Qty'],
            )
        ],
        'help_text': 'Item table with Value and Weight per unit item. Weight is resource consumption per unit and must match capacity_limit units.',
    }


def table_material_demand(field_name):
    # Generic use: per-item demand requirement that procurement must satisfy.
    # Example use: raw material plans, SKU replenishment, component needs.
    return {
        'initial': pd.DataFrame({
            'Item': ['I1', 'I2', 'I3'],
            'Demand': [100, 80, 60],
        }),
        'validators': [table_columns_validator(field_name, required_cols=['Item', 'Demand'])],
        'help_text': 'Item demand quantities. Demand units should match supplier capacities and supplier-item Max Qty units.',
    }


def table_supplier_master(field_name):
    # Generic use: provider attributes including capacity and fixed activation cost.
    # Example use: supplier onboarding cost, contractor retainers, service tiers.
    return {
        'initial': pd.DataFrame({
            'Supplier': ['S1', 'S2', 'S3'],
            'Capacity': [180, 160, 140],
            'Fixed Cost': [500, 650, 450],
            'Min Order': [0, 0, 0],
            'Risk': [4, 7, 3],
            'Quality': [82, 75, 88],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Supplier', 'Capacity', 'Fixed Cost'],
                optional_cols=['Min Order', 'Risk', 'Quality'],
            )
        ],
        'help_text': (
            "Supplier attributes table. Capacity uses the same quantity units as item demand. "
            "Fixed Cost is per selected supplier. Optional Risk/Quality values use user-defined scales; "
            "set min/max thresholds using the same scales."
        ),
    }


def table_supplier_item_cost(field_name):
    # Generic use: provider-item variable cost table with optional pairwise max limit.
    # Example use: contract pricing grids, lane rates, source-specific unit costs.
    return {
        'initial': pd.DataFrame({
            'Supplier': ['S1', 'S1', 'S1', 'S2', 'S2', 'S2', 'S3', 'S3', 'S3'],
            'Item': ['I1', 'I2', 'I3', 'I1', 'I2', 'I3', 'I1', 'I2', 'I3'],
            'Unit Cost': [11, 13, 12, 10, 14, 13, 12, 12, 11],
            'Max Qty': [100, 80, 60, 100, 80, 60, 100, 80, 60],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Supplier', 'Item', 'Unit Cost'],
                optional_cols=['Max Qty'],
            )
        ],
        'help_text': 'Supplier-item variable cost table. Unit Cost is cost per one quantity unit; Max Qty uses the same quantity basis as demand.',
    }


def table_capacity_object(field_name):
    # Generic use: capacity planning table balancing available and required quantities.
    # Example use: production lines, staffing blocks, cloud quota envelopes.
    return {
        'initial': pd.DataFrame({
            'Resource': ['R1', 'R2', 'R3'],
            'Available': [120, 95, 80],
            'Required': [70, 60, 50],
            'Unit Cost': [5, 6, 7],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Resource', 'Available', 'Required', 'Unit Cost'],
            )
        ],
        'help_text': 'Resource table. Available and Required must use the same quantity units. Unit Cost is per one quantity unit.',
    }


def table_routing_object(field_name):
    # Generic use: route graph edges with movement cost and optional capacity.
    # Example use: logistics lanes, network links, workflow transfer paths.
    return {
        'initial': pd.DataFrame({
            'From': ['N1', 'N1', 'N2', 'N2', 'N3'],
            'To': ['N2', 'N3', 'N3', 'N4', 'N4'],
            'Cost': [4, 7, 3, 6, 2],
            'Capacity': [100, 80, 90, 70, 110],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['From', 'To', 'Cost', 'Capacity'],
            )
        ],
        'help_text': 'Route edge table. Capacity must use the same units as demand_qty. Cost is per one unit of routed flow.',
    }


def table_placement_object(field_name):
    # Generic use: entity-to-location placement scoring/cost matrix.
    # Example use: VM-to-host assignment, SKU-to-bin slotting, team-to-site placement.
    return {
        'initial': pd.DataFrame({
            'Entity': ['E1', 'E1', 'E2', 'E2', 'E3', 'E3'],
            'Location': ['L1', 'L2', 'L1', 'L2', 'L1', 'L2'],
            'Score': [9, 7, 8, 6, 7, 9],
            'Cost': [5, 4, 6, 3, 4, 5],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Entity', 'Location', 'Score', 'Cost'],
            )
        ],
        'help_text': 'Table of entity-location options with score and cost.',
    }


def table_redundancy_object(field_name):
    # Generic use: primary/backup pairing inputs with resilience and cost factors.
    # Example use: failover design, supplier backup plans, spare-capacity strategy.
    return {
        'initial': pd.DataFrame({
            'Primary': ['P1', 'P2', 'P3'],
            'Backup': ['B1', 'B2', 'B3'],
            'Coverage %': [99.0, 97.5, 98.8],
            'Extra Cost': [12, 9, 11],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Primary', 'Backup', 'Coverage %', 'Extra Cost'],
            )
        ],
        'help_text': 'Primary-backup options with Coverage % and Extra Cost. Coverage % uses percent scale (0-100).',
    }


def table_projects(field_name):
    # Generic use: project candidate table with value, cost, and optional resource usage.
    # Example use: capex pipeline, feature roadmap, portfolio intake decisions.
    return {
        'initial': pd.DataFrame({
            'Project': ['P1', 'P2', 'P3', 'P4', 'P5'],
            'Value': [180, 130, 170, 115, 90],
            'Cost': [95, 75, 100, 55, 45],
            'Resource': [5, 4, 6, 3, 2],
            'Must Do': [0, 0, 0, 0, 0],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Project', 'Value', 'Cost'],
                optional_cols=['Resource', 'Must Do'],
            )
        ],
        'help_text': 'Project table with Project, Value, Cost and optional Resource, Must Do columns.',
    }


def table_project_rules(field_name):
    # Generic use: relation rules between project pairs.
    # Type supports 'depends_on' and 'excludes'.
    return {
        'initial': pd.DataFrame({
            'From': ['P3', 'P2'],
            'To': ['P1', 'P4'],
            'Type': ['depends_on', 'excludes'],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['From', 'To', 'Type'],
            )
        ],
        'help_text': "Optional relation rules: Type in {'depends_on', 'excludes'}.",
    }


def table_workforce_staff(field_name):
    # Generic use: available workers with assignment limits and per-shift cost.
    # Optional Skills uses comma-separated tags for skill-constrained shifts.
    return {
        'initial': pd.DataFrame({
            'Worker': ['W1', 'W2', 'W3', 'W4'],
            'Max Shifts': [3, 2, 2, 1],
            'Cost per Shift': [100, 90, 95, 110],
            'Skills': ['packing,forklift', 'packing', 'quality', 'forklift,quality'],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Worker', 'Max Shifts', 'Cost per Shift'],
                optional_cols=['Skills'],
            )
        ],
        'help_text': 'Worker table with max shifts, cost per shift, and optional comma-separated skills.',
    }


def table_workforce_shift_demand(field_name):
    # Generic use: required staffing per shift with optional required skill.
    return {
        'initial': pd.DataFrame({
            'Shift': ['Day-1', 'Day-2', 'Night-1'],
            'Required': [2, 2, 1],
            'Required Skill': ['packing', '', 'quality'],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Shift', 'Required'],
                optional_cols=['Required Skill'],
            )
        ],
        'help_text': "Shift demand table with required headcount/assignments and optional 'Required Skill'. Required should generally be integer-valued.",
    }


def table_prodinv_item_master(field_name):
    # Generic use: item-level inventory economics.
    return {
        'initial': pd.DataFrame({
            'Item': ['A', 'B'],
            'Initial Inventory': [20, 10],
            'Holding Cost': [1.5, 1.0],
            'Backlog Penalty': [12, 10],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Item', 'Initial Inventory', 'Holding Cost', 'Backlog Penalty'],
            )
        ],
        'help_text': 'Item economics table. Initial Inventory uses the same quantity units as Demand and Max Production. Holding Cost and Backlog Penalty are per one quantity unit.',
    }


def table_prodinv_demand(field_name):
    # Generic use: period demand by item.
    return {
        'initial': pd.DataFrame({
            'Period': ['1', '1', '2', '2', '3', '3'],
            'Item': ['A', 'B', 'A', 'B', 'A', 'B'],
            'Demand': [50, 45, 55, 40, 60, 50],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Period', 'Item', 'Demand'],
            )
        ],
        'help_text': 'Period-wise demand by item. Demand units should match Initial Inventory and Max Production units.',
    }


def table_prodinv_production(field_name):
    # Generic use: period production economics and capacity by item.
    return {
        'initial': pd.DataFrame({
            'Period': ['1', '1', '2', '2', '3', '3'],
            'Item': ['A', 'B', 'A', 'B', 'A', 'B'],
            'Unit Cost': [7.0, 6.5, 7.2, 6.6, 7.4, 6.8],
            'Max Production': [65, 55, 65, 55, 70, 60],
            'Setup Cost': [20, 15, 20, 15, 20, 15],
        }),
        'validators': [
            table_columns_validator(
                field_name,
                required_cols=['Period', 'Item', 'Unit Cost', 'Max Production'],
                optional_cols=['Setup Cost'],
            )
        ],
        'help_text': 'Period-item production table. Max Production uses same quantity units as demand/inventory; Unit Cost is per one quantity unit.',
    }




