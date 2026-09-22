# Optimization: Project Portfolio

## Purpose

This calculator selects projects to maximize total value under optional budget,
resource, count, mandatory-project, and project-rule constraints.

It answers the question every planning cycle raises: given everything you
could fund, which specific set of projects should you actually commit to so
total value is maximized without breaking budget, headcount, or dependency
rules?

## Background

### Problem Domain

Portfolio optimization is a constrained binary selection problem (choose/do not
choose each project). It follows the same logic used in capital budgeting and
venture portfolio construction: individually attractive projects can still be
dropped once budget, resource, and dependency rules interact across the whole
set.

### Real-World Uses

- **Capital allocation**: Viable initiatives often outnumber available budget.
	Use the model to select the project combination that maximizes total value
	under funding and resource limits.
- **Product roadmap selection**: Feature candidates compete for finite delivery
	capacity and spend. Use the model to prioritize the highest-value set while
	respecting hard constraints.
- **R&D portfolio planning**: Opportunity value may be high but investment caps
	are strict. Use the model to choose projects objectively while enforcing
	minimum or maximum portfolio size.
- **Dependency-aware prioritization**: Some projects require prerequisites and
	others cannot run together. Use the model to build a feasible portfolio that
	respects `depends_on` and `excludes` rules.

## Inputs

- `projects`: Input table with required columns `Project`, `Value`, and `Cost`,
	plus optional `Resource` and `Must Do`. Any row with `Must Do > 0` is forced
	into the selected portfolio.
- `project_rules`: Input table with columns `From`, `To`, and `Type` where
	`Type` is one of `depends_on` or `excludes`.
	`depends_on` means selecting `From` requires selecting `To`; `excludes` means
	the two projects cannot both be selected.
- `project_budget_limit`: Optional total cost cap on selected projects.
- `project_resource_limit`: Optional total resource cap.
	This requires `Resource` in the `projects` table.
- `project_max_selected`: Maximum number of selected projects.
	Use `0` for no upper limit.
- `project_min_selected`: Minimum number of selected projects.
	Use `0` for no lower limit.
- `show_zero`: Controls output display.
	Turn on to include non-selected projects; turn off to show only selected
	projects.

## Results

- `Summary`: Portfolio headline with selected project count, total value,
	total cost, and active limit references. This is your primary
	decision-quality snapshot.
- `Decision Table`: Project-level selection details including selected flag and
	value/cost/resource contributions, so stakeholders can review what was kept
	versus dropped.
- `Constraint Slack`: Slack for budget, resource, count, and rule constraints,
	useful for seeing whether additional budget/capacity would likely improve
	portfolio value.

## Understanding the Calculation

Objective:

- Maximize $\sum_p \text{Value}_p x_p$.

Constraints can include:

- Budget: $\sum_p \text{Cost}_p x_p \le B$
- Resource: $\sum_p \text{Resource}_p x_p \le R$
- Count bounds, must-do constraints, dependency/exclusion rules.

## Example

Default run gives `Optimal` objective `400`, selecting `3` projects with total
cost `215` under budget limit `220`.

Interpretation: selected combination yields highest possible total value while
remaining within constraints. A project can be rejected here even with a great
value-to-cost ratio on its own — `depends_on` and `excludes` rules mean the
best portfolio is not just the sum of the best individual projects.

## Important Assumptions and Limitations

- Project values and costs are treated deterministic and additive.
- No schedule/time-phased dependency modeling.
- No risk-adjusted objective in this model.
