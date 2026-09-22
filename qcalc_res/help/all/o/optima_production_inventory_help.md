# Optimization: Production and Inventory Planning

## Purpose

This calculator plans period-wise production and inventory for multiple items to
minimize total cost (production, holding, optional backlog, optional setup)
while satisfying flow-balance constraints.

It answers a question every planner juggles period after period: how much
should you produce now versus later, so carrying costs and shortage risk stay
as low as possible across the whole planning horizon?

## Background

### Problem Domain

Multi-period production planning decides how much to produce now versus later,
considering inventory carrying and shortage/backlog implications. It descends
from the classic dynamic lot-sizing problem in operations research, which asks
a deceptively simple question with a surprisingly rich answer: is it cheaper
to build ahead and store it, or wait and risk running short?

### Real-World Uses

- **Factory monthly planning**: Demand changes by period while line capacity and
  production cost also vary over time. Use the model to set period-wise
  production quantities that minimize total planning cost.
- **SKU make-to-stock planning**: Producing early raises holding cost, while
  producing later can create service pressure. Use the model to optimize the
  production-inventory balance for each item.
- **Capacity-limited replenishment**: Maximum producible quantity may fall short
  of period demand. Use the model to allocate constrained production and manage
  inventory/backlog flow logically.
- **Inventory vs backlog tradeoff**: Carrying stock incurs holding cost, while
  delayed fulfillment incurs penalty. Use the model to find the lowest-cost
  tradeoff across the full horizon.

## Inputs

- `prodinv_item_master`: Input table with columns `Item`, `Initial Inventory`,
  `Holding Cost`, and `Backlog Penalty`.
  `Initial Inventory` should use the same quantity basis as demand and
  production. `Holding Cost` and `Backlog Penalty` are per one quantity unit.
- `prodinv_demand`: Input table with columns `Period`, `Item`, and `Demand`.
- `prodinv_production`: Input table with columns `Period`, `Item`, `Unit Cost`,
  and `Max Production`, plus optional `Setup Cost`. Every Period-Item pair must
  exist in this table. `Max Production` should use the same quantity basis as
  `Demand`, and `Unit Cost` is per one quantity unit.
- `prodinv_qty_type`: Quantity variable type.
  Use `continuous` for fractional quantities or `integer` for whole-number
  quantities.
- `prodinv_allow_backlog`: Backlog policy.
  Use `Yes` to allow backlog carry-forward with penalty; use `No` to force
  in-period demand fulfillment.
- `show_zero`: Controls output display.
  Turn on to include inactive rows; turn off to show only relevant non-zero
  rows.

## Results

- `Summary`: Horizon-level planning picture with total demand/production,
  ending inventory/backlog, and cost-component breakdown. This helps validate
  whether the plan is financially and operationally acceptable.
- `Decision Table`: Period-item plan rows with demand, production,
  ending inventory, ending backlog, unit cost, capacity, utilization, and setup
  cost. This is the execution-level schedule for planning teams.
- `Constraint Slack`: Slack for production caps, setup links, and
  inventory-balance constraints, useful for diagnosing where the plan is most
  constrained.

## Understanding the Calculation

Objective:

- Minimize production + holding + backlog + setup costs.

Constraints:

- Production cap each period-item.
- If setup cost is active, production is linked to setup binary variable.
- Inventory balance by period and item:
  - with backlog: previous inventory - previous backlog + production
    equals demand + ending inventory - ending backlog
  - without backlog: previous inventory + production equals demand + ending
    inventory.

## Example

Default run returns `Optimal` objective `1986.5`, with totals:

- `Total Demand = 300`
- `Total Production = 270`
- `Ending Inventory = 0`
- `Ending Backlog = 0`

Interpretation: initial inventory plus optimized production exactly cover demand,
with setup cost included and no residual stock/backlog at horizon end. Zero
ending inventory and backlog together are a good sign here — production was
timed tightly to demand rather than masking a planning gap with excess stock
or unpaid shortfall.

## Important Assumptions and Limitations

- Deterministic demand and costs.
- No explicit changeover sequence constraints.
- No shelf-life/perishability logic.
- Backlog is a linear penalty abstraction when enabled.
