# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qutil import is_debug


OPTIMIZATION_STATUS_DESCRIPTIONS = {
    "Optimal": "A finite optimal solution was found!",
    "Not Solved": "The optimization problem has not been solved.",
    "Infeasible": "No solution satisfies all the specified constraints.",
    "Unbounded": "The objective can improve indefinitely; no finite optimal solution exists.",
    "Undefined": "The solver could not determine a valid solution status.",
}


def safe_objective_value(prob):
    value = prob.objective.value()
    return round(float(value), 6) if value is not None else None


def solver():
    return pulp.PULP_CBC_CMD(msg=is_debug())


def optimization_status_description(status_name, fallback="Unknown optimization status."):
    return OPTIMIZATION_STATUS_DESCRIPTIONS.get(status_name, fallback)


def slack_table(prob):
    rows = []
    for name, cons in prob.constraints.items():
        rows.append({'Constraint': name, 'Slack': round(float(cons.slack), 6)})
    return pd.DataFrame(rows)



