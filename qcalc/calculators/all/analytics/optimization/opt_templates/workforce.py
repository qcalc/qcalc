# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qutil import require_columns, require_unique_values

from ..opt_core import safe_objective_value, solver, slack_table


def _skills_set(value):
    if value in ('', None):
        return set()
    return {token.strip().lower() for token in str(value).split(',') if token.strip()}


def solve_workforce_scheduling(
    workforce_staff,
    workforce_shift_demand,
    allow_shortage,
    shortage_penalty,
    show_zero,
):
    require_columns(
        workforce_staff,
        'workforce_staff',
        ['Worker', 'Max Shifts', 'Cost per Shift'],
        optional_cols=['Skills'],
    )
    require_columns(
        workforce_shift_demand,
        'workforce_shift_demand',
        ['Shift', 'Required'],
        optional_cols=['Required Skill'],
    )

    staff_df = workforce_staff.copy()
    demand_df = workforce_shift_demand.copy()

    if staff_df.empty:
        raise Exception('workforce_staff must contain at least one row')
    if demand_df.empty:
        raise Exception('workforce_shift_demand must contain at least one row')

    staff_df['Worker'] = staff_df['Worker'].astype(str).str.strip()
    demand_df['Shift'] = demand_df['Shift'].astype(str).str.strip()

    workers = require_unique_values(staff_df, 'workforce_staff', 'Worker')
    shifts = require_unique_values(demand_df, 'workforce_shift_demand', 'Shift')

    max_shifts = dict(zip(staff_df['Worker'], pd.to_numeric(staff_df['Max Shifts'])))
    cost_per_shift = dict(zip(staff_df['Worker'], pd.to_numeric(staff_df['Cost per Shift'])))
    required = dict(zip(demand_df['Shift'], pd.to_numeric(demand_df['Required'])))

    for worker in workers:
        if float(max_shifts[worker]) < 0:
            raise Exception(f'Max Shifts must be non-negative for worker: {worker}')
        if float(cost_per_shift[worker]) < 0:
            raise Exception(f'Cost per Shift must be non-negative for worker: {worker}')

    for shift in shifts:
        if float(required[shift]) < 0:
            raise Exception(f'Required must be non-negative for shift: {shift}')

    worker_skills = {worker: set() for worker in workers}
    if 'Skills' in staff_df.columns:
        worker_skills = {
            str(row['Worker']).strip(): _skills_set(row['Skills'])
            for _, row in staff_df.iterrows()
        }

    shift_required_skill = {shift: '' for shift in shifts}
    if 'Required Skill' in demand_df.columns:
        shift_required_skill = {
            str(row['Shift']).strip(): str(row['Required Skill']).strip().lower()
            for _, row in demand_df.iterrows()
        }

    feasible_pairs = []
    for worker in workers:
        for shift in shifts:
            req_skill = shift_required_skill.get(shift, '')
            if req_skill and req_skill not in worker_skills.get(worker, set()):
                continue
            feasible_pairs.append((worker, shift))

    if not feasible_pairs:
        raise Exception('No feasible worker-shift assignments found. Check required skills and staff skill tags.')

    allow_short = bool(allow_shortage)
    penalty = float(shortage_penalty)
    if penalty < 0:
        raise Exception('shortage_penalty must be non-negative')

    prob = pulp.LpProblem('optima_workforce_scheduling', pulp.LpMinimize)
    x = pulp.LpVariable.dicts('Assign', feasible_pairs, lowBound=0, upBound=1, cat=pulp.LpBinary)

    shortage = {}
    if allow_short:
        shortage = pulp.LpVariable.dicts('Short', shifts, lowBound=0, cat=pulp.LpContinuous)

    labor_cost_expr = pulp.lpSum(float(cost_per_shift[w]) * x[(w, s)] for (w, s) in feasible_pairs)
    shortage_cost_expr = pulp.lpSum(penalty * shortage[s] for s in shifts) if allow_short else 0.0
    prob += labor_cost_expr + shortage_cost_expr

    for worker in workers:
        w_pairs = [(w, s) for (w, s) in feasible_pairs if w == worker]
        prob += pulp.lpSum(x[p] for p in w_pairs) <= float(max_shifts[worker]), f'max_shifts_{worker}'

    for shift in shifts:
        s_pairs = [(w, s) for (w, s) in feasible_pairs if s == shift]
        if allow_short:
            prob += (
                pulp.lpSum(x[p] for p in s_pairs) + shortage[shift] == float(required[shift]),
                f'coverage_{shift}'
            )
        else:
            prob += (
                pulp.lpSum(x[p] for p in s_pairs) == float(required[shift]),
                f'coverage_{shift}'
            )

    prob.solve(solver())
    status = pulp.LpStatus[prob.status]

    assign_rows = []
    total_assignments = 0.0
    for worker, shift in feasible_pairs:
        val = float(x[(worker, shift)].value() or 0.0)
        total_assignments += val
        if show_zero or val > 0:
            assign_rows.append({
                'Worker': worker,
                'Shift': shift,
                'Assigned': round(val, 6),
                'Cost per Shift': round(float(cost_per_shift[worker]), 6),
                'Line Cost': round(float(cost_per_shift[worker]) * val, 6),
            })

    coverage_rows = []
    total_required = 0.0
    total_shortage = 0.0
    for shift in shifts:
        assigned = sum(float(x[(w, s)].value() or 0.0) for (w, s) in feasible_pairs if s == shift)
        req = float(required[shift])
        short = float(shortage[shift].value() or 0.0) if allow_short else 0.0
        total_required += req
        total_shortage += short
        coverage_rows.append({
            'Shift': shift,
            'Required': round(req, 6),
            'Assigned': round(assigned, 6),
            'Shortage': round(short, 6),
            'Coverage %': round((assigned / req * 100.0) if req else 100.0, 4),
            'Required Skill': shift_required_skill.get(shift, ''),
        })

    utilization_rows = []
    for worker in workers:
        assigned = sum(float(x[(w, s)].value() or 0.0) for (w, s) in feasible_pairs if w == worker)
        limit = float(max_shifts[worker])
        utilization_rows.append({
            'Worker': worker,
            'Max Shifts': round(limit, 6),
            'Assigned Shifts': round(assigned, 6),
            'Utilization %': round((assigned / limit * 100.0) if limit else 0.0, 4),
            'Skills': ', '.join(sorted(worker_skills.get(worker, set()))),
        })

    total_labor_cost = sum(float(cost_per_shift[w]) * float(x[(w, s)].value() or 0.0) for (w, s) in feasible_pairs)
    total_shortage_cost = penalty * total_shortage if allow_short else 0.0

    return {
        'Summary': pd.DataFrame([{
            'Model': 'Workforce Shift Scheduling',
            'Status': status,
            'Objective': safe_objective_value(prob),
            'Workers': len(workers),
            'Shifts': len(shifts),
            'Total Required': round(total_required, 6),
            'Total Assigned': round(total_assignments, 6),
            'Total Shortage': round(total_shortage, 6),
            'Labor Cost': round(total_labor_cost, 6),
            'Shortage Cost': round(total_shortage_cost, 6),
        }]),
        'Decision Table': pd.DataFrame(assign_rows),
        'Coverage Table': pd.DataFrame(coverage_rows),
        'Worker Utilization': pd.DataFrame(utilization_rows),
        'Constraint Slack': slack_table(prob),
    }
