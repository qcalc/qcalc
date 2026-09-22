# Optimization: Routing

## Purpose

This calculator finds the minimum-cost flow from a source node to a target node
over a directed network with edge capacities.

It helps you answer a very practical question: if a single direct connection
can't (or shouldn't) carry your entire required volume, how should you split
it across the available connections so everything still gets through at the
lowest possible cost? Instead of guessing which combination of routes to use,
you get a ready-to-execute, least-cost dispatch plan.

## Background

### Problem Domain

Routing optimization here is a minimum-cost flow model, not shortest path alone,
because capacities and demanded flow quantity are enforced. This is the same
class of problem behind large-scale logistics and network-traffic engines:
the cheapest single path is often blocked by capacity, forcing flow to split
across multiple routes at once.

### Real-World Uses

- **Freight routing with lane limits**: The cheapest direct lanes may not have
	enough capacity. Use the model to route required volume through alternate
	arcs at lowest total transport cost.
- **Data/network traffic routing**: Link bandwidth is constrained and path
	costs are non-uniform. Use the model to push feasible minimum-cost flow from
	origin to destination.
- **Multi-hop logistics transfer planning**: Shipments may need intermediate
	nodes because of network topology. Use the model to allocate path flow while
	satisfying demand and node-balance rules.
- **Pipeline/utility dispatch**: Target flow must move through a constrained
	network without breaching segment limits. Use the model to compute least-cost
	edge-level dispatch quantities.

## Inputs

- `routing_object`: Edge table with columns `From`, `To`, `Cost`, and
	`Capacity`.
	`Capacity` should use the same quantity unit basis as `demand_qty`, and
	`Cost` is interpreted per one unit of routed flow.
- `source_node`: Start node that provides net outflow.
- `target_node`: End node that receives net inflow.
- `demand_qty`: Required net flow quantity from `source_node` to `target_node`.
	Use the same quantity unit basis as edge `Capacity`.
- `routing_flow_type`: Edge flow type.
	Use `continuous` for fractional flow or `integer` for whole-number flow.
- `show_zero`: Controls output display.
	Turn on to include zero-flow edges; turn off to show only used edges.

## Results

- `Summary`: High-level routing outcome with `Status`, `Objective`, source,
	target, demand, and total edge flow. This confirms whether required flow is
	feasible and what minimum transport cost it implies.
- `Decision Table`: Edge-level dispatch plan (`Flow`, `Capacity`,
	`Utilization %`, `Unit Cost`) that shows which arcs carry volume and where
	network pressure exists.
- `Constraint Slack`: Slack for edge-capacity and node-conservation
	constraints, useful for identifying bottleneck links.

## Understanding the Calculation

Objective:

- Minimize $\sum_{(i,j)} c_{ij} f_{ij}$.

Constraints:

- Edge cap: $f_{ij} \le \text{Capacity}_{ij}$.
- Flow conservation at each node.
- Source net outflow equals `demand_qty`; target net inflow equals it.

## Example

Default run gives `Optimal` objective `90` for demand `10` from `N1` to `N4`,
using edges:

- `N1 -> N3: 10`
- `N3 -> N4: 10`

Interpretation: this path is cheapest while satisfying capacity and flow
conservation constraints. If a seemingly obvious direct lane isn't used, check
its `Capacity` — the optimizer routes around any edge, however cheap, the
moment it can't carry the required volume.

## Important Assumptions and Limitations

- Single source and single target in one solve.
- Linear per-unit edge cost.
- No transit time, reliability, or fixed edge-open costs.
