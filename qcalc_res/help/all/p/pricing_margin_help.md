# Pricing and Margin Calculator

The **Pricing and Margin Calculator** helps you understand the profitability of a product or service and determine appropriate pricing based on costs, margins, discounts, and sales volume.

It calculates gross profit, gross margin, markup, target pricing, maximum allowable cost, discounted pricing, margin after discount, break-even price, and total profit at a given quantity.

## Inputs

### Selling Price

The selling price charged for one unit.

**Example:** `100 USD`

This is used to calculate gross profit, gross margin, markup, discounted price, and margin after discount.

### Unit Cost

The total cost associated with one unit for the gross-profit and margin calculations.

**Example:** `60 USD`

### Target Margin

The desired gross margin expressed as a percentage of the selling price.

**Example:** `30 pct`

A 30% margin means that 30% of the selling price is intended to remain as gross profit.

### Target Price

The selling price at which you want to achieve the specified target margin.

**Example:** `100 USD`

This is used to calculate the maximum cost that can be allowed while maintaining the target margin.

### Discount

The percentage discount applied to the selling price.

**Example:** `10 pct`

The calculator uses this to determine the discounted selling price and the resulting margin.

### Quantity

The number of units sold.

**Example:** `1000`

Quantity is used for the break-even price and total profit calculations.

### Fixed Cost

The total fixed cost associated with the quantity being analyzed.

**Example:** `10000 USD`

Fixed costs do not change with the number of units in the simple break-even model.

### Variable Cost

The variable cost incurred for each unit.

**Example:** `60 USD`

This is used for the break-even price and total profit calculations.

## Results

### Gross Profit

The money earned per unit before considering fixed costs:

**Gross Profit = Selling Price − Unit Cost**

For example, if the selling price is $100 and the unit cost is \$60:

**Gross Profit = `$100 − $60` = $40 per unit**

### Gross Margin

Gross profit expressed as a percentage of selling price:

**Gross Margin = Gross Profit / Selling Price × 100**

With a $40 gross profit on a \$100 selling price, the gross margin is 40%.

### Markup

Profit expressed as a percentage of cost:

**Markup = Gross Profit / Unit Cost × 100**

With a `$40` profit on a `$60` cost, the markup is 66.67%.

Margin and markup are therefore different measures. A 40% margin does not mean a 40% markup.

### Required Price

The selling price needed to achieve the specified target margin at the given unit cost:

**Required Price = Unit Cost / (1 − Target Margin)**

For example, if unit cost is $60 and the target margin is 30%:

**Required Price = $60 / (1 − 0.30) = $85.71**

### Maximum Cost

The maximum unit cost that can be allowed while achieving the target margin at the target price:

**Maximum Cost = Target Price × (1 − Target Margin)**

For example, with a target price of $100 and a target margin of 30%:

**Maximum Cost = $100 × (1 − 0.30) = $70**

### Discounted Price

The selling price after applying the specified discount:

**Discounted Price = Selling Price × (1 − Discount)**

For example, a 10% discount on a $100 selling price gives:

**Discounted Price = $100 × (1 − 0.10) = $90**

### Margin After Discount

The gross margin remaining after the discount:

**Margin After Discount = (Discounted Price − Unit Cost) / Discounted Price × 100**

For example, with a `$90` discounted price and a `$60` unit cost:

**Margin After Discount = ($90 − $60) / $90 × 100 = 33.33%**

A discount can therefore reduce the margin substantially even when the discount itself appears small.

### Break-even Price

The minimum selling price required to cover both variable and fixed costs for the specified quantity:

**Break-even Price = Variable Cost per Unit + Fixed Cost / Quantity**

At this price, total revenue equals total cost and profit is zero.

For example, with variable cost of `$60` per unit, fixed costs of $10,000, and quantity of 1,000:

**Break-even Price = $60 + $10,000 / 1,000 = $70**

### Profit at Quantity

The total profit from selling the specified quantity:

**Profit at Quantity = (Selling Price − Variable Cost) × Quantity − Fixed Cost**

For example, with a `$100` selling price, `$60` variable cost, 1,000 units, and $10,000 fixed costs:

**Profit = ($100 − $60) × 1,000 − $10,000 = $30,000**

## Margin vs. Markup

Margin and markup are often confused because both describe profitability as a percentage.

**Margin** measures profit relative to selling price:

**Margin = Profit / Selling Price**

**Markup** measures profit relative to cost:

**Markup = Profit / Cost**

For example:

- Cost = $60
- Selling price = $100
- Profit = $40
- Gross margin = 40%
- Markup = 66.67%

Use **margin** when evaluating profitability as a percentage of sales. Use **markup** when determining how much to add to cost when setting prices.

## Using the Calculator for Pricing Decisions

The calculator can be used in several common ways.

### Setting a price from a target margin

Enter the unit cost and target margin. The **Required Price** shows the selling price needed to achieve that margin.

### Checking whether a proposed price is profitable

Enter the selling price and unit cost. **Gross Profit**, **Gross Margin**, and **Markup** show the resulting profitability.

### Evaluating a discount

Enter the selling price, unit cost, and discount. **Discounted Price** and **Margin After Discount** show how the promotion affects profitability.

### Setting a purchasing or production cost limit

Enter the target price and target margin. **Maximum Cost** shows the highest unit cost compatible with the desired margin.

### Finding the minimum viable price

Enter the variable cost, fixed cost, and quantity. **Break-even Price** shows the price required to cover the costs at that volume.

### Estimating profit at a sales volume

Enter selling price, variable cost, fixed cost, and quantity. **Profit at Quantity** shows the resulting total profit.

## Important distinction between Unit Cost and Variable Cost

The calculator uses **Unit Cost** for gross-profit, margin, markup, target-price, and discount calculations.

**Variable Cost** is used for break-even and total-profit calculations.

These values can be the same when all unit costs are variable. They can differ when the unit cost used for pricing or gross-margin analysis includes costs that are not treated as variable in the break-even model.

## Important assumptions

The calculations use a simple pricing and cost model:

- Gross profit is calculated per unit.
- Gross margin is measured against selling price.
- Markup is measured against unit cost.
- Target margin is treated as a percentage of selling price.
- Break-even calculations use a constant variable cost per unit and total fixed cost.
- Profit at quantity uses the specified selling price and variable cost for every unit.
- Fixed costs are included only in the break-even and total-profit calculations.

The calculator does not account for taxes, commissions, payment-processing fees, changing costs, tiered pricing, volume discounts, product mix, or other business-specific cost structures unless they are incorporated into the supplied inputs.
