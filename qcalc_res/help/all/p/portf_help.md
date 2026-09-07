# Portfolio Optimization

## Purpose

This calculator finds a set of investment weights across several stocks
that achieves a specific target annualized return, using each stock's
historical price movements. It is useful for deciding how to split an
investment across a group of stocks so that the combined portfolio's
expected return matches a goal you set, while only ever holding
non-negative amounts of each stock.

## Background

### From historical prices to expected return

The calculator starts from a table of historical closing prices for each
stock and converts them into daily returns (the day-to-day percentage
change in price). Averaging those daily returns and scaling them up to a
yearly basis gives each stock's expected annualized return. A portfolio's
overall expected return is the weighted average of its stocks' expected
returns, using the fraction of the portfolio invested in each one (the
**Weight**). The calculator searches for the combination of weights — each
between 0% and 100%, all summing to 100% — that makes this weighted-average
return equal your **Target Return**.

## Inputs

### CSV File

A table of historical closing prices (uploaded, or given as a URL), with
one column identifying the date of each observation and one additional
column per stock, containing that stock's closing price on each date. Each
column of prices is converted internally to daily returns before
optimization. For example:

```
TranDate   StockA   StockB   StockC
1/1/2024   85.0     257.5    146.2
1/2/2024   85.0     257.5    146.2
1/3/2024   85.2     256.8    147.0
...
```

The first column's name and date format do not matter — it is never parsed
as an actual date, only used as a row label. What matters is that the rows
are already listed in chronological order, oldest first, since the
day-to-day returns are calculated from row to row, not from the date
values themselves. You can use a different date format
entirely, or even use plain labels like `Day1`, `Day2` — as long as the
row order is correct, the result is unaffected.

### Target Return

The annualized return you want the optimized portfolio to achieve, entered
as a decimal fraction (for example, `0.3` for a 30% annual return). The
calculator searches for portfolio weights that make the expected return
equal to this value; a target far outside the range achievable by the
stocks provided may not be reachable.

### Show Input

When checked, the original uploaded price table is included in the results
as **Input Data**, so you can review the source data alongside the
optimization result. Leave unchecked to omit it.

## Results

### Success

Whether the optimizer found a set of weights that satisfies the
constraints (weights between 0 and 1, summing to 1, and matching the
**Target Return**). If this is not successful, the target may not be
achievable with the stocks and historical data provided.

### Expected Return

The annualized return actually achieved by the optimized weights. When
**Success** is true, this should match your **Target Return**.

### Optimized Portfolio

A table with one row per stock:

-   **Stock** — the stock's column name from the **CSV File**.
-   **Weight** — the fraction of the portfolio to invest in that stock, as
    found by the optimizer (between 0 and 1; all weights sum to 1). A
    weight of 0 (or a value effectively 0, shown in scientific notation)
    means that stock is excluded from the optimized portfolio.
-   **Avg Annual Return** — that stock's own annualized historical return,
    based on its average daily price change scaled up to a year. This is
    the per-stock return the optimizer weighs and combines to reach the
    portfolio's **Expected Return**; a negative value means the stock lost
    value on average over the historical period covered by the data.

### Log

The raw output of the underlying numerical optimizer, useful mainly for
troubleshooting if **Success** is false.

### Input Data

The original uploaded price table, shown only when **Show Input** is
checked; otherwise displays "Not Shown".

## Understanding the Calculation

Each stock's price series is converted to day-to-day percentage returns,
and the average daily return is scaled to an annual figure. The optimizer
then searches for a **Weight** for every stock, subject to: every weight is
between 0 and 1; all weights sum to 1; and the weighted-average annualized
return of the portfolio equals the **Target Return**. Among the weight
combinations that satisfy these conditions, the optimizer returns the
first one it converges to — it is not necessarily minimizing risk or
volatility, only matching the target return under the stated constraints.

## Example

Using the sample historical price data for six stocks (ACMB, APOT, BPMO,
SNGU, STQM, UNVC) with a **Target Return** of 0.3 (30% per year), the
calculator finds a portfolio with:

-   **Success**: True, **Expected Return**: 0.30 (matching the target)
-   SNGU: weight ≈ 0.18
-   STQM: weight ≈ 0.47
-   UNVC: weight ≈ 0.35
-   ACMB, APOT, and BPMO: weight ≈ 0 (excluded)

This means investing roughly 18% in SNGU, 47% in STQM, and 35% in UNVC,
with nothing in the other three stocks, is expected to achieve a 30%
annualized return based on their historical price behavior. This makes
sense given their individual **Avg Annual Return** values: SNGU is close
to flat (about -5%), while STQM (about 47%) and UNVC (about 26%) are the
strongest historical performers among the six, so the optimizer favors
them to reach the 30% target; ACMB, APOT, and BPMO all show negative
historical returns and are excluded entirely.

## Important Assumptions and Interpretation

-   Expected returns and weights are derived purely from **historical**
    price movements in the CSV file; they are not a guarantee of future
    performance.
-   The optimizer only targets a specific return — it does not minimize
    risk, volatility, or correlation between stocks, so two different runs
    that both hit the target return may carry very different risk levels.
-   Weights are constrained to be non-negative (no short selling) and to
    sum to exactly 1 (the full portfolio is invested, with no cash held
    back).
-   If **Success** is false, or the **Target Return** is very high or low
    relative to what the historical data supports, the optimizer may not
    find a valid set of weights.
