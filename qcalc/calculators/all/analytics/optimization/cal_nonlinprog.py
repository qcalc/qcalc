import math
import re

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from qcore import qlist, qtext, QChart
from calculators.all.general.chart import surface_contour3d_chart
from calc import optimization_status_description
from qutil import preprocess_expression


_NONLINEAR_EVAL_GLOBALS = {
    "__builtins__": {},
    "np": np,
    "math": math,
    "pi": math.pi,
    "e": math.e,
    "abs": abs,
    "min": min,
    "max": max,
    "pow": pow,
}
for _name in (
    "sin", "cos", "tan", "asin", "acos", "atan",
    "sinh", "cosh", "tanh",
    "exp", "log", "log10", "log2", "sqrt",
    "floor", "ceil", "fabs",
):
    _NONLINEAR_EVAL_GLOBALS[_name] = getattr(np, _name, getattr(math, _name))


def _parse_decision_variable_definitions(decision_variables):
    variable_specs = {}
    variable_order = []

    for definition in decision_variables:
        definition = definition.replace(" ", "")

        if ">=" in definition:
            name, bound = definition.split(">=", 1)
            spec = (float(bound), None)
        elif "<=" in definition:
            name, bound = definition.split("<=", 1)
            spec = (None, float(bound))
        else:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", definition):
                raise ValueError(
                    f"Invalid decision variable definition: '{definition}'. "
                    "Must be either a variable name or a variable with >= or <= 0."
                )

            name = definition
            spec = (0.0, None)

        if name not in variable_specs:
            variable_order.append(name)
        variable_specs[name] = spec

    bounds = [variable_specs[name] for name in variable_order]
    return variable_order, bounds


def _build_variable_namespace(variable_names, values):
    return dict(zip(variable_names, values))


def _evaluate_expression(expression, variable_names, values):
    namespace = _build_variable_namespace(variable_names, values)
    return eval(
        preprocess_expression(expression),
        _NONLINEAR_EVAL_GLOBALS,
        namespace,
    )


def _coerce_initial_guess(initial_guess):
    if initial_guess is None:
        return None

    if isinstance(initial_guess, str):
        text = initial_guess.strip()
        if not text:
            return None
        parts = [part for part in re.split(r"[\s,]+", text) if part]
        return [float(part) for part in parts]

    return [float(value) for value in initial_guess]


def _initial_guess_from_bounds(bounds):
    guess = []

    for low_bound, up_bound in bounds:
        if low_bound is not None and up_bound is not None:
            value = (low_bound + up_bound) / 2.0
        elif low_bound is not None:
            value = low_bound if low_bound >= 0 else 0.0
            if up_bound is None and value == low_bound:
                value = low_bound + 1.0
        elif up_bound is not None:
            value = up_bound if up_bound <= 0 else 0.0
            if low_bound is None and value == up_bound:
                value = up_bound - 1.0
        else:
            value = 0.0

        if low_bound is not None:
            value = max(value, low_bound)
        if up_bound is not None:
            value = min(value, up_bound)

        guess.append(value)

    return guess


def _make_scipy_constraint(constraint_text, variable_names):
    constraint_text = constraint_text.replace(" ", "")

    if "<=" in constraint_text:
        lhs, rhs = constraint_text.split("<=", 1)

        def _constraint(values):
            return float(rhs) - _evaluate_expression(lhs, variable_names, values)

        return {"type": "ineq", "fun": _constraint}

    if ">=" in constraint_text:
        lhs, rhs = constraint_text.split(">=", 1)

        def _constraint(values):
            return _evaluate_expression(lhs, variable_names, values) - float(rhs)

        return {"type": "ineq", "fun": _constraint}

    if "=" in constraint_text:
        lhs, rhs = constraint_text.split("=", 1)

        def _constraint(values):
            return _evaluate_expression(lhs, variable_names, values) - float(rhs)

        return {"type": "eq", "fun": _constraint}

    raise ValueError(f"Invalid constraint: '{constraint_text}'.")


def nonlinprog__info():
    return {
        "title": "Optimization: Nonlinear Programming",
        'kins': 'linprog',
        'tags': 'optimization, non-linear programming',
        'desc': (
            'Solve a nonlinear optimization problem by selecting an objective, '
            'defining decision variables, and applying nonlinear constraints. '
        ),
        'schema': {
            'objective': {
                'type': 'choice', 'choices': ['Maximize', 'Minimize'],
                'help_text': 'Whether to maximize or minimize the objective_function.',
            },
            'decision_variables': {
                'help_text': (
                    'One variable per line: a bare name (e.g. x), or with a single '
                    'bound (e.g. x >= 0, y <= 10). A bare name defaults to x >= 0. '
                    'Only one bound per variable is kept if a name is listed twice.'
                ),
            },
            'objective_function': {
                'help_text': (
                    'Expression to maximize or minimize. Nonlinear terms are allowed, '
                    'for example (r - 5)**2 + (h - 10)**2, x*y + sin(x), or exp(x) - log(y).'
                ),
            },
            'constraints': {
                'help_text': (
                    'One constraint per line, e.g. pi*r**2*h = 1000 or sin(x) + y = 3. '
                    'Use <=, >=, or = with a numeric right side.'
                ),
            },
            'initial_guess': {
                'type': 'text',
                'help_text': (
                    'Optional starting point as comma-separated values in decision variable order. '
                    'If omitted, a reasonable guess is derived from the variable bounds.'
                ),
            },
        }
    }


def nonlinprog(
    objective='Minimize',
    decision_variables: qlist[str] = ['r >= 0', 'h >= 0'],
    objective_function: qtext = '2*pi*r*h + 2*pi*r**2',
    constraints: qlist[str] = ['pi*r**2*h = 1000'],
    initial_guess: qtext = '',
):
    """
    Solve a nonlinear programming optimization problem using SciPy.

    Real-life example: minimize the material needed for a cylindrical tank with
    fixed volume 1000, where `r` is the radius and `h` is the height.

    `decision_variables`:
        Decision variable definitions, e.g.:
        r >= 0
        h >= 0

    `objective_function`:
        Objective expression, e.g.:
        2*pi*r*h + 2*pi*r**2

    `constraints`:
        Constraints, e.g.:
        pi*r**2*h = 1000
        sin(x) + y <= 3
    """

    variable_names, bounds = _parse_decision_variable_definitions(decision_variables)

    x0 = _coerce_initial_guess(initial_guess)
    if x0 is None:
        x0 = _initial_guess_from_bounds(bounds)

    if len(x0) != len(variable_names):
        raise ValueError(
            f"Initial guess length {len(x0)} does not match number of decision variables {len(variable_names)}."
        )

    if objective == "Maximize":

        def _objective(values):
            return -float(_evaluate_expression(objective_function, variable_names, values))

    else:

        def _objective(values):
            return float(_evaluate_expression(objective_function, variable_names, values))

    scipy_constraints = [
        _make_scipy_constraint(constraint, variable_names)
        for constraint in constraints
    ]

    result = minimize(
        _objective,
        x0=x0,
        method='SLSQP',
        bounds=bounds,
        constraints=scipy_constraints,
    )

    if objective == "Maximize":
        objective_value = -result.fun if result.fun is not None else None
    else:
        objective_value = result.fun

    message = str(getattr(result, "message", "") or "")
    message_lower = message.lower()
    if result.success:
        status_name = "Optimal"
    elif "infeasible" in message_lower or "constraints are incompatible" in message_lower:
        status_name = "Infeasible"
    elif "unbounded" in message_lower:
        status_name = "Unbounded"
    else:
        status_name = "Not Solved"

    status_description = optimization_status_description(status_name, fallback=message or "Unknown optimization status.")

    solution_values = list(result.x) if getattr(result, "x", None) is not None else x0

    output = {
        "Status": status_name,
        "Status Description": status_description,
        "Objective": objective_value,
        **{
            name: value
            for name, value in zip(variable_names, solution_values)
        },
    }

    if status_name == "Optimal" and len(variable_names) == 1:
        x_center = solution_values[0]
        low_bound, up_bound = bounds[0]
        if low_bound is not None and up_bound is not None and low_bound != up_bound:
            x_vals = np.linspace(low_bound, up_bound, 100)
        else:
            span = max(abs(x_center), 1.0)
            x_min = low_bound if low_bound is not None else x_center - 2.0 * span
            x_max = up_bound if up_bound is not None else x_center + 2.0 * span
            if x_min == x_max:
                x_min -= span
                x_max += span
            x_vals = np.linspace(x_min, x_max, 100)

        y_vals = [
            float(_evaluate_expression(objective_function, variable_names, [x_val]))
            for x_val in x_vals
        ]

        chart = QChart()
        fig, ax = chart.create_figure()
        ax.plot(x_vals, y_vals)
        chart.set_labels(
            xlabel=variable_names[0],
            ylabel='Objective',
            title=f'Objective vs {variable_names[0]}',
            grid=True,
        )
        chart.mark([x_center, objective_value], label='Optimum', show_axis_guides=True)
        output['chart'] = chart

    if status_name == "Optimal" and len(variable_names) == 2:
        x_center, y_center = solution_values
        x_span = max(abs(x_center), 1.0)
        y_span = max(abs(y_center), 1.0)
        x_vals = np.linspace(max(0.0, x_center - 2.0 * x_span), x_center + 2.0 * x_span, 40)
        y_vals = np.linspace(max(0.0, y_center - 2.0 * y_span), y_center + 2.0 * y_span, 40)
        z_vals = [
            [
                float(_evaluate_expression(objective_function, variable_names, [x_val, y_val]))
                for x_val in x_vals
            ]
            for y_val in y_vals
        ]
        chart = surface_contour3d_chart(
            xvals=', '.join(str(value) for value in x_vals),
            yvals=', '.join(str(value) for value in y_vals),
            zvals2d=pd.DataFrame(z_vals),
            xlabel=variable_names[0],
            ylabel=variable_names[1],
            zlabel='Objective',
            title='Objective Surface with Contours',
        ).get('chart')

        if chart is not None:
            chart.mark([x_center, y_center, objective_value], show_axis_guides=False)
            output['chart'] = chart

    return output
