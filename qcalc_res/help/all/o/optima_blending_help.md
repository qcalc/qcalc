# Optimization: Raw Material Mix

## Purpose

This calculator computes the lowest-cost blend that satisfies batch size and
property specification limits.

It answers a question every formulator faces: out of the ingredients on hand,
what mix hits every quality target at the lowest possible cost, instead of
relying on a fixed recipe that may be overpaying for compliance?

## Background

### Problem Domain

Blending optimization determines material quantities so final composition meets
quality bounds while minimizing cost. It belongs to the same family of math
that launched linear programming in the 1940s (originally applied to diet and
refinery planning), and it still runs quietly behind the scenes whenever a
factory recipe needs to hit a spec at the lowest price.

### Real-World Uses

- **Animal feed/food formulation**: Nutrition specs must be met while
  ingredient prices vary. Use the model to compute least-cost ingredient
  quantities that satisfy composition limits.
- **Fuel/lubricant blending**: Product properties (for example octane or
  viscosity proxies) must stay within spec ranges. Use the model to produce a
  compliant blend at minimum per-unit cost.
- **Alloy/chemical recipes**: Target property windows and material bounds can
  make many recipes infeasible. Use the model to find the cheapest feasible
  recipe for the required batch size.
- **Fertilizer/ingredient mix design**: Nutrient targets must be balanced
  against volatile input costs. Use the model to optimize cost while still
  meeting all min/max property limits.

## Inputs

- `blend_materials`: Input table with required columns `Material` and
  `Unit Cost`, optional bounds `Min Qty` and `Max Qty`, and one or more
  property columns (for example `Protein %`, `Fiber %`).
- `blend_specs`: Specification table with `Property`, `Min %`, and `Max %`.
  Property names must match property columns in `blend_materials` (ignoring
  trailing `%`, case, and spacing differences).
- `batch_size`: Total blend quantity to produce.
- `blend_qty_type`: Material quantity type.
  Use `continuous` for fractional quantities or `integer` for whole-number
  quantities.
- `show_zero`: Controls output display.
  Turn on to include zero-quantity materials; turn off to show only active
  materials.

## Results

- `Summary`: Overall blend economics with `Batch Size`, `Total Cost`,
  `Cost per Unit`, `Material Count`, and `Active Materials`.
  This is the main business view of whether the optimized recipe is attractive.
- `Consistency Note`: Confirms whether optional `Min Qty`/`Max Qty` bounds were
  recognized, helping you verify that your table structure was interpreted as
  intended.
- `Optimal Mix`: Material-level plan including quantity, batch share, cost,
  bounds, remaining headroom, and bound status. This shows exactly what to blend
  and which ingredients are driving cost or tightness.
- `Property Compliance`: Spec-level quality check with required min/max,
  achieved values, slack, and binding status so you can see how safely each
  quality target is met.
- `Constraint Slack`: Slack for batch-balance and property constraints, useful
  for understanding which specs are controlling the final recipe.

## Understanding the Calculation

Objective:

- Minimize total cost $\sum_m c_m x_m$.

Constraints:

- Batch total: $\sum_m x_m = B$.
- Material bounds: $\text{MinQty}_m \le x_m \le \text{MaxQty}_m$.
- Property min/max constraints:
  $\sum_m p_{mk} x_m \ge \text{Min}_k B$ and
  $\sum_m p_{mk} x_m \le \text{Max}_k B$.

## Example

Default run returns `Optimal` with total cost about `400` and cost per unit
`0.4`, using two active materials (A and B). Example quantities:

- `A = 333.33333`
- `B = 666.66667`

Interpretation: this is the cheapest feasible mix that satisfies given protein
and fiber bounds for batch size 1000. Optimal blends often land exactly on a
spec boundary rather than comfortably inside it — a strong signal that the
specification, not ingredient price, is what's controlling the recipe.

## Important Assumptions and Limitations

- Material properties combine linearly by weighted average.
- No nonlinear blending effects or process losses modeled.
- Specs are hard constraints, not soft penalties.
