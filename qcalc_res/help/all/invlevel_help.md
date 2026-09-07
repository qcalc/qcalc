# Calculate Inventory Level

## Purpose

This calculator shows how a stock level would move over time under a
simple **reorder-point** ordering policy: whenever available stock (on hand
plus already on order) drops to or below a reorder point, a fixed-size
order is placed, and it arrives after a lead time. It helps you see how
current stock, pending orders, and demand interact over a planning period,
and whether a chosen reorder point and order quantity keep stock from
running out.

## Background

### Reorder point and order quantity

Two decisions drive the simulation: the **reorder point** — the stock level
that triggers a new order — and the **reorder quantity** — the fixed amount
ordered each time. Demand steadily reduces stock on hand every day. Once the
projected stock position (stock on hand plus quantity already on order but
not yet received) falls to or below the reorder point, a new order for the
reorder quantity is placed. That order arrives after the stated lead time,
adding to stock on the day it is received.

## Inputs

### Demand

The rate at which the item is consumed, expressed per year by default and
applied evenly across every day of the simulation.

### Current Stock

The quantity on hand at the start of the simulation (Day 0).

### Reorder Point

The stock position at or below which a new order is triggered. The
calculator compares this against **Current Stock plus any quantity already
on order but not yet received**, not against on-hand stock alone.

### Reorder Quantity

The fixed quantity ordered every time the reorder point is reached.

### Lead Time

The number of days between placing an order and receiving it.

### Time Horizon

The total length of the simulation.

### Calculate Every

How often, at minimum, a row of results is produced (for example, weekly).
The calculator also adds an extra row on any day an order is placed or
received, even if that day falls between the regular intervals, so events
are never missed from the results.

### Show

Choose whether to display a **Table**, a **Chart**, or **Both** of the
simulated results.

## Results

### Current Stock

The simulated quantity on hand for each reported day. It decreases daily
with demand and increases on days an order is received.

### Reorder Point

The reorder point value repeated on every row, shown alongside **Current
Stock** so you can see how close stock is to triggering a new order.

### Stock Promised

The quantity currently on order but not yet received (0 once no orders are
outstanding). This rises by the **Reorder Quantity** each time an order is
placed and falls by the same amount when that order is received.

### Chart / Table of results over time

The table and chart plot **Current Stock**, **Reorder Point**, and **Stock
Promised** against **Day**. A sudden rise in **Current Stock** marks an
order being received; a rise in **Stock Promised** marks an order being
placed. The results do not include a separate marker column for these
events — they are visible only as these changes in the plotted values.

## Understanding the Calculation

The calculator steps through each day of the **Time Horizon**:

1. Subtract one day's **Demand** from **Current Stock**.
2. If an order placed earlier is due to arrive (its lead time has elapsed),
   add the **Reorder Quantity** to **Current Stock** and remove that amount
   from **Stock Promised**.
3. If **Current Stock plus Stock Promised** has fallen to or below the
   **Reorder Point**, place a new order: add the **Reorder Quantity** to
   **Stock Promised**, to arrive after **Lead Time** days.
4. Record a result row if the day matches the **Calculate Every** interval,
   or if an order was placed or received on that day.

Because a new order is only triggered once per day and only when the
stock position is at or below the reorder point, more than one order can be
outstanding at a time if demand and lead time make that necessary.

## Example

Using the default inputs — Demand of 1200 unit/yr, Current Stock of 150
units, Reorder Point of 200 units, Reorder Quantity of 500 units, Lead Time
of 30 days, a Time Horizon of 1 year, and results calculated at least every
week — the simulation behaves as follows:

-   Stock starts at 150 units, already below the 200-unit reorder point, so
    an order for 500 units is placed on Day 1 (**Stock Promised** becomes
    500).
-   Stock continues to fall with daily demand until Day 31, when the order
    arrives (**Current Stock** jumps up by 500 units and **Stock Promised**
    returns to 0).
-   This cycle of gradual decline, a new order near the 200-unit reorder
    point, and a jump on arrival roughly 30 days later repeats over the
    1-year horizon.

This shows that with these inputs, the 500-unit reorder quantity and 30-day
lead time keep stock from running out, since a new order is placed well
before stock would be depleted.

## Important Assumptions and Interpretation

-   Demand is assumed constant and applied every day; the calculator does
    not model seasonal or random demand variation.
-   Orders are placed at most once per day and always for the full
    **Reorder Quantity** — there is no minimum order quantity check or
    capacity limit.
-   The simulation does not report a stockout warning explicitly; if
    **Current Stock** falls below zero in the results, demand exceeded
    available stock before the next order arrived.
-   Results are a projection based on the inputs given, not a guarantee of
    actual future stock levels, which will vary with real demand and
    supplier performance.
