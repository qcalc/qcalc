# Minimum Order Quantity (MOQ) Impact

## Purpose

Suppliers often impose a **Minimum Order Quantity (MOQ)** — the smallest
quantity they are willing to sell per order — regardless of what is
economically optimal for the buyer. This calculator answers: **when a
supplier's MOQ is larger than the Economic Order Quantity (EOQ), what extra
inventory and cost does that constraint impose?**

It is a companion to the [EOQ calculator](../e/eoq_help.md): where `eoq`
finds the theoretical cost-minimizing order quantity ignoring any supplier
constraint, `moq` takes that same EOQ as a baseline and compares it against
a real-world MOQ, reporting the actual order quantity, actual costs, and the
extra cost/inventory caused by the constraint.

## Background

### EOQ vs. MOQ

The Economic Order Quantity balances ordering cost against holding cost to
find the cheapest order size. A supplier's MOQ is an external constraint
that has nothing to do with cost optimization — it exists because of the
supplier's own production, packaging, or shipping economics. When the MOQ
exceeds the EOQ, the buyer is forced to order more than optimal, carrying
extra average inventory and paying extra holding cost. When the MOQ is
smaller than the EOQ, it has no effect — the buyer simply orders the EOQ as
before.

### Related calculators

-   **`eoq`** — computes the Economic Order Quantity itself (the baseline this
    calculator starts from). Use it directly if you only need the
    theoretical optimum, with no supplier constraint.
-   **`purcost`** — computes ordering/holding/total cost for *any* specified
    order quantity. This calculator uses `purcost` internally to price the
    actual (MOQ-constrained) order quantity.
-   **`invlevel`** — simulates day-by-day inventory levels over time given a
    reorder policy (reorder point and reorder quantity). Use it if you want
    to see stock levels over time rather than a steady-state annual cost
    comparison.

## Inputs

### Demand

The quantity of the item expected to be used or sold per year.

### Transaction Cost

The cost incurred each time an order is placed, regardless of order size.

### Unit Cost

The purchase cost of one unit of the item. Optional — when provided, it is
used with **Cost of Capital** to derive the holding cost per unit and
enables **Material Cost Total** and **Total Cost**. Leave blank to state the
holding cost directly using **Cost of Excess** instead.

### Cost of Capital

The annual cost of tying up money in inventory, as a fraction of unit cost
per year (e.g. `0.2` for 20%). Used only when **Unit Cost** is provided.

### Cost of Excess

The cost of holding one unit in stock for one year, stated directly in
currency per unit per year. Used only when **Unit Cost** is left blank.

### Supplier MOQ

The minimum order quantity the supplier requires per order. This is the
constraint being tested against the EOQ.

## Results

### Economic Order Quantity

The theoretical cost-minimizing order quantity, computed exactly as in the
`eoq` calculator, ignoring the supplier's MOQ.

### Supplier MOQ

The MOQ value entered, echoed back for reference.

### Actual Order Quantity

The order quantity actually used: `max(Economic Order Quantity, Supplier
MOQ)`. This is what is fed into the cost calculations below.

### MOQ is Binding

`True` if the Supplier MOQ exceeds the Economic Order Quantity (so the
constraint actually forces a larger-than-optimal order); `False` if the MOQ
is at or below the EOQ (so it has no effect).

### Order Interval, Number of Transactions

The average time between orders (in months) and the number of orders per
year, based on ordering the **Actual Order Quantity** each time.

### Inventory Cost Total, Transaction Cost Total, Operational Cost Total

The annual holding cost, ordering cost, and their sum, based on the
**Actual Order Quantity** — i.e. the real costs incurred given the MOQ
constraint, not the theoretical EOQ-based minimum.

### Material Cost Total, Total Cost

The annual cost of goods purchased, and the full annual cost (material +
operational). Available only when **Unit Cost** is provided.

### Extra Inventory Cost from MOQ, Extra Operational Cost from MOQ, Extra Total Cost from MOQ

The difference between the actual cost (at the MOQ-constrained order
quantity) and the theoretical minimum cost (at the EOQ) for, respectively,
inventory (holding) cost, operational cost, and total cost. These are zero
when **MOQ is Binding** is `False`, and positive whenever the MOQ forces a
larger-than-optimal order.

## Understanding the Calculation

1.  The Economic Order Quantity is computed exactly as in the `eoq`
    calculator:

    $$EOQ = \sqrt{\dfrac{2 \times \text{Transaction Cost} \times \text{Demand}}{\text{Cost of Excess}}}$$

2.  The actual order quantity is the larger of the two:

    $$\text{Actual Order Quantity} = \max(EOQ, \text{Supplier MOQ})$$

3.  Costs at the actual order quantity are computed with the same cost
    model as `eoq`/`purcost` (Number of Transactions = Demand ÷ Actual Order
    Quantity, Inventory Cost = Actual Order Quantity ÷ 2 × Cost of Excess,
    etc.).

4.  The same cost model is evaluated a second time at the EOQ (the `eoq`
    baseline), and the "Extra ... from MOQ" results are simply the
    difference between the actual and the EOQ-baseline costs.

## Example

Using the default inputs — Demand 1200 unit/yr, Transaction Cost 100 USD,
Unit Cost 5 USD/unit, Cost of Capital 0.2/yr, and a **Supplier MOQ** of 1000
unit:

-   **Economic Order Quantity**: ≈ 490 unit
-   **Actual Order Quantity**: 1000 unit (the MOQ, since it exceeds the EOQ)
-   **MOQ is Binding**: `True`
-   **Order Interval**: 10 months, **Number of Transactions**: 1.2/yr
-   **Operational Cost Total**: 620 USD/yr, vs. ≈ 490 USD/yr at the true EOQ
-   **Extra Operational Cost from MOQ**: ≈ 130 USD/yr
-   **Extra Total Cost from MOQ**: ≈ 130 USD/yr

This means the supplier's 1000-unit MOQ costs about 130 USD/yr more than
ordering the economically optimal 490 units would, purely because of the
larger, less frequent orders it forces.

## Important Assumptions and Interpretation

-   Inherits all the assumptions of `eoq`: steady demand, and transaction
    cost / holding cost per unit that don't change with order size.
-   Assumes the buyer always orders exactly the **Actual Order Quantity**
    each time (no partial fulfillment of the MOQ).
-   Does not account for quantity discounts the supplier might offer at the
    MOQ level (which could offset some of the extra holding cost) — if unit
    cost changes with order size, re-run with the discounted **Unit Cost**
    to see its effect.
-   If **Unit Cost** is left blank, **Material Cost Total** and **Total
    Cost** are not available, same as in `eoq`.
