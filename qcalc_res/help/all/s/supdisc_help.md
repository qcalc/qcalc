# Supplier Discount Analysis

## Purpose

This calculator compares a supplier's **all-units quantity-discount** tiers
to find the tier and order quantity with the lowest relevant annual cost. It
answers whether the purchase saving from accepting a lower unit price is large
enough to offset the extra inventory required to qualify for that price.

Enter the annual demand, the cost of placing an order, the annual cost of
capital, and the supplier's discount tiers. The calculator evaluates every
tier, including purchase cost, ordering cost, and inventory carrying cost,
then identifies the lowest-cost option.

## Background

### Why Supplier Discount Analysis Is Needed

A lower unit price does not automatically make a discount tier the best
choice. A tier may require a larger order, which raises average inventory,
ties up more working capital, and increases annual carrying cost. Supplier
Discount Analysis compares those effects together rather than looking only at
the quoted price.

This is related to, but different from, other inventory calculators:

- **EOQ** finds one cost-minimizing order quantity when the unit price is
  fixed.
- **MOQ** measures the cost of a supplier-imposed minimum order quantity at a
  fixed unit price.
- **Purchase Cost** prices one chosen order quantity, without comparing
  discount tiers or selecting the best one.
- **Inventory Level** shows stock over time for a reorder policy; it does not
  compare supplier prices.

In a discount analysis, each tier has its own unit price. Since carrying cost
is calculated from unit price and the Cost of Capital, each tier can also have
a different economically optimal order quantity.

### All-units discounts

This calculator uses an **all-units** discount rule. Once an order reaches a
tier's minimum quantity, every unit in that order is priced at that tier's
Unit Price. For example, an order qualifying for a 10% tier at 9 USD/unit
costs 9 USD for every unit, not 10 USD for the first units and 9 USD only for
the units above the threshold.

## Inputs

### Demand

The expected quantity used or sold per year, such as `12000 unit/yr`. It must
be greater than zero. Demand is used to calculate annual purchase cost and
the number of orders per year for every tier.

### Transaction Cost

The cost of placing and receiving one order, regardless of its size, such as
`100 USD`. This establishes the currency used in the results. It cannot be
negative.

### Cost of Capital

The annual cost of money tied up in inventory, expressed as a rate such as
`0.2 peryr` for 20% per year. The calculator multiplies each tier's Unit Price
by this rate to calculate that tier's annual carrying cost per unit. It cannot
be negative.

### Discount Tier Table

Enter one row per supplier price tier. The table must contain these columns:

- **Discount Tier**: a name used to identify the tier in the results.
- **Minimum Order Quantity**: the smallest order that qualifies for the tier.
  It can be zero but cannot be negative.
- **Unit Price**: the all-units purchase price for that tier. It must be
  greater than zero.

The first row is treated as the **No-Discount Tier** reference when savings
are calculated. It does not have to be named exactly "No discount", but it
should be your normal base-price option. Tiers are evaluated independently;
the calculator does not require the rows to be sorted.

## Results

### Discount Analysis

This table contains one row per discount tier.

- **Discount Tier** identifies the input row.
- **Minimum Order Quantity** and **Unit Price** repeat that tier's terms.
- **Economic Order Quantity** is the tier-specific EOQ before applying the
  tier minimum.
- **Order Quantity** is the quantity tested for that tier: the larger of its
  Economic Order Quantity and Minimum Order Quantity.
- **Purchase Cost** is annual demand multiplied by Unit Price.
- **Average Inventory** is half of the tested Order Quantity.
- **Average Inventory Value** is Average Inventory multiplied by Unit Price.
- **Inventory Carrying Cost** is the annual cost of holding Average Inventory.
- **Transaction Cost** is the annual ordering cost at the tested Order
  Quantity.
- **Total Annual Cost** is Purchase Cost + Inventory Carrying Cost +
  Transaction Cost. The lowest value is the cost-based winner.
- **Savings vs No-Discount Tier** is the first row's Total Annual Cost minus
  this tier's Total Annual Cost. A positive value means this tier costs less
  than the first row; a negative value means it costs more.
- **Recommendation** displays `Recommended` on the lowest-cost tier.

### Recommended Discount Tier and Recommended Order Quantity

These give the name and tested order quantity of the tier with the smallest
**Total Annual Cost**. They are a cost-only recommendation based on the
values entered.

### Lowest Total Annual Cost and Annual Savings vs No-Discount Tier

**Lowest Total Annual Cost** is the winning tier's annual total. **Annual
Savings vs No-Discount Tier** compares it with the first table row. A positive
value is an annual saving; zero means the first row is already the lowest-cost
option (or is tied for it).

## Understanding the Calculation

For each tier, the annual carrying cost per unit is:

$$H_i = C_i \times r$$

where `C_i` is that tier's Unit Price and `r` is the Cost of Capital. The
tier-specific economic order quantity is:

$$EOQ_i = \sqrt{\dfrac{2DS}{H_i}}$$

where `D` is annual Demand and `S` is Transaction Cost per order. The order
quantity tested for the tier is the larger of `EOQ_i` and the tier's minimum:

$$Q_i = \max(EOQ_i, \text{Minimum Order Quantity}_i)$$

Finally, the calculator compares total annual cost for every tier:

$$TAC_i = D C_i + \frac{Q_i}{2}H_i + \frac{D}{Q_i}S$$

The three terms are, respectively, annual Purchase Cost, Inventory Carrying
Cost, and Transaction Cost. The tier with the smallest `TAC_i` is recommended.

## Example

With the default inputs - **Demand** `12000 unit/yr`, **Transaction Cost**
`100 USD`, **Cost of Capital** `0.2 peryr` - and the following tiers:

| Discount Tier | Minimum Order Quantity | Unit Price |
|---|---:|---:|
| No discount | 0 | 10.00 USD/unit |
| 5% discount | 2,000 | 9.50 USD/unit |
| 10% discount | 4,000 | 9.00 USD/unit |

the approximate results are:

| Discount Tier | Order Quantity | Total Annual Cost | Savings vs No-Discount Tier |
|---|---:|---:|---:|
| No discount | 1,095 unit | 122,191 USD/yr | 0 USD/yr |
| 5% discount | 2,000 unit | 116,500 USD/yr | 5,691 USD/yr |
| 10% discount | 4,000 unit | 111,900 USD/yr | 10,291 USD/yr |

The 10% tier is recommended. Its larger order raises average inventory to
2,000 units and its annual carrying cost to 3,600 USD/yr, but its lower price
reduces annual purchase cost enough to more than offset those added costs.

## Important Assumptions and Interpretation

- The calculator assumes all-units discounts only. It does not model
  incremental discounts, where only units above a threshold receive the lower
  price.
- Demand, unit price, Cost of Capital, and Transaction Cost are treated as
  constant for the whole year.
- Inventory is assumed to decline steadily from each order quantity to zero,
  so average cycle inventory is one-half of the order quantity.
- The calculation includes the inventory carrying cost represented by Cost of
  Capital. It does not separately estimate storage capacity, insurance,
  obsolescence, spoilage, stockout risk, taxes, delivery lead time, or quality
  and reliability differences between suppliers.
- The first tier is the savings reference, not necessarily the lowest-price or
  lowest-cost option. Use a normal no-discount/base-price row first when that
  is the comparison you need.
- A recommendation identifies the lowest calculated annual cost under these
  assumptions. It is a decision aid, not a substitute for supplier, cash-flow,
  capacity, or risk review.