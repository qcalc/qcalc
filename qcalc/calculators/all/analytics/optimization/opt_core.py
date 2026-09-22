# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import pandas as pd
import pulp
from qutil import is_debug


def safe_objective_value(prob):
    value = prob.objective.value()
    return round(float(value), 6) if value is not None else None


def solver():
    return pulp.PULP_CBC_CMD(msg=is_debug())


def slack_table(prob):
    rows = []
    for name, cons in prob.constraints.items():
        rows.append({'Constraint': name, 'Slack': round(float(cons.slack), 6)})
    return pd.DataFrame(rows)



