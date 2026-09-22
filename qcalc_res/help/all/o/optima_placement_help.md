# Optimization: Placement

## Purpose

This calculator assigns entities to locations under per-location capacity while
balancing score and cost.

It answers a question that comes up whenever options differ in both quality
and price: which entity should go where so you get the best overall outcome,
without pushing any location past its capacity?

## Background

### Problem Domain

Placement optimization is a binary assignment with either score-first or
cost-first orientation, using a blended score-cost objective. This mirrors a
common real-world dilemma — the best-performing option is rarely the
cheapest one — and lets you dial in exactly how much extra performance is
worth through `score_weight`.

### Real-World Uses

- **VM/container placement**: Each workload can run on multiple hosts with
	different performance scores and operating costs. Use the model to assign
	workloads within host capacity while optimizing score-cost tradeoff.
- **Warehouse slotting**: Products can be placed in alternative locations with
	different handling efficiency and cost. Use the model to choose the best
	location per entity under slot capacity limits.
- **Team/site assignment**: Teams can be deployed across sites with varying
	benefit and expense. Use the model to enforce one-site-per-team placement
	under the selected objective mode.
- **Asset placement decisions**: High-performing locations can also be more
	expensive. Use the model as a transparent score-vs-cost framework when
	assigning assets to limited-capacity locations.

## Inputs

- `placement_object`: Input table with columns `Entity`, `Location`, `Score`,
	and `Cost`.
- `objective_mode`: Optimization orientation.
	Use `maximize_score` to maximize blended utility or `minimize_cost` to
	minimize the cost-oriented variant of the same blended expression.
- `location_capacity`: Maximum entities allowed per location.
- `score_weight`: Weight applied to `Score` in the blended objective.
- `show_zero`: Controls output display.
	Turn on to include non-selected entity-location rows; turn off to show only
	selected placements.

## Results

- `Summary`: Overall placement quality with objective mode, location capacity,
	total selected score, and total cost. This shows the headline tradeoff the
	optimizer achieved.
- `Decision Table`: Entity-location assignment output (`Selected`, `Score`,
	`Cost`) so you can directly see chosen placements and rejected alternatives.
- `Constraint Slack`: Slack for one-location-per-entity and location-capacity
	constraints, indicating where capacity limits are binding.

## Understanding the Calculation

Binary variable $x_{e,l}$ indicates whether entity $e$ is placed at location
$l$.

Blended expression per pair is $(w \cdot \text{Score}_{e,l} - \text{Cost}_{e,l})$.

- In `maximize_score`, this expression is maximized.
- In `minimize_cost`, its negation is minimized.

Constraints:

- Each entity assigned exactly once.
- Per-location selected entities do not exceed `location_capacity`.

## Example

Default run (`maximize_score`, capacity 2) returns `Optimal` objective `11`,
with assignments like:

- `E1 -> L1`
- `E2 -> L2`
- `E3 -> L2`

Interpretation: this arrangement gives best blended score-cost outcome under
location caps. Try raising `score_weight` and re-running — entities may shift
toward higher-score locations even at higher cost, revealing how sensitive the
plan is to how much performance is worth to you.

## Important Assumptions and Limitations

- Score and cost are linearly combined.
- Same location capacity applies to every location.
- No affinity/anti-affinity or compatibility constraints beyond table rows.
