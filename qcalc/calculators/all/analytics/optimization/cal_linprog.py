import pulp
import re

from qcore import qlist, qtext
from calculators.all.general.chart import feasible_chart


def linprog__info():
    return {
        "title": "Linear Programming",
        'desc': (
            'Solve a linear programming problem by selecting an objective, '
            'defining decision variables, and applying linear constraints.'
        ),
        'schema': {
            'objective': {
                'type': 'choice', 'choices': ['Maximize', 'Minimize'],
            }
        }
    }


def linprog(
    objective='Minimize',
    decision_variables: qlist[str] = ['x >= 0', 'y >= 0'],
    objective_function: qtext = '3*x + 5*y',
    constraints: qlist[str] = ['2 * x + 3 * y >= 12',
                               '-x + y <= 3',
                               'x >= 4',
                               'y <= 3'],
):
    """
    Solve a linear programming optimization problem.

    `decision_variables`:
        Decision variable definitions, e.g.:
        x >= 0
        y >= 0

    `objective_function`:
        Objective expression, e.g.:
        3*x + 5*y

    `constraints`:
        Constraints, e.g.:
        2*x + 3*y <= 12
        -x + y <= 3
    """

    # Create model
    sense = pulp.LpMaximize if objective == "Maximize" else pulp.LpMinimize
    model = pulp.LpProblem("Linear_Programming", sense)

    # Keep chart constraints in the user's original form.
    # chart_constraints = list(constraints)

    # Create decision variables
    variables = {}

    for definition in decision_variables:
        definition = definition.replace(" ", "")

        if ">=" in definition:
            name, bound = definition.split(">=", 1)
            # chart_constraints.append(f"{name}>={bound}")
            variables[name] = pulp.LpVariable(
                name, lowBound=float(bound), cat="Continuous"
            )
        elif "<=" in definition:
            name, bound = definition.split("<=", 1)
            # chart_constraints.append(f"{name}<={bound}")
            variables[name] = pulp.LpVariable(
                name, upBound=float(bound), cat="Continuous"
            )
        else:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", definition):
                raise ValueError(
                    f"Invalid decision variable definition: '{definition}'. "
                    "Must be either a variable name or a variable with >= or <= 0."
                )

            variables[definition] = pulp.LpVariable(
                definition, lowBound=0, cat="Continuous"
            )
    # Build expressions using the variables
    namespace = variables

    objective = eval(objective_function, {"__builtins__": {}}, namespace)

    # Maximize
    model += objective

    # Add constraints
    for constraint in constraints:
        constraint = constraint.replace(" ", "")

        if "<=" in constraint:
            lhs, rhs = constraint.split("<=", 1)
            model += (
                eval(lhs, {"__builtins__": {}}, namespace)
                <= float(rhs)
            )

        elif ">=" in constraint:
            lhs, rhs = constraint.split(">=", 1)
            model += (
                eval(lhs, {"__builtins__": {}}, namespace)
                >= float(rhs)
            )

        elif "=" in constraint:
            lhs, rhs = constraint.split("=", 1)
            model += (
                eval(lhs, {"__builtins__": {}}, namespace)
                == float(rhs)
            )

    # Solve
    status = model.solve()

    status_name = pulp.LpStatus[status]

    status_descriptions = {
        "Optimal": "A finite optimal solution was found!",
        "Not Solved": "The optimization problem has not been solved.",
        "Infeasible": "No solution satisfies all the specified constraints.",
        "Unbounded": "The objective can improve indefinitely; no finite optimal solution exists.",
        "Undefined": "The solver could not determine a valid solution status.",
    }

    status_description = status_descriptions.get(
        status_name,
        "Unknown optimization status.",
    )

    # Results
    result = {
        "Status": status_name,
        "Status Description": status_description,
        "Objective": pulp.value(model.objective),
        **{
            name: pulp.value(variable)
            for name, variable in variables.items()
        },
    }

    # Add feasible-region chart for 2-variable optimal problems.
    if status_name == 'Optimal' and len(variables) == 2:
        var_names = sorted(variables.keys())
        result.update(feasible_chart(
            objective=objective_function,
            constraints=constraints,
            solution=[result[var_names[0]], result[var_names[1]]],
        ))

    return result
