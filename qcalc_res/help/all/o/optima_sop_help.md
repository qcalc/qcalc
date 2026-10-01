# Planning: S&OP Optimization

## Purpose

This calculator optimizes a multi-period Sales and Operations Planning (S&OP) plan across products and periods. It decides production, inventory, fulfillment, and optional backlog while respecting capacity and product limits.

It can run in three planning modes:

- Minimize Total Cost
- Maximize Service Level
- Minimize Inventory

Optional modules let you extend the core plan with overtime capacity, BOM-driven material requirements, procurement optimization, stability controls versus a previous plan, and scenario reruns.

## Background

### What the model optimizes

At its core, the model balances demand and supply over time:

- Demand is entered by Product and Period.
- Production is limited by product-level max production and period-level total capacity.
- Inventory flows across periods and must stay above safety stock.
- Backlog can be allowed, disallowed, or capped.

The optimization objective determines the trade-off:

- Cost mode minimizes production, holding, backlog, setup, overtime, stability, and (if enabled) procurement costs.
- Service mode maximizes fulfilled demand, with very small penalties to avoid unnecessary production, inventory, backlog, overtime, and procurement spend.
- Inventory mode minimizes inventory, with very small penalties on backlog/overtime/procurement where applicable.

## Inputs

### Settings

- Objective: Selects the optimization goal. Initial selection is Minimize Total Cost.
- Quantity type: Continuous or Integer decision quantities. Use Integer when whole-unit plans are required.
- Backlog policy: Allow, Disallow, or Cap backlog. Initial policy allows backlog.
- Max backlog percent: Used only when backlog policy is Cap.
- Service level floor percent: Used in cost-minimization mode to enforce a minimum fulfillment percentage.
- Stability enabled: Turns on stability controls against a previous approved plan.
- Scenarios enabled: Turns on scenario reruns and comparison chart.
- BOM enabled: Turns on product-to-material explosion from production plan.
- Overtime enabled: Turns on period overtime capacity and overtime cost.
- Procurement enabled: Turns on integrated supplier sourcing tied to BOM-driven material demand.
- Show zero: Includes zero-valued rows in detailed output tables.

### Product Master (required table)

Each row is one product with planning economics and limits:

- Product
- Opening Inventory
- Safety Stock
- Production Cost
- Holding Cost
- Max Production
- Backlog Penalty
- Setup Cost (optional)

### Demand (required table)

Period-product demand table:

- Period
- Product
- Demand

### Capacity (required table)

Period capacity table:

- Period
- Capacity

Capacity must be provided for every planning period appearing in the union of demand and capacity periods.

### BOM (used when BOM enabled)

Product-to-material coefficients:

- Product
- Material
- Qty per Unit

This is used to derive material demand from solved production.

### Overtime (used when Overtime enabled)

Period overtime data:

- Period
- Overtime Capacity
- Overtime Cost

When enabled, all planning periods must have overtime rows.

### Stability (used when Stability enabled with active penalty/cap)

- Stability penalty: Penalty per unit absolute change from previous production.
- Max change percent: Optional hard cap on absolute change versus previous production.
- Previous plan table:
  - Period
  - Product
  - Previous Production

If stability is active, previous plan data is required.

### Scenarios (used when Scenarios enabled)

Scenario multiplier table:

- Scenario
- Demand Multiplier
- Capacity Multiplier
- Production Cost Multiplier
- Holding Cost Multiplier
- Backlog Penalty Multiplier

### Procurement (used when Procurement enabled)

Procurement is a companion optimization submodel and requires BOM to be enabled.

Control fields:

- Maximum suppliers (0 means no explicit max)
- Procurement quantity type (Continuous or Integer)
- Optional budget limit
- Optional minimum average quality
- Optional maximum average risk

Tables:

- Supplier master: Supplier, Capacity, Fixed Cost, optional Min Order, optional Risk, optional Quality
- Supplier-item cost: supplier/material pair costs and optional pair limits (based on table schema)

If average quality or average risk constraints are used, Supplier master must include the corresponding columns.

## Results

- Summary: Solver status, objective value, objective mode, demand/fulfillment totals, service level, cost breakdown, ending inventory/backlog, overtime, and capacity utilization metrics.
- Period Plan: Product-period plan with demand, fulfilled, production, ending inventory/backlog, safety stock, unit costs, capacity, overtime, setup usage, and stability columns.
- Capacity Utilization: Period-level base capacity, overtime capacity/used/cost, production used, and utilization percentage.
- Product Summary: Totals by product for demand, fulfilled, production, backlog, and ending inventory.
- Constraint Slack: Slack table from the solved optimization model.
- Constraint Slack Note: Interpretation note for positive, zero, and negative slack.

Conditional outputs:

- Stability Summary: Product-period previous vs current production, absolute change, and change cost.
- Overtime Summary: Period overtime capacity, used amount, and overtime cost.
- Scenario Summary: One solved row per scenario with objective and service/cost outcomes.
- Scenario Chart: Bar chart comparing scenarios by objective-relevant metric.
- Procurement Summary: Integrated procurement status, selected suppliers, purchased quantity, and procurement objective.
- Material Requirement Detail: Product-to-material implied usage from solved production plan.
- Material Demand: Aggregated material demand passed into procurement.
- Procurement Decision Table: Purchased quantity and line cost by supplier-material.
- Procurement Supplier Utilization: Supplier selection and capacity utilization.
- Procurement Constraint Slack: Procurement-related constraint slack values.

## Understanding the Calculation

### Core decision structure

For each Product p and Period t, the model creates:

- Production p,t
- Inventory p,t
- Fulfilled p,t
- Backlog p,t (if backlog allowed)
- Setup p,t (binary, if positive setup costs exist)
- Overtime t (if overtime enabled)
- Stability change variables (if stability active)

### Objective logic

- Cost mode minimizes all included cost terms.
- Service mode maximizes fulfilled quantity, then applies tiny penalties to discourage unnecessary side effects.
- Inventory mode minimizes inventory, with tiny penalties on selected optional terms.

### Main constraints

1. Product max production per period:

$$Production_{p,t} \le MaxProduction_p$$

2. Period capacity (plus overtime when enabled):

$$\sum_p Production_{p,t} \le Capacity_t + Overtime_t$$

3. Inventory flow:

$$PrevInventory + Production_{p,t} = Fulfilled_{p,t} + Inventory_{p,t}$$

4. Safety stock floor:

$$Inventory_{p,t} \ge SafetyStock_p$$

5. Demand/backlog balance:

- With backlog:

$$Fulfilled_{p,t} + Backlog_{p,t} = Demand_{p,t} + PrevBacklog_{p,t}$$

- Without backlog:

$$Fulfilled_{p,t} = Demand_{p,t}$$

6. Optional backlog cap (cap policy):

$$Backlog_{p,t} \le Demand_{p,t} \times BacklogCap\%$$

7. Optional service floor in cost mode:

$$\sum_{p,t} Fulfilled_{p,t} \ge TotalDemand \times ServiceFloor\%$$

8. Optional stability controls:

- Absolute change construction from previous production
- Optional cap on absolute change percentage

### Optional procurement coupling

When procurement is enabled (and BOM enabled), material requirements are linked to production via Qty per Unit coefficients. Procurement then decides supplier-material purchases under supplier capacities and optional budget/quality/risk constraints.

### Scenario mode

Scenario mode reruns the same model under multiplier-adjusted demand, capacity, and cost inputs, then returns a comparison table and chart.

## Example

Example planning workflow:

- Objective: Minimize Total Cost
- Backlog policy: Cap
- Service floor percent: set to a target if you need guaranteed minimum fulfillment in cost mode
- Enable Overtime if near-capacity periods are expected
- Enable BOM and Procurement to extend production planning into material sourcing
- Enable Stability when comparing against an already approved prior plan
- Enable Scenarios for demand and capacity stress tests

Expected interpretation:

- Summary gives the primary KPI picture for the selected objective.
- Period Plan and Capacity Utilization explain where constraints bind.
- Constraint Slack helps diagnose which limits are tight.
- Scenario Summary/Chart show plan sensitivity under alternate assumptions.

## Important Assumptions and Interpretation

- Quantities are optimized on the unit basis implied by your tables; keep units consistent across Product Master, Demand, Capacity, Overtime, BOM, and Procurement tables.
- Demand is grouped by Period and Product before solving.
- Capacity must be available for every planning period represented in the run.
- Service-level objective requires backlog to be allowed.
- Procurement cannot run unless BOM is enabled.
- If stability is enabled but penalty and cap are both zero, stability constraints are not effectively active.
- Solver status should always be checked before operational use. Infeasible or non-optimal statuses require input/constraint review.
- This model is a planning optimizer, not an execution schedule; operational sequencing and shop-floor constraints may require additional tools.
