# Transportation Optimization - Plant to Customer

## Purpose

This calculator finds the cheapest way to ship goods from a set of plants,
each with a fixed capacity, to a set of customers, each with a fixed
demand, given the cost of shipping between every plant-customer pair. It is
useful for distribution and logistics planners who need to decide how much
each plant should send to each customer to fully meet demand at the lowest
total shipping cost.

## Background

### The classic transportation problem

Each plant can only supply up to its **Capacity**, and each customer's
**Demand** must be fully met. Shipping a unit from a given plant to a given
customer has its own cost, which can vary widely by plant-customer pair
(for example, due to distance). When several plants could serve the same
customer, and a plant could serve several customers, there are many possible
ways to divide the shipments — this calculator searches all of them and
picks the combination that meets every customer's demand, without exceeding
any plant's capacity, at the lowest possible total cost.

## Inputs

### Supply

A table listing each plant with its **Plant** name/identifier and its
**Capacity** — the maximum quantity it can ship in total, across all
customers.

### Demand

A table listing each customer with its **Customer** name/identifier and its
**Demand** — the quantity it must receive, in total, from one or more
plants.

### Cost

A table with one row per plant-customer pair that can be used, giving the
**Plant**, the **Customer**, and the **Cost** of shipping one unit between
them. Only pairs listed here are considered as possible shipping routes; a
pair not listed cannot be used to supply that customer.

## Results

### Network

A diagram of the plants and customers, with a line drawn between every
plant-customer pair listed in the **Cost** table. Each line is labeled with
the quantity the optimal solution ships along it (0 if that route is not
used in the optimal solution).

### Solution

A text summary of the optimization outcome:

-   **Status** — whether an optimal solution was found. **Optimal** means a
    feasible shipping plan meeting every constraint was found at the lowest
    possible cost.
-   **Total Cost** — the total shipping cost of the optimal plan: the sum,
    over every plant-customer pair used, of quantity shipped multiplied by
    its **Cost**.
-   One line per plant-customer pair actually used in the optimal plan,
    stating how many units are shipped from that plant to that customer.
    Pairs not used are omitted from this list.

## Understanding the Calculation

The calculator solves an optimization model that:

-   **Minimizes total cost** — the sum of quantity shipped × **Cost** over
    every plant-customer pair.
-   **Respects each plant's Capacity** — the total shipped out of a plant,
    across all customers, cannot exceed its capacity.
-   **Meets each customer's Demand exactly** — the total received by a
    customer, from all plants combined, must equal its demand.

Total plant capacity does not need to equal total customer demand; capacity
can exceed demand, in which case some plants will ship less than their full
capacity, but total demand must not exceed total capacity or no feasible
plan exists.

## Example

Using the default inputs — two plants (P1 with capacity 100, P2 with
capacity 125) and three customers (C1 demanding 25, C2 demanding 95, C3
demanding 80, for a total demand of 200) with the given cost table — the
calculator finds:

-   **Status**: Optimal
-   **Total Cost**: 66625.0
-   Ship 25 units from P1 to C1
-   Ship 75 units from P1 to C3
-   Ship 95 units from P2 to C2
-   Ship 5 units from P2 to C3

This uses all 100 units of P1's capacity and 100 of P2's 125-unit capacity,
meeting all 200 units of total demand at the lowest possible combined
shipping cost. Splitting C3's demand across both plants (75 from P1, 5 from
P2) is cheaper overall than any single-plant assignment, given the cost
table.

## Important Assumptions and Interpretation

-   Demand for a single customer can be split across more than one plant;
    the model does not require each customer to be served by only one
    plant.
-   The **Cost** values should use one consistent currency or cost unit
    throughout the table.
-   If total demand exceeds total plant capacity, no feasible plan exists
    and **Status** will not show **Optimal** — reduce demand or increase
    capacity and try again.
-   The result is a cost-minimizing shipping plan for the inputs given; it
    does not account for factors not modeled here, such as delivery time,
    minimum shipment sizes, or capacity/cost changes over time.
