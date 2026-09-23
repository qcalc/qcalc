# Nonlinear Programming

## Purpose

This calculator solves a nonlinear optimization problem by letting you choose an objective, define decision variables, and add nonlinear constraints.

It is useful when the best answer is not found by simple trial and error. Typical uses include designing a tank, sizing equipment, tuning a process, or maximizing profit when demand, cost, or capacity changes with the decision itself.

## Background

### Nonlinear optimization

In a nonlinear model, the objective or the constraints are not just straight-line relationships. Terms like `r*h`, `r**2`, `sin(x)`, `exp(x)`, `log(y)`, `min(...)`, and `max(...)` are all allowed here.

That makes this calculator more flexible than a linear program, but also more numerical. It searches for a feasible solution with the best objective value, rather than solving a symbolic formula.

## Inputs

### Objective

Choose whether the calculator should `Minimize` or `Maximize` the objective function.

Use `Minimize` when lower values are better, such as material use, cost, loss, or error. Use `Maximize` when higher values are better, such as profit, output, or score.

### Decision Variables

Enter one variable definition per line.

You can use a bare name such as `x`, which defaults to `x >= 0`, or you can add a single bound such as `x >= 0` or `y <= 10`. If you repeat a variable name, the later bound replaces the earlier one.

The variable names you enter here are also the names that appear in the result.

### Objective Function

Enter the expression to minimize or maximize.

The expression can be nonlinear and can use standard math-style functions and constants such as `pi`, `e`, `sin`, `cos`, `exp`, `log`, `sqrt`, `min`, and `max`. Keep the units consistent with your own model, because the calculator does not assign units automatically.

### Constraints

Enter one constraint per line.

Use `<=`, `>=`, or `=`. The right-hand side must be a plain number, so if the limit depends on a variable, move the full expression to the left. For example, write `x + 4*p <= 260` rather than `x <= 260 - 4*p`.

### Initial Guess

Optional starting point for the solver, entered as comma-separated values in the same order as the decision variables.

If you leave it blank, the calculator derives a reasonable starting point from the variable bounds.

## Results

### Status

Shows whether the solver found a feasible optimum.

`Optimal` means the solver found a best feasible solution for the model it was given. Other values such as `Infeasible`, `Unbounded`, or `Not Solved` mean you should treat the answer as a failed or incomplete solve rather than a recommendation.

### Status Description

Plain-language explanation of the solver status.

This is useful when the status is not `Optimal`, because it gives the most direct summary of what went wrong.

### Objective

The final value of the objective function.

For `Minimize`, smaller is better. For `Maximize`, larger is better. The unit is whatever unit your expression represents, such as area, cost, or profit.

### Decision Variable Results

The calculator returns the optimized value of each decision variable using the names you entered.

Read these values together with the objective. They tell you what setting the solver chose, not just how good the final value was.

### chart

When there is exactly one decision variable, the calculator returns a line chart of objective value versus that variable with the optimum marked.

When there are exactly two decision variables, it returns a 3D surface-contour chart with the optimum marked.

## Understanding the Calculation

The solver evaluates your objective and constraints numerically.

For a minimization problem, it searches for the feasible point with the smallest objective value. For a maximization problem, it solves the equivalent numerical search in the opposite direction and then reports the best objective value back in the original sign convention.

Constraint handling is direct: each line you enter becomes a feasibility condition that must be satisfied. Bounds on decision variables are taken from the variable definitions, and the starting point is taken from `Initial Guess` when you provide one, otherwise from the bounds.

Because this is a numerical optimizer, the result is approximate. On curved or multi-peaked problems, the answer can depend on the starting point, and a local optimum may be found instead of a global one.

## Example

### Default cylinder example

The default problem minimizes the cylinder surface-area expression `2*pi*r*h + 2*pi*r**2` subject to the fixed-volume constraint `pi*r**2*h = 1000`, with `r >= 0` and `h >= 0`.

Using the default values, the solver returns `Status = Optimal`, `Objective ≈ 553.58`, `r ≈ 5.42`, and `h ≈ 10.84`.

Interpretation: this is the cylinder shape with the least surface area for volume 1000. If your material cost is proportional to surface area, the same result is also the least-material-cost design.

### Profit maximization with demand, production capacity, and a price cap

Suppose a business wants to maximize profit where each unit sells for `p` and costs `20 USD` to produce. Demand falls as price rises, so the sales ceiling is `x + 4*p <= 260`. Production is also limited to `x <= 100`, and management will not allow a price above `35`.

One way to model that is:

- Objective: maximize `(p - 20) * x`
- Decision variables: `p >= 0`, `x >= 0`
- Constraints: `x + 4*p <= 260`, `x <= 100`, `p <= 35`

With those values, the solver returns `Status = Optimal`, `Objective ≈ 1500`, `p ≈ 35`, and `x ≈ 100`.

Interpretation: the business charges the highest allowed price and produces at full capacity. At that price, the demand ceiling is still above capacity, so the production cap is the active limit on sales.

## Important Assumptions and Interpretation

- The calculator is a numerical solver, not a symbolic algebra system.
- Results are approximate and may shift slightly with a different starting guess or tighter model bounds.
- The solver does not guarantee a global optimum for every nonlinear problem.
- Units are not enforced automatically, so all quantities, prices, costs, and rates must be kept consistent by the user.
- If the status is not `Optimal`, the reported values should be treated carefully because they are not a confirmed best solution.