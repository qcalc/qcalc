# Optimization: Knapsack

## Purpose

This calculator selects items to maximize total value subject to a capacity
limit (weight, budget, volume, or any constrained resource).

It answers a question every budget-constrained decision eventually runs into:
out of everything you'd like to include, which combination actually fits —
and delivers the most value — without going over your limit?

## Background

### Problem Domain

Knapsack optimization helps you pick the best subset (or quantities) under a
hard limit. It's one of the best-known NP-hard problems in computer science —
checking every combination becomes impossible as the item count grows — yet
modern integer programming solvers still find the guaranteed-best answer
quickly for realistic item lists.

### Real-World Uses

- **Budgeting projects/features**: Candidate initiatives exceed available
  budget. Use the model to choose the combination with the highest total value
  under the budget cap.
- **Cargo loading**: Truck or container capacity is limited while item choices
  are many. Use the model to maximize shipment value without overloading.
- **Marketing mix selection**: Campaign options compete for a fixed spend
  ceiling. Use the model to pick the set with the best expected value under the
  cap.
- **Procurement bundles**: Quantity-limited buying opportunities must fit within
  budget or capacity limits. Use the model to decide which items and how many
  units to buy for maximum value.

## Inputs

- `items`: Input table with columns `Item`, `Value`, `Weight`, and optional
  `Max Qty` (present in defaults). `Value` is benefit, `Weight` is consumed
  capacity, and `Max Qty` is used in integer mode. In this model, `Weight`
  means resource consumption per unit item (for example kg, m^3, hours, or
  budget units).
- `capacity_limit`: Total available capacity (for example weight, budget,
  volume, or another constrained resource). This must be in the same unit basis
  as `Weight`.
- `decision_type`: Decision variable type.
  Use `binary` for 0/1 selection and `integer` for quantity selection in the
  range `0..Max Qty` per item.
- `show_zero`: Controls output display.
  Turn on to include non-selected rows; turn off to show only selected items.

## Results

- `Summary`: Overall solution quality with `Total Value`, `Total Weight`,
  `Capacity Limit`, and `Status`. This confirms whether your capacity is used
  effectively.
- `Decision Table`: Item-level decision output with selected quantity and
  contribution fields such as `Value Contribution` and `Weight Contribution`.
  This shows which items drive value and which consume most capacity.
- `Constraint Slack`: Remaining capacity after optimization. A near-zero slack
  indicates the capacity limit is strongly driving the final selection.

## Understanding the Calculation

The model solves:

- Maximize: $\sum_i v_i x_i$
- Capacity: $\sum_i w_i x_i \leq C$
- Decision bounds:
  - binary mode: $x_i \in \{0,1\}$
  - integer mode: $0 \le x_i \le \text{MaxQty}_i$.

Unit interpretation note:

- `w_i` (`Weight`) and `C` (`capacity_limit`) must be in the same units.
  If `Weight` is kg/item, then `capacity_limit` is total kg.
  If `Weight` is budget-per-item, then `capacity_limit` is total budget.

## Example

Default run gives `Optimal` with `Total Value = 37`, `Total Weight = 5`,
`Capacity Limit = 5`, selecting `I1`, `I2`, and `I4`.

Interpretation: capacity is fully used and no higher-value feasible
combination exists under the same limit. When items are indivisible, even the
optimal answer can leave capacity unused — a reminder that "fully packed" and
"best value" are not always the same target.


## Important Assumptions and Limitations

- Linear additive value and weight assumptions.
- No item incompatibility/dependency constraints.
- Single capacity dimension only.
