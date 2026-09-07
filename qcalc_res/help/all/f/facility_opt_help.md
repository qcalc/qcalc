# Facility Location Optimization - Facility to Customer

## Purpose

This calculator helps decide **which candidate facility sites to open, and
how to assign customer demand to them**, in order to serve all customers at
the lowest total cost. It is useful for supply-chain and network planners
choosing among a shortlist of possible warehouse, plant, or distribution
sites, when opening a facility carries a fixed cost and serving a customer
from it carries a variable cost or distance.

The calculator solves an optimization problem: it selects a subset of the
candidate facilities and splits each customer's demand across them so that
total cost — fixed costs of open facilities plus variable transportation
cost — is as low as possible, while respecting facility capacity and any
service-level constraints you set.

## Background

### Fixed cost vs. variable cost trade-off

Opening a facility usually costs money regardless of how much it is used
(rent, staffing, equipment — captured here as **Fixed Cost**), while serving
each unit of customer demand from a facility has its own per-unit cost or
distance (captured in the **Cost** table). Opening more facilities tends to
shorten the distance to customers and lower variable cost, but adds more
fixed cost. Opening too few facilities saves fixed cost but can increase
variable cost and make it harder to serve nearby customers well. This
calculator searches for the balance that minimizes the combined total.

### Service-level constraints

Beyond minimizing cost, you can require the solution to keep customers
reasonably close to the facility serving them. Two constraints are
available for this: an overall demand-weighted average distance limit, and
a minimum percentage of demand that must be served within a chosen distance.
These let you trade a small amount of extra cost for a network that serves
customers more evenly, rather than accepting a cheap solution that serves a
few customers from very far away.

## Inputs

### Cost

A table with one row per customer/demand location and these columns:

-   **Location** — an identifier for the customer or demand point.
-   **Demand** — the quantity that location needs, to be supplied by one or
    more of the candidate facilities.
-   One additional column per candidate facility (named to match the
    **Location** values in the **Facility** table), giving the per-unit cost
    or distance of serving that customer from that facility.

The facility column names in this table must exactly match the facility
locations listed in the **Facility** table; if they do not, the calculator
reports an inconsistency instead of a result.

### Facility

A table listing the candidate facility sites, with columns:

-   **Location** — an identifier for the candidate site (must match a column
    name in the **Cost** table).
-   **Capacity** — the maximum total demand that facility can supply if
    opened.
-   **Fixed Cost** — the cost added to the total whenever that facility is
    chosen to open, regardless of how much of its capacity is used.

### Minimum Number of Facilities

The fewest candidate facilities the solution is allowed to open.

### Maximum Number of Facilities

The most candidate facilities the solution is allowed to open.

### Maximum Average Customer Distance

An optional cap intended to limit how high the average cost/distance may be
across the customer-facility pairs actually used in the solution. Leave
blank to not apply this limit.

### Maximum Average Demand Distance

A cap on the demand-weighted average cost/distance across all deliveries:
the total cost/distance incurred, divided by total demand served, must not
exceed this value. This keeps the network from serving most customers well
while leaving a few served at very high cost/distance.

### Minimum Percent Demand

The minimum share of total demand (as a percentage) that must be served from
a facility within the **Demand Within Distance** threshold.

### Demand Within Distance

The cost/distance threshold used together with **Minimum Percent Demand**:
at least the specified percentage of total demand must be served from a
facility at or within this cost/distance.

## Results

### Status

The outcome of the optimization: **Optimal** means a best solution meeting
every constraint was found. Other statuses (for example, infeasible) mean no
solution satisfies all the constraints as given — try relaxing the
facility-count, capacity, or distance/percentage limits.

### Total Cost

The total cost of the solution: the sum of the variable cost/distance
incurred for every unit of demand delivered, plus the **Fixed Cost** of
every facility chosen to open. It is expressed in the same units used in the
**Cost** and **Fixed Cost** columns you entered (currency, distance, or any
consistent cost metric).

### Selected Facilities

Below the Status and Total Cost, the calculator lists the facilities chosen
to open, shown as `Possible_Facility_<Location> : 1.0` for each opened site.
Candidate facilities not listed here were not selected in the optimal
solution.

## Understanding the Calculation

The calculator builds and solves a mixed-integer optimization model:

-   **Decide which facilities to open**, subject to the **Minimum/Maximum
    Number of Facilities** limits.
-   **Assign demand from every customer location to one or more open
    facilities** so that each location's full **Demand** is met.
-   **Respect each facility's Capacity** — the total demand assigned to a
    facility cannot exceed it — and demand can only be assigned to a
    facility that is actually opened.
-   Apply the optional distance/service-level limits: **Maximum Average
    Customer Distance**, **Maximum Average Demand Distance**, and the
    **Minimum Percent Demand** within **Demand Within Distance**.
-   **Minimize total cost** = sum of (assigned demand × per-unit cost) over
    every customer-facility pair actually used, plus the **Fixed Cost** of
    every opened facility.

The solver searches for the assignment and facility selection that achieves
the lowest possible total cost while satisfying every constraint above.

## Example

Using the default inputs — 12 customer locations with varying demand, and 5
candidate facility sites (BO, NA, PR, SP, WO) each with capacity 2000 and
fixed cost 10000, a minimum of 1 and maximum of 5 facilities allowed, a
maximum demand-weighted average distance of 60, and at least 80% of demand
required within a distance of 50 — the calculator finds:

-   **Status**: Optimal
-   **Total Cost**: 66781.0
-   **Selected Facilities**: BO, NA, PR, and SP are opened; WO is not.

This means opening four of the five candidate sites, and splitting customer
demand among them as determined by the solver, achieves the lowest total
cost (transportation plus fixed costs) while keeping enough customers close
enough to their assigned facility to satisfy the distance requirements.
Opening the fifth site (WO) was not worthwhile once its fixed cost was
weighed against the transportation savings it would add.

## Important Assumptions and Interpretation

-   The **Cost** table values can represent either a monetary transportation
    cost or a physical distance — the calculator treats them the same way
    mathematically, so make sure all entries use one consistent unit or
    currency, matching the **Fixed Cost** unit.
-   Demand at a customer location can be split across more than one open
    facility; the model does not require single-sourcing unless capacity or
    the other constraints force it.
-   The result is a cost-minimizing plan for the inputs given. It does not
    account for factors not modeled here, such as lead time, service-level
    variability by product, or changes in demand over time.
-   If **Status** is not **Optimal**, the listed constraints (facility
    count, capacity, or distance/percentage limits) cannot all be satisfied
    together; relax one or more of them and re-run.
-   The **Cost** table's facility columns must match the **Facility**
    table's **Location** entries exactly, or no result can be produced.
