# Optimization: Transportation

## Purpose

This calculator finds the lowest-cost shipping plan from multiple sources to
multiple destinations while meeting all destination demand and respecting each
source capacity.

It is useful when you must decide how much to ship on each source-destination
lane, not just whether a lane is open. In practice, it answers a concrete
question before you commit budget: which combination of routes gets every
customer their required quantity for the least total freight spend?

## Background

### Problem Domain

Transportation optimization is one of the oldest and most studied problems in
linear programming, with roots in WWII-era logistics planning. It still
quietly powers modern distribution software: you choose shipment quantities to
minimize total variable cost, and the same math scales from a handful of
plants to national supply networks.

### Real-World Uses

- **Plant-to-customer dispatch planning**: Multiple plants can serve the same
	customer at different freight rates. Use the model to set lane shipment
	quantities so demand is met at minimum cost.
- **Regional warehouse replenishment**: Demand spikes across regions while
	upstream supply is limited. Use the model to allocate shipments by lane
	without exceeding source capacities.
- **Inter-branch stock balancing**: Some branches hold surplus stock while
	others have deficits, and transfer costs differ by route. Use the model to
	build a least-cost rebalancing plan.
- **Budget-constrained distribution planning**: Freight spend is under pressure
	and lane economics are uneven. Use the model to test feasible low-cost
	allocations and identify expensive lanes.

## Inputs

- `supply`: Input table with columns `Source` and `Capacity`.
	`Source` is the origin node name/id, and `Capacity` is the maximum shippable
	quantity from that source. Use the same quantity unit basis as `demand`
	(for example units, tons, pallets).
- `demand`: Input table with columns `Destination` and `Demand`.
	`Demand` is the required received quantity at each destination and should use
	the same unit basis as `supply` capacity.
- `ship_cost`: Input table with columns `Source`, `Destination`, and `Cost`.
	`Cost` is per-unit shipping cost on that lane. This table must contain the
	full Source-Destination pair grid (every source with every destination).
	`Cost` is interpreted per one flow unit in the same quantity basis as
	`Capacity`/`Demand`.
- `flow_type`: Shipment variable type.
	Use `continuous` for fractional flow and `integer` for whole-number flow.
- `show_zero`: Controls output display.
	Turn on to include zero-flow decisions; turn off to show only active lanes.

## Results

- `Summary`: High-level optimization outcome with `Model`, `Status`,
	`Objective`, and `Decision Count`.
	`Objective` is minimum total shipping cost, and `Status = Optimal` confirms a
	feasible minimum-cost plan was found.
- `Decision Table`: Lane-level shipping plan (`Source`, `Destination`, `Flow`,
	`Unit Cost`). This tells you exactly how much to move on each route.
- `Capacity Utilization`: Per-source utilization (`Used`, `Capacity`,
	`Utilization %`) to show where supply is tight or has headroom.
- `Constraint Slack`: Constraint-by-constraint slack values that help explain
	which limits are binding and where capacity expansions might reduce cost.

## Understanding the Calculation

The model solves:

- Minimize: $\sum_{s,d} c_{sd} x_{sd}$
- Source capacity: $\sum_d x_{sd} \leq \text{Capacity}_s$
- Demand balance: $\sum_s x_{sd} = \text{Demand}_d$
- $x_{sd} \ge 0$ and optionally integer.

## Example

Using defaults, the model returns `Status: Optimal`, objective `66625`, with
active flows such as:

- `P1 -> C1 = 25`
- `P1 -> C3 = 75`
- `P2 -> C2 = 95`

Interpretation: these lane quantities satisfy all demand at minimum total cost
for the given cost table. Notice that not every source-destination pair is
used — the optimizer naturally skips costlier lanes even when they still have
spare capacity, which is often the most useful insight for negotiating
freight rates.

## Important Assumptions and Limitations

- Costs are linear per unit (no tier pricing).
- No explicit lane fixed-charge or minimum-lot logic.
- No transit-time/service-level constraints.
- Full pair grid is required in `ship_cost`.
