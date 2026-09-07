# Transshipment Optimization - Plant to Distribution Center to Customer

## Purpose

This calculator finds the cheapest way to move goods from plants to
customers when shipments must pass through an intermediate layer of
distribution centers (DCs), rather than going direct. It is useful for
distribution and logistics planners who route product through DCs and need
to decide how much to ship on each plant-to-DC and DC-to-customer leg, at
the lowest total shipping cost, while fully meeting every customer's demand
without exceeding any plant's capacity.

## Background

### A two-stage network

Goods flow in two stages: **Plant → Distribution Center**, then
**Distribution Center → Customer**. Each plant can only ship up to its
**Capacity** in total. Each customer's **Demand** must be fully met.
Distribution centers themselves do not generate or consume goods — whatever
arrives at a DC from the plants must equal what leaves it to customers, so
DCs act purely as routing points, not storage. Shipping a unit on any given
leg (plant-to-DC or DC-to-customer) has its own cost, and the calculator
searches all the ways to route goods through the network to find the
combination that meets every constraint at the lowest total cost.

## Inputs

### Supply

A table listing each plant with its **Plant** name/identifier and its
**Capacity** — the maximum quantity it can ship in total, across all
distribution centers.

### Distribution

A table listing each distribution center by its **DC** name/identifier.
Distribution centers in this calculator have no capacity limit of their own
— they simply pass through whatever flow the optimal solution routes
through them.

### Demand

A table listing each customer with its **Customer** name/identifier and its
**Demand** — the quantity it must receive, in total, from one or more
distribution centers.

### Cost

A table with one row per usable leg, giving a **From** location, a **To**
location, and the **Cost** of shipping one unit between them. This table
covers both stages of the network: plant-to-DC legs and DC-to-customer
legs. Only legs listed here are considered as possible routes.

## Results

### Network

A diagram of plants, distribution centers, and customers, with a line drawn
for every plant-to-DC and DC-to-customer leg listed in the **Cost** table.
Each line is labeled with the quantity the optimal solution ships along it
(0 if that leg is not used).

### Solution

A text summary of the optimization outcome:

-   **Status** — whether an optimal solution was found. **Optimal** means a
    feasible routing plan meeting every constraint was found at the lowest
    possible cost.
-   **Total Cost** — the total shipping cost of the optimal plan: the sum,
    over every leg used, of quantity shipped multiplied by its **Cost**,
    across both the plant-to-DC and DC-to-customer stages.
-   One line per plant-to-DC leg actually used, stating how many units are
    shipped from that plant to that distribution center.
-   One line per DC-to-customer leg actually used, stating how many units
    are shipped from that distribution center to that customer.

## Understanding the Calculation

The calculator solves an optimization model that:

-   **Minimizes total cost** — the sum of quantity shipped × **Cost** over
    every plant-to-DC and DC-to-customer leg.
-   **Respects each plant's Capacity** — total shipments out of a plant,
    across all distribution centers, cannot exceed its capacity.
-   **Balances flow at each distribution center** — the total quantity
    arriving at a DC from all plants must equal the total quantity leaving
    it to all customers; a DC cannot accumulate or create stock.
-   **Meets each customer's Demand exactly** — the total received by a
    customer, from all distribution centers combined, must equal its
    demand.

Because distribution centers have no capacity limit here, the model is free
to route any amount of flow through a given DC as long as the flow-balance
condition holds; only plant capacity and customer demand constrain the
solution.

## Example

Using the default inputs — two plants (P1 with capacity 100, P2 with
capacity 125), two distribution centers (D1, D2), three customers (C1
demanding 25, C2 demanding 95, C3 demanding 80), and the given cost table —
the calculator finds:

-   **Status**: Optimal
-   **Total Cost**: 69200.0
-   Ship 75 units from P1 to D2
-   Ship 105 units from P2 to D1
-   Ship 20 units from P2 to D2
-   Ship 25 units from D1 to C1
-   Ship 80 units from D1 to C3
-   Ship 95 units from D2 to C2

Every unit that arrives at D1 (105) is passed on to customers from D1 (25 +
80 = 105); every unit that arrives at D2 (75 + 20 = 95) is passed on to C2
(95) — confirming the flow-balance requirement at each distribution center.
Total demand of 200 units is met using 75 units of P1's capacity and 125 of
P2's capacity, at the lowest total cost across both shipping stages.

## Important Assumptions and Interpretation

-   Distribution centers have no throughput capacity in this calculator —
    any volume can pass through a DC as long as inflow equals outflow.
-   A customer's demand can be split across more than one distribution
    center, and a distribution center can be fed by more than one plant;
    the model does not require single-sourcing at either stage.
-   The **Cost** values should use one consistent currency or cost unit
    throughout the table.
-   If total customer demand exceeds total plant capacity, no feasible plan
    exists and **Status** will not show **Optimal** — reduce demand or
    increase capacity and try again.
-   The result is a cost-minimizing routing plan for the inputs given; it
    does not account for factors not modeled here, such as delivery time,
    minimum shipment sizes, or DC capacity/cost changes over time.
