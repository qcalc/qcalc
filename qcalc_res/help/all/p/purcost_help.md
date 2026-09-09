# Calculate Purchase Cost

## Purpose

This calculator tells you the annual cost of purchasing and carrying an item
**if you order a specific quantity each time you order**, and shows how that
compares to the cost-minimizing Economic Order Quantity (EOQ). It is useful
when you already have a preferred or practical order size in mind (for
example, a supplier's pack size or minimum order) and want to know its cost
impact, or how far it is from the theoretically optimal order size.

## Background

### Ordering cost vs. holding cost

Every order you place costs money to process (**Transaction Cost**),
regardless of its size. Every unit sitting in stock also costs money to hold
over time (its **Cost of Excess**). Ordering a larger quantity each time
means fewer orders per year (lower total transaction cost) but more average
stock on hand (higher total holding cost); ordering a smaller quantity does
the opposite. This calculator evaluates both costs for the **Order
Quantity** you specify, and also reports the **Economic Order Quantity** —
the order size that would minimize the combined cost — so you can see how
your chosen quantity compares.

### Two ways to state the holding cost

You can describe the annual cost of holding one unit in stock in either of
two ways:

-   **Directly**, as a cost per unit per year (**Cost of Excess**), or
-   **Indirectly**, as a percentage of the unit's purchase price
    (**Cost of Capital**) applied to the **Unit Cost**.

If a **Unit Cost** is entered, the holding cost is derived as **Unit Cost ×
Cost of Capital**, and the calculator also reports **Material Cost Total**
and **Total Cost**. If **Unit Cost** is left blank, **Cost of Excess** is
used directly, and material and total cost cannot be computed since the
purchase price is unknown.

## Inputs

### Demand

The quantity of the item expected to be used or sold per year.

### Transaction Cost

The cost incurred each time an order is placed, regardless of the order
size.

### Unit Cost

The purchase cost of one unit of the item. Optional. When provided, it is
used with **Cost of Capital** to derive the holding cost per unit, and
enables the **Material Cost Total** and **Total Cost** results. Leave it
blank if you prefer to state the holding cost directly with **Cost of
Excess**.

### Cost of Capital

The annual cost of tying up money in inventory, as a fraction of unit cost
per year (for example, `0.2` for 20% per year). Used only when **Unit
Cost** is provided.

### Cost of Excess

The cost of holding one unit in stock for one year, stated directly in
currency per unit per year. Used only when **Unit Cost** is left blank.

### Order Quantity

The quantity you actually intend to order each time — this is the quantity
being evaluated. It does not have to equal the Economic Order Quantity;
the calculator reports the cost of ordering exactly this amount.

## Results

### Order Interval

The average time between orders, in months, that results from ordering the
**Order Quantity** each time.

### Number of Transactions

The number of orders placed per year at the **Order Quantity**.

### Inventory Cost Total

The total annual cost of holding stock, based on the average inventory
level (half the **Order Quantity**) and the per-unit annual holding cost.

### Transaction Cost Total

The total annual cost of placing orders: **Transaction Cost** multiplied by
**Number of Transactions**.

### Operational Cost Total

**Inventory Cost Total** plus **Transaction Cost Total** — the total annual
ordering-and-holding cost at the **Order Quantity** you specified.

### Material Cost Total

The total annual cost of the goods purchased (annual **Demand** valued at
**Unit Cost**). Appears only when **Unit Cost** is provided.

### Total Cost

**Material Cost Total** plus **Operational Cost Total** — the full annual
cost of acquiring and carrying the item at the **Order Quantity** you
specified. Appears only when **Unit Cost** is provided.

### Economic Order Quantity

The order size that would minimize **Operational Cost Total**, shown for
comparison with the **Order Quantity** you entered. It does not change how
the other results above are calculated — those are always based on your
**Order Quantity**.

## Understanding the Calculation

For the **Order Quantity** you specify:

-   **Number of Transactions** = Demand ÷ Order Quantity
-   **Order Interval** = 12 months ÷ Number of Transactions
-   **Inventory Cost Total** = (Order Quantity ÷ 2) × Cost of Excess
-   **Transaction Cost Total** = Transaction Cost × Number of Transactions
-   **Operational Cost Total** = Inventory Cost Total + Transaction Cost Total

When **Unit Cost** is available, **Material Cost Total** = Demand × Unit
Cost, and **Total Cost** = Material Cost Total + Operational Cost Total.

Separately, the calculator computes the **Economic Order Quantity** using
the same formula as the dedicated EOQ calculator:

$$EOQ = \sqrt{\dfrac{2 \times \text{Transaction Cost} \times \text{Demand}}{\text{Cost of Excess}}}$$

This value is informational only — it is not substituted into the cost
results above, which always reflect the **Order Quantity** you entered.

The currency used for all cost results is taken from the currency entered
with **Transaction Cost**.

## Example

Using the default inputs — Demand of 1200 unit/yr, Transaction Cost of 100
USD, Unit Cost of 5 USD/unit, Cost of Capital of 0.2 per year (20%), and an
**Order Quantity** of 300 units — the derived Cost of Excess is 5 × 0.2 = 1
USD/unit/yr. The calculator returns:

-   **Order Interval**: 3 months
-   **Number of Transactions**: 4 per year
-   **Inventory Cost Total**: 150 USD/yr
-   **Transaction Cost Total**: 400 USD/yr
-   **Operational Cost Total**: 550 USD/yr
-   **Material Cost Total**: 6000 USD/yr
-   **Total Cost**: 6550 USD/yr
-   **Economic Order Quantity**: approximately 490 units (for comparison)

This shows that ordering 300 units every 3 months costs 550 USD/yr in
combined ordering and holding cost — about 60 USD/yr more than the 490-unit
Economic Order Quantity would cost, since 300 units is smaller than the
cost-minimizing size and results in more frequent, though individually
cheaper-to-hold, orders.

## Important Assumptions and Interpretation

-   The calculation assumes demand is steady over the year and that
    transaction cost and holding cost per unit do not change with order
    size (no quantity discounts).
-   **Order Quantity** is taken exactly as entered; the calculator does not
    round it, adjust it toward the Economic Order Quantity, or check it
    against any minimum or maximum order size.
-   If **Unit Cost** is left blank, **Material Cost Total** and **Total
    Cost** are not available, since the purchase price of the item is
    unknown; only the ordering-and-holding cost (**Operational Cost
    Total**) can be determined.
-   To specifically evaluate a supplier's **minimum order quantity (MOQ)**
    against the EOQ - including the extra cost the MOQ imposes when it
    exceeds the EOQ - use the **moq** calculator, which builds on this same
    cost model.
-   Results are a cost estimate based on the inputs provided, not a
    guarantee of actual costs, which will vary with real-world demand
    fluctuations and pricing changes.
