# Optimization: Redundancy

## Purpose

This calculator selects one backup option per primary entity at minimum extra
cost, with optional average coverage target and budget limit.

It answers a practical resilience question: of the available backup options,
which one should you commit to for each primary so you get adequate
protection without overspending on redundancy you don't need?

## Background

### Problem Domain

Redundancy planning balances resilience (`Coverage %`) against additional cost.
It's essentially an insurance decision formalized as math: every backup option
costs something, but the right one reduces the chance that a single failure
turns into an outage.

### Real-World Uses

- **System failover pairing**: Each primary service or component needs a backup
	option, and higher coverage typically costs more. Use the model to choose one
	backup per primary at minimum extra cost while meeting coverage targets.
- **Backup supplier planning**: Continuity risk rises when a main supplier
	fails. Use the model to choose backup pairings that maintain resilience while
	controlling added cost.
- **Disaster recovery route pairing**: Every primary route or process requires
	a fallback path with measurable coverage quality. Use the model to select
	lowest-cost fallback options under optional budget limits.
- **Continuity architecture design**: Resilience programs operate under limited
	spend. Use the model to quantify cost-coverage tradeoffs before finalizing
	redundancy pair selections.

## Inputs

- `redundancy_object`: Input table with columns `Primary`, `Backup`,
	`Coverage %`, and `Extra Cost`. You can provide multiple backup options for
	each primary. `Coverage %` is on a percent scale from 0 to 100.
- `min_avg_coverage`: Optional minimum average coverage target across selected
	pairs, also on a 0-100 percent scale (for example 98 means 98%).
- `redundancy_budget_limit`: Optional cap on total extra cost.
- `show_zero`: Controls output display.
	Turn on to include unselected pair rows; turn off to show only chosen pairs.

## Results

- `Summary`: Portfolio-level redundancy outcome with selected pair count,
	average coverage, and total extra cost. This gives the key resilience-cost
	balance at a glance.
- `Decision Table`: Pair-level selection output (`Selected`, `Coverage %`,
	`Extra Cost`) showing exactly which backup options are chosen.
- `Constraint Slack`: Slack for one-backup-per-primary, average-coverage, and
	budget constraints, helping explain whether coverage targets or budget are
	driving decisions.

## Understanding the Calculation

Objective:

- Minimize $\sum_p \text{ExtraCost}_p y_p$.

Constraints:

- Exactly one selected backup per primary.
- Optional average coverage lower bound.
- Optional budget upper bound.

## Example

Default run returns `Optimal` with objective `32`, selecting three pairs,
average coverage about `98.433333%`.

Interpretation: with default data, one option exists per primary, so all pairs
are selected and total extra cost is fixed. The model gets genuinely
interesting once a primary has multiple backup candidates — that's when
`min_avg_coverage` and `redundancy_budget_limit` start actively trading
resilience against cost instead of just confirming a single obvious choice.

## Important Assumptions and Limitations

- Coverage is aggregated as simple average of selected pairs.
- No probabilistic failure dependencies modeled.
- No multi-level or shared-backup capacity effects.
