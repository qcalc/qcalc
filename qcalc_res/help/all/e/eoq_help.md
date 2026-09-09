# Economic Order Quantity and Total Cost

## Purpose

This calculator answers a common inventory planning question: **how much
should be ordered each time, and how often, to keep total inventory-related
costs as low as possible?** It is useful for anyone who manages purchasing or
stock levels for a product with reasonably steady demand — for example
purchasing, operations, or supply-chain planners.

Given the annual demand for an item, the cost of placing an order, and the
cost of holding a unit in stock, the calculator finds the **Economic Order
Quantity (EOQ)** — the order size that balances ordering costs against
holding costs — and reports the resulting order frequency and annual costs.

## Background

### Why order size matters

Ordering in large batches means fewer orders per year, which reduces total
transaction (ordering) cost. But larger orders also mean more average stock
sitting in inventory, which increases holding cost. Ordering in small batches
does the opposite: more frequent orders (higher transaction cost) but less
stock on hand (lower holding cost). The EOQ is the order quantity where these
two competing costs are balanced, minimizing their combined total.

### Two ways to state the holding cost

The calculator lets you describe the cost of holding one unit in stock for a
year in either of two ways:

-   **Directly**, as a cost per unit per year (**Cost of Excess**), or
-   **Indirectly**, as a percentage of the unit's purchase cost (**Cost of
    Capital**) applied to the **Unit Cost**.

If a **Unit Cost** is entered, the calculator derives the holding cost from
**Unit Cost × Cost of Capital** and also reports **Material Cost Total** and
**Total Cost**. If **Unit Cost** is left blank, the calculator uses **Cost of
Excess** directly and cannot compute material or total cost, since the
purchase price of the item is unknown.

## Inputs

### Demand

The quantity of the item expected to be used or sold per year. This is the
annual demand rate that drives how many units must be ordered in total over
the year.

### Transaction Cost

The cost incurred each time an order is placed (for example, administrative,
processing, or delivery costs per order), regardless of the order size.

### Unit Cost

The purchase cost of one unit of the item. This is optional. When provided,
it is used together with **Cost of Capital** to derive the holding cost per
unit, and it enables the **Material Cost Total** and **Total Cost** results.
Leave it blank if you prefer to state the holding cost directly using **Cost
of Excess**.

### Cost of Capital

The annual cost of tying up money in inventory, expressed as a fraction of
the unit cost per year (for example, `0.2` for 20% per year). This is used
only when **Unit Cost** is provided, to derive the per-unit annual holding
cost.

### Cost of Excess

The cost of holding one unit in stock for one year, stated directly in
currency per unit per year. This is used only when **Unit Cost** is left
blank; otherwise the holding cost is derived from **Unit Cost** and **Cost of
Capital** instead.

## Results

### Economic Order Quantity

The order size that minimizes the combined annual ordering and holding cost.
Ordering this many units each time is the most cost-efficient choice given
the stated demand, transaction cost, and holding cost.

### Order Interval

The average time between orders, in months, that results from ordering the
Economic Order Quantity each time. A larger EOQ relative to demand produces a
longer interval between orders.

### Number of Transactions

The number of orders placed per year when ordering the Economic Order
Quantity each time.

### Inventory Cost Total

The total annual cost of holding stock, based on the average inventory level
(half the Economic Order Quantity) and the per-unit annual holding cost.

### Transaction Cost Total

The total annual cost of placing orders: the **Transaction Cost** multiplied
by the **Number of Transactions**.

### Operational Cost Total

The sum of **Inventory Cost Total** and **Transaction Cost Total** — the
total annual cost that the Economic Order Quantity minimizes. This is
reported regardless of whether **Unit Cost** is provided.

### Material Cost Total

The total annual cost of the goods purchased (annual demand valued at **Unit
Cost**). This result appears only when **Unit Cost** is provided.

### Total Cost

**Material Cost Total** plus **Operational Cost Total** — the full annual
cost of acquiring and carrying the item. This result appears only when
**Unit Cost** is provided.

## Understanding the Calculation

The Economic Order Quantity is calculated as:

$$EOQ = \sqrt{\dfrac{2 \times \text{Transaction Cost} \times \text{Demand}}{\text{Cost of Excess}}}$$

where **Cost of Excess** is either entered directly or derived as **Unit
Cost × Cost of Capital** when **Unit Cost** is given.

From the EOQ, the calculator derives:

-   **Number of Transactions** = Demand ÷ EOQ
-   **Order Interval** = 12 months ÷ Number of Transactions
-   **Inventory Cost Total** = (EOQ ÷ 2) × Cost of Excess
-   **Transaction Cost Total** = Transaction Cost × Number of Transactions
-   **Operational Cost Total** = Inventory Cost Total + Transaction Cost Total

When **Unit Cost** is available, **Material Cost Total** = Demand × Unit
Cost, and **Total Cost** = Material Cost Total + Operational Cost Total.

The currency used for all cost results is taken from the currency entered
with **Transaction Cost**.

## Example

Using the default inputs — Demand of 1200 unit/yr, Transaction Cost of 100
USD, Unit Cost of 5 USD/unit, and Cost of Capital of 0.2 per year (20%) — the
derived Cost of Excess is 5 × 0.2 = 1 USD/unit/yr. The calculator returns:

-   **Economic Order Quantity**: approximately 490 units
-   **Number of Transactions**: approximately 2.45 per year
-   **Order Interval**: approximately 4.9 months between orders
-   **Inventory Cost Total** and **Transaction Cost Total**: approximately
    245 USD/yr each
-   **Operational Cost Total**: approximately 490 USD/yr
-   **Material Cost Total**: 6000 USD/yr (1200 units × 5 USD/unit)
-   **Total Cost**: approximately 6490 USD/yr

This means ordering about 490 units roughly every 5 months keeps combined
ordering and holding costs at their lowest achievable level, about 490
USD/yr, for this demand and cost profile.

## Important Assumptions and Interpretation

-   The calculation assumes demand is steady over the year and that
    transaction cost and holding cost per unit do not change with order size.
-   It does not account for quantity discounts, storage capacity limits,
    supplier minimum order quantities, lead time, or stockout risk. For a
    view of stock levels over time given a reorder policy, see the related
    inventory-level calculator (**invlevel**). For the cost impact of a
    supplier's minimum order quantity specifically, see the **moq**
    calculator; for the cost of any other arbitrary order quantity, see
    **purcost**.
-   Results are a cost-minimizing estimate based on the inputs provided, not
    a guarantee of actual costs, which will vary with real-world demand
    fluctuations and pricing changes.
-   If **Unit Cost** is left blank, **Material Cost Total** and **Total
    Cost** are not available, since the purchase price of the item is
    unknown; only the ordering-and-holding cost (**Operational Cost
    Total**) can be determined.
