# Net Future Value (NFV) of Cashflows

## Purpose

This calculator compounds a series of cash flows forward to a common
future point and sums them to produce a single **Net Future Value**. It is
useful when you want to know what an entire cash flow stream is worth at
the end of the project timeline, at a chosen interest rate. 

> It supports
cash flows at irregular periods, so **Period** values do not need to be
consecutive.

## Background

### Compounding cash flows to a future point

Future value analysis moves every cash flow to a target future time rather
than discounting to today. Earlier cash flows are compounded for longer,
while later cash flows are compounded for fewer periods. Summing those
future-equivalent amounts gives the **Net Future Value** at that target
point.

## Inputs

### Interest Rate

The compounding rate used to move each cash flow forward (for example,
`5 pct/yr`).

### Cashflow Interval

The interval used for compounding (for example, `yr` or `mo`). The entered
**Interest Rate** is converted to this interval before calculation.

### Cashflows

A table with exactly two columns in this order:

-   **Period** (first column), for example 1, 10, 15, 25, 26.
-   **Cashflow** (second column), the corresponding cash flow amount.

Any renamed, reordered, missing, or extra column is rejected.

## Results

### Net Future Value

The sum of all cash flows after compounding each one to the final period
used by the input series.

## Understanding the Calculation

When periods are consecutive by row order, with the last cash flow at
period `N`, the calculation is:

$$NFV = \sum_{i=0}^{N} \text{Cashflow}_i (1+r)^{N-i}$$

where `r` is the interval rate.

When an explicit **Period** column is provided, periods are normalized so
that the first listed period is treated as the start. If the normalized
periods are `t_k - t_1` and the final normalized period is `T`, then:

$$NFV = \sum_{k=1}^{m} \text{Cashflow}_k (1+r)^{T-(t_k-t_1)}$$

This keeps 1, 2, 3, ... equivalent to the consecutive-row model, while
also supporting sparse periods.

## Example

Using default cash flows -40000, 5000, 8000, 12000, 30000 at 5% per year,
the final period is the fifth listed period. The calculator compounds each
entry to that endpoint and returns a **Net Future Value** of approximately
8,587.88.

## Important Assumptions and Interpretation

-   The result is tied to the final period in the provided series. If you
    extend the timeline with additional periods, the NFV changes.
-   Timing matters: the same cash flow amounts at different periods can
    produce very different NFV values.
-   For comparison across alternatives, ensure the same **Interest Rate**,
    **Cashflow Interval**, and horizon definition are used.
-   The calculation assumes a constant compounding rate over the full
    timeline.

### Quick Cross-Check with NPV/FV

For the same series and rate basis:

$$NFV = NPV \times (1+r)^T$$

You can reproduce this in **FV** by setting **Present Value = NPV**,
**Periodic Payment = 0**, and **Duration = T** intervals.
