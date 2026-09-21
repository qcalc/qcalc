# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import itertools
import numpy as np
import sympy as sp
from matplotlib.figure import Figure

from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)


transformations = standard_transformations + (
    implicit_multiplication_application,
)


def feasible_region(
    objective: str,
    constraints: list[str],
    solution: dict[str, float] | list[float] | tuple[float, float] | None = None,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    fig=None,
    ax=None,
):
    """
    Plot the feasible region of a two-variable linear programming problem.

    objective:
        Objective function, e.g. "2x+3y"

    constraints:
        List of constraints, e.g.
        ["x+y>=90", "2x+y<=150", "x>=0", "y>=0"]

    solution:
        Optional optimal solution, e.g.
        {"x": 30, "y": 60}

    xlim, ylim:
        Optional plot limits.

    fig, ax:
        Optional matplotlib figure and axis to draw on.
    """

    # ---------------------------------------------------------
    # Find the two decision variables
    # ---------------------------------------------------------

    expressions = [objective] + constraints
    symbols = set()

    for expression in expressions:
        # Remove comparison operators before parsing
        expression = (
            expression
            .replace(">=", " ")
            .replace("<=", " ")
            .replace(">", " ")
            .replace("<", " ")
            .replace("=", " ")
        )

        parsed = parse_expr(
            expression,
            transformations=transformations,
        )

        symbols.update(parsed.free_symbols)

    variables = sorted(symbols, key=str)

    if len(variables) != 2:
        raise ValueError(
            "Feasible-region chart requires exactly two decision variables."
        )

    x_var, y_var = variables

    # ---------------------------------------------------------
    # Parse objective
    # ---------------------------------------------------------

    obj = parse_expr(
        objective,
        transformations=transformations,
        local_dict={
            str(x_var): x_var,
            str(y_var): y_var,
        },
    )

    objective_coefficients = (
        float(obj.coeff(x_var)),
        float(obj.coeff(y_var)),
    )

    # ---------------------------------------------------------
    # Parse constraints
    # ---------------------------------------------------------

    chart_constraints = []

    for constraint in constraints:

        if ">=" in constraint:
            operator = ">="
        elif "<=" in constraint:
            operator = "<="
        elif ">" in constraint:
            operator = ">"
        elif "<" in constraint:
            operator = "<"
        elif "=" in constraint:
            operator = "="
        else:
            raise ValueError(
                f"Invalid constraint: '{constraint}'"
            )

        lhs, rhs = constraint.split(operator, 1)

        lhs = parse_expr(
            lhs,
            transformations=transformations,
            local_dict={
                str(x_var): x_var,
                str(y_var): y_var,
            },
        )

        rhs = parse_expr(
            rhs,
            transformations=transformations,
            local_dict={
                str(x_var): x_var,
                str(y_var): y_var,
            },
        )

        # Move everything to:
        #
        #     a*x + b*y <= c
        #
        # or equivalent >= / = form.
        expression = sp.expand(lhs - rhs)

        a = float(expression.coeff(x_var))
        b = float(expression.coeff(y_var))

        constant = float(
            expression.subs({
                x_var: 0,
                y_var: 0,
            })
        )

        c = -constant

        chart_constraints.append(
            (a, b, operator, c)
        )

    # ---------------------------------------------------------
    # Add non-negativity constraints
    # ---------------------------------------------------------

    if not any(
        a == 1 and b == 0 and operator == ">=" and c == 0
        for a, b, operator, c in chart_constraints
    ):
        chart_constraints.append((1, 0, ">=", 0))

    if not any(
        a == 0 and b == 1 and operator == ">=" and c == 0
        for a, b, operator, c in chart_constraints
    ):
        chart_constraints.append((0, 1, ">=", 0))

    # ---------------------------------------------------------
    # Convert constraints to <= form for finding feasible points
    # ---------------------------------------------------------

    inequalities = []

    for a, b, operator, c in chart_constraints:

        if operator in ("<=", "<"):
            inequalities.append((a, b, c))

        elif operator in (">=", ">"):
            inequalities.append((-a, -b, -c))

        elif operator == "=":
            inequalities.append((a, b, c))
            inequalities.append((-a, -b, -c))

    # ---------------------------------------------------------
    # Find all intersections of constraint lines
    # ---------------------------------------------------------

    points = []

    for c1, c2 in itertools.combinations(inequalities, 2):

        a1, b1, d1 = c1
        a2, b2, d2 = c2

        determinant = a1 * b2 - a2 * b1

        if abs(determinant) < 1e-10:
            continue

        x = (d1 * b2 - d2 * b1) / determinant
        y = (a1 * d2 - a2 * d1) / determinant

        if all(
            a * x + b * y <= c + 1e-9
            for a, b, c in inequalities
        ):
            points.append((x, y))

    if not points:
        raise ValueError("No feasible region exists.")

    # Remove duplicate points
    points = list({
        (round(x, 10), round(y, 10))
        for x, y in points
    })

    points = np.array(points)

    # ---------------------------------------------------------
    # Sort points around centroid
    # ---------------------------------------------------------

    center = points.mean(axis=0)

    angles = np.arctan2(
        points[:, 1] - center[1],
        points[:, 0] - center[0],
    )

    points = points[np.argsort(angles)]

    # ---------------------------------------------------------
    # Plot
    # ---------------------------------------------------------

    if fig is None or ax is None:
        fig = Figure()
        ax = fig.subplots()

    # Feasible region
    ax.fill(
        points[:, 0],
        points[:, 1],
        alpha=0.25,
        label="Feasible Region",
    )

    # ---------------------------------------------------------
    # Determine plot limits
    # ---------------------------------------------------------

    if xlim is None:
        xmax = max(points[:, 0]) * 1.2
        xmax = max(xmax, 1)
        xlim = (0, xmax)

    if ylim is None:
        ymax = max(points[:, 1]) * 1.2
        ymax = max(ymax, 1)
        ylim = (0, ymax)

    x = np.linspace(xlim[0], xlim[1], 500)

    # ---------------------------------------------------------
    # Constraint lines
    # ---------------------------------------------------------

    for a, b, operator, c in chart_constraints:

        if abs(b) > 1e-10:
            y = (c - a * x) / b

            ax.plot(
                x,
                y,
                label=f"{a:g}x + {b:g}y {operator} {c:g}",
            )

        elif abs(a) > 1e-10:
            # Vertical constraint: x = c/a
            x_value = c / a

            ax.axvline(
                x_value,
                label=f"x {operator} {x_value:g}",
            )

    # ---------------------------------------------------------
    # Optimal solution
    # ---------------------------------------------------------

    if solution is not None:

        if isinstance(solution, dict):
            x_opt = float(solution[str(x_var)])
            y_opt = float(solution[str(y_var)])
        elif isinstance(solution, (list, tuple)) and len(solution) == 2:
            x_opt = float(solution[0])
            y_opt = float(solution[1])
        else:
            raise ValueError('Solution must be a dict {var: value} or a 2-item sequence')

        ax.scatter(
            x_opt,
            y_opt,
            s=80,
            zorder=5,
            label="Optimal Solution",
        )

        ax.annotate(
            f"({x_opt:g}, {y_opt:g})",
            (x_opt, y_opt),
            xytext=(8, 8),
            textcoords="offset points",
        )

    # ---------------------------------------------------------
    # Objective function through optimal solution
    # ---------------------------------------------------------

    oa, ob = objective_coefficients

    if solution is not None:

        x0 = x_opt
        y0 = y_opt

        objective_value = oa * x0 + ob * y0

        if abs(ob) > 1e-10:

            y_obj = (
                objective_value - oa * x
            ) / ob

            ax.plot(
                x,
                y_obj,
                linestyle="--",
                label=f"Objective = {objective_value:g}",
            )

        elif abs(oa) > 1e-10:

            x_obj = objective_value / oa

            ax.axvline(
                x_obj,
                linestyle="--",
                label=f"Objective = {objective_value:g}",
            )

    # ---------------------------------------------------------
    # Labels and formatting
    # ---------------------------------------------------------

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    ax.set_xlabel(str(x_var))
    ax.set_ylabel(str(y_var))

    ax.set_title("Linear Programming Feasible Region")

    ax.grid(True, alpha=0.3)
    ax.legend()

    return fig, ax