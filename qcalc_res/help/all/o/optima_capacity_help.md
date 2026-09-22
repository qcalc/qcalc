# Optimization: Capacity

## Purpose

This calculator allocates limited resource capacity against required demand,
minimizing allocation cost plus shortage penalty.

It helps you answer a hard but common question: when you can't fully cover
every requirement, which shortfalls should you accept, and how should the
capacity you do have be allocated to keep total cost as low as possible?

## Background

### Problem Domain

Capacity optimization is useful when resources may be insufficient and you need
the least-cost allocation/shortage tradeoff. It formalizes a decision many
teams make instinctively under pressure — which shortfalls are cheapest to
accept — by putting an explicit price on unmet demand instead of leaving it as
an unplanned surprise.

### Real-World Uses

- **Production capacity planning**: Peak demand can exceed available machine or
  line capacity. Use the model to allocate capacity at least cost and quantify
  unavoidable shortfalls.
- **Staffing across departments**: Staff-hours are limited and service requests
  compete for the same pool. Use the model to allocate effort and measure
  shortfalls with penalty impact.
- **Utility/resource allocation**: Finite supply (power, water, bandwidth) must
  cover required loads. Use the model to create a cost-minimizing dispatch with
  explicit unmet-demand quantities.
- **Service commitment planning**: Committed workloads across resources may not
  all be fully fulfillable. Use the model to prioritize allocations using cost
  and shortage-penalty tradeoffs.

## Inputs

- `capacity_object`: Input table with columns `Resource`, `Available`,
  `Required`, and `Unit Cost`.
  `Available` and `Required` must use the same quantity units, and `Unit Cost`
  is interpreted per one quantity unit.
- `capacity_qty_type`: Allocation/shortage quantity type.
  Use `continuous` for fractional quantities or `integer` for whole numbers.
- `shortage_penalty`: Penalty cost applied per unit of shortage in the same
  quantity basis as `Required`.
- `show_zero`: Controls output display.
  Turn on to include rows with zero allocation/shortage; turn off to focus on
  active rows.

## Results

- `Summary`: Aggregate fulfillment outcome with required, allocated, shortage,
  and `Fulfillment %`. This quickly shows whether you can meet demand or must
  accept shortfalls.
- `Decision Table`: Resource-level allocation details (`Required`, `Available`,
  `Allocated`, `Shortage`, `Unit Cost`) to guide operational adjustments.
- `Constraint Slack`: Slack on availability and requirement-balance constraints,
  highlighting where capacity pressure is limiting service levels.

## Understanding the Calculation

Objective:

- Minimize $\sum_r (\text{UnitCost}_r\,\text{Alloc}_r +
  \text{Penalty}\,\text{Short}_r)$.

Constraints:

- $\text{Alloc}_r \le \text{Available}_r$
- $\text{Alloc}_r + \text{Short}_r = \text{Required}_r$
- Non-negativity (and integer if selected).

## Example

Default run returns `Optimal` with objective `1060`, `Total Shortage = 0`, and
`Fulfillment % = 100%`.

Interpretation: available capacity is sufficient, so all requirements are met
without shortage penalties. Try lowering `Available` on one resource and
re-running — you'll see exactly how much shortage the model accepts before it
becomes cheaper than paying for more capacity.


## Important Assumptions and Limitations

- Independent resources (no substitution logic between resources).
- Linear costs and penalties.
- No minimum-run, setup, or temporal constraints.
