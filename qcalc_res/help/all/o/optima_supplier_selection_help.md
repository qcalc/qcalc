# Optimization: Supplier Selection

## Purpose

This calculator chooses supplier-item purchase quantities to minimize total
procurement cost while satisfying demand and respecting supplier constraints.

It can include fixed supplier activation costs, per-item caps, optional budget,
and optional average quality/risk targets. In practice, it helps you answer:
which suppliers should you actually use, and how much should you buy from
each, so total cost stays low without compromising on quality, risk, or
supply reliability?

## Background

### Problem Domain

Supplier selection is a mixed-integer optimization problem: quantity variables
plus binary supplier-use decisions. It captures a tension every procurement
team faces — the supplier with the lowest unit price is not automatically the
cheapest choice once you add their fixed onboarding or activation cost, so the
optimal mix can look different from a simple lowest-price ranking.

### Real-World Uses

- **Multi-vendor sourcing**: No single supplier can fulfill all demand, and
    supplier capacities differ. Use the model to split purchases across suppliers
    at minimum total landed cost.
- **Risk/quality-governed sourcing**: The cheapest mix can violate acceptable
    quality or risk thresholds. Use the model to meet demand while satisfying
    average risk/quality targets.
- **Spend-constrained procurement**: Budget is fixed, but required quantities
    still need to be purchased. Use the model to test feasibility and determine
    the best supplier-item allocation.
- **Vendor rationalization**: Too many active suppliers increase operational
    overhead. Use the model to cap supplier count while preserving demand coverage
    and controlling cost.

## Inputs

- `material_demand`: Input table with columns `Item` and `Demand`.
    Defines required purchase quantity per item. Use one consistent quantity unit
    basis across all procurement tables.
- `supplier_master`: Input table with columns `Supplier`, `Capacity`, and
    `Fixed Cost`, plus optional `Min Order`, `Risk`, and `Quality`.
    `Capacity` should use the same quantity units as `material_demand`.
- `supplier_item_cost`: Input table with columns `Supplier`, `Item`, and
    `Unit Cost`, plus optional `Max Qty` per supplier-item pair.
    `Unit Cost` is per one quantity unit, and `Max Qty` should use the same
    quantity basis as `Demand` and supplier `Capacity`.
- `max_suppliers`: Maximum number of selected suppliers.
    Use `0` for no supplier-count limit.
- `material_qty_type`: Purchase quantity type.
    Use `continuous` for fractional quantities or `integer` for whole-number
    quantities.
- `budget_limit`: Optional total spend cap including variable and fixed costs.
- `min_avg_quality`: Optional demand-weighted average quality floor.
    Requires `Quality` in `supplier_master` and uses the same numeric scale as
    the `Quality` column.
- `max_avg_risk`: Optional demand-weighted average risk ceiling.
    Requires `Risk` in `supplier_master` and uses the same numeric scale as the
    `Risk` column.
- `show_zero`: Controls output display.
    Turn on to include zero-quantity lines; turn off to show only active lines.

## Results

- `Summary`: Portfolio-level outcome with `Selected Suppliers`,
    `Total Purchased`, `Total Demand`, and minimum `Objective` cost.
    This shows whether demand is fully covered and how many suppliers were needed.
- `Decision Table`: Active supplier-item purchase lines (`Qty`, `Unit Cost`,
    `Line Cost`) used as the execution-ready buying plan.
- `Supplier Utilization`: Per-supplier selection and usage view (purchased qty,
    capacity utilization, fixed cost, optional risk/quality) to evaluate vendor
    concentration and dependence.
- `Constraint Slack`: Slack for capacity, budget, supplier-count, risk, and
    quality constraints; useful for understanding what is constraining cost.

## Understanding the Calculation

Objective:

- Minimize variable purchase cost + fixed supplier costs.

Core constraints:

- Item demand exactly met.
- Supplier total purchases within capacity.
- Linking: purchases from a supplier allowed only if that supplier is selected.
- Optional constraints for min order, budget, max suppliers, average quality,
  and average risk.

## Example

Default run returns `Optimal` with objective `3670`, selecting `2` suppliers
and purchasing total `240` units (exactly matching demand). Sample lines:

- `S1-I1: 100`
- `S3-I2: 80`
- `S3-I3: 60`

Interpretation: a two-supplier mix is cheapest after accounting for both unit
prices and fixed supplier costs. Adding a third supplier might lower unit
costs further but isn't worth its fixed activation cost — exactly the kind of
tradeoff that's hard to see without running the numbers.

## Important Assumptions and Limitations

- Linear unit costs and fixed costs.
- No lead-time, service-level, or disruption probability modeling.
- Quality/risk aggregation is demand-weighted average, not worst-case.
