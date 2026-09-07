# Debt Paydown vs Investment

## Overview

The **Debt Paydown vs Investment** calculator helps you compare two ways
of using available cash:

1.  **Pay down debt** by making a lump-sum payment.
2.  **Invest the cash** while continuing to make the original debt
    payments.

The calculator projects the financial outcome over one or more
comparison periods and shows which strategy produces the higher net
wealth under the assumptions you provide.

This is a comparison tool, not personalized financial advice.

## Inputs

### Available Cash

The amount of cash available for either debt repayment or investment.

**Example:** `20000 USD`

If the available cash is greater than the outstanding debt, only the
amount needed to eliminate the debt is applied to the debt in the
paydown scenario.

### Debt Remaining

The current outstanding balance of the debt.

**Example:** `100000 USD`

### Debt Interest Rate

The annual interest rate charged on the debt.

**Example:** `9 pct/yr`

A higher debt rate increases the financial benefit of paying down the
debt.

### Remaining Debt Term

The remaining term of the debt, in years.

**Example:** `20`

The calculator uses this term to determine the original monthly debt
payment and the reduced monthly payment after the lump-sum paydown.

### Expected Investment Return

The expected annual investment return before tax.

**Example:** `8 pct/yr`

The calculator applies the investment tax rate to this return.

### Investment Tax

The tax rate applied to investment returns.

**Example:** `15 pct`

The calculator uses the after-tax investment return for the investment
scenario.

### Inflation Rate

The expected annual inflation rate.

**Example:** `3 pct/yr`

Inflation is used to show equivalent values in today's purchasing power.

### Comparison Periods

The number of years over which you want to compare the strategies.

Enter one or more whole numbers separated by commas.

**Example:**

`5,10,20`

This produces results after 5, 10, and 20 years.

## How the comparison works

### Strategy 1 --- Invest

The available cash is invested immediately.

The original debt remains in place, so the original monthly debt payment
continues.

At each comparison date, the calculator determines:

-   investment value;
-   remaining debt balance;
-   net wealth = investment value minus remaining debt.

### Strategy 2 --- Pay Down Debt

The available cash is applied immediately to the outstanding debt.

Because the debt balance is lower, the required monthly payment is
recalculated over the remaining debt term.

The difference between the original and reduced monthly payment is
assumed to be invested at the after-tax investment return.

This makes the comparison fairer: the paydown strategy does not simply
ignore the cash-flow benefit created by the lower debt payment.

At each comparison date, the calculator determines:

-   remaining debt balance;
-   value of the invested monthly payment savings;
-   net wealth = investment of payment savings minus remaining debt.

## Understanding the results

### Original Monthly Debt Payment

The monthly payment calculated from the original debt balance, interest
rate, and remaining term.

### Reduced Monthly Debt Payment

The monthly payment after applying the available cash to the debt.

If the available cash is enough to eliminate the debt, this value
becomes zero.

### Monthly Payment Saving

The difference between the original and reduced monthly payments.

This amount is assumed to be invested every month in the debt-paydown
scenario.

### After-Tax Investment Return

The expected investment return after applying the specified investment
tax.

For example, with an 8% expected return and 15% tax:

-   Before tax: 8%
-   Tax: 15% of the return
-   After tax: 6.8%

### Break-Even Investment Return

The approximate pre-tax investment return required for the investment
return, after tax, to equal the debt interest rate.

For example, with a 9% debt rate and 15% investment tax, the break-even
investment return is approximately 10.59%.

An expected investment return above this level may favor investing,
while a return below it generally favors paying down the debt, subject
to the other assumptions and risks.

## Comparison table

The calculator provides results for every requested comparison period.

Important columns include:


| Result | Meaning |
| --- | --- |
| Investment Value | Value of the initial cash when invested. |
| Debt Balance (Invest) | Remaining debt when the cash is invested. |
| Net Wealth (Invest) | Investment value minus remaining debt. |
| Savings Invested (Paydown) | Future value of the monthly payment savings. |
| Debt Balance (Paydown) | Remaining debt after the lump-sum paydown. |
| Net Wealth (Paydown) | Investment of payment savings minus remaining debt. |
| Wealth Difference | Net wealth from investing minus net wealth from paying down debt. |
| Net Wealth (Invest, Today) | Investment strategy net wealth adjusted for inflation. |
| Net Wealth (Paydown, Today) | Paydown strategy net wealth adjusted for inflation. |
| Difference (Today) | Inflation-adjusted wealth difference. |
| Better Choice | Strategy producing the higher calculated net wealth. |

A **positive Wealth Difference** means the investment strategy produces
higher calculated net wealth.

A **negative Wealth Difference** means the debt-paydown strategy
produces higher calculated net wealth.

## Example

Suppose you have:

-   Available cash: **$20,000**
-   Debt remaining: **$100,000**
-   Debt interest rate: **9%**
-   Remaining debt term: **20 years**
-   Expected investment return: **8%**
-   Investment tax: **15%**
-   Inflation: **3%**
-   Comparison periods: **5, 10, 20 years**

Enter:

``` text
Available Cash       20000 USD
Debt Remaining       100000 USD
Debt Interest Rate   9 pct/yr
Remaining Debt Term  20
Investment Return    8 pct/yr
Investment Tax       15 pct
Inflation            3 pct/yr
Comparison Periods   5,10,20
```

The calculator will then show the relative net wealth of the two
strategies after 5, 10, and 20 years.

## Important assumptions

The comparison depends strongly on the assumptions entered.

In particular:

-   Investment returns are assumed to compound at the specified expected
    rate.
-   Investment returns are reduced by the specified investment tax.
-   The debt is modeled using a fixed interest rate and fixed remaining
    term.
-   The lump-sum debt payment is made immediately.
-   The reduced debt payment is recalculated over the remaining debt
    term.
-   The monthly payment saving from the debt-paydown strategy is
    invested at the after-tax investment return.
-   Inflation is used only to express projected wealth in today's
    purchasing power.
-   The calculator does not account for investment volatility,
    transaction costs, investment fees, changing tax rates, variable
    debt rates, or other personal financial circumstances.

## Interpreting the result

Do not look only at the nominal future value.

A strategy can show a larger future dollar amount but a smaller
inflation-adjusted value. The **Difference (Today)** is therefore useful
when considering long-term periods.

Also consider factors that cannot be captured completely by a numerical
comparison:

-   investment risk;
-   certainty of the debt interest savings;
-   liquidity needs;
-   emergency cash reserves;
-   tax deductions or credits;
-   penalties or fees for early debt repayment;
-   variability of future investment returns.

The calculator provides a mathematical comparison based on the
assumptions supplied. It does not determine which choice is appropriate
for an individual's financial situation.
