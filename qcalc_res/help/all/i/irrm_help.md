# Modified Internal Rate of Return (IRRM)

## Purpose

This calculator finds the **Modified Internal Rate of Return** for a
series of cash flows, an alternative to the standard Internal Rate of
Return (IRR) that lets you separately control the cost of financing
outgoing cash flows and the return earned by reinvesting incoming cash
flows. It is useful when the plain IRR's assumption — that all positive
cash flows are reinvested at the project's own IRR — does not match
reality.

## Background

### Why "modified"

The standard IRR implicitly assumes that any positive cash flow a project
produces is reinvested at that same project's IRR until the end of the
series, which can be an unrealistic (often overly optimistic) assumption,
especially for high-IRR projects. MIRR instead lets you specify two
separate rates: a **Finance Rate**, used to discount the negative cash
flows (money you need to finance), and a **Reinvestment Rate**, used to
grow the positive cash flows (money you receive and reinvest) to the end
of the series. It then finds the single rate that reconciles these two
discounted/compounded totals, giving a typically more conservative and
realistic measure of return than the plain IRR.

## Inputs

### Cashflow Interval

The time period between entries in the **Cashflows** series (for example,
`yr` for one entry per year).

### Cashflows

A single column of cash flow amounts, one per period, in order. The first
entry is normally the initial outlay (a negative number); later entries
are the returns received in subsequent periods.

### Finance Rate

The rate used to discount the series' negative cash flows back to the
present — representing the cost of financing those outflows (for example,
your borrowing rate).

### Reinvestment Rate

The rate used to grow the series' positive cash flows forward to the end
of the series — representing the return you expect to earn by reinvesting
those proceeds elsewhere.

## Results

### Periodic Interest Rate

The Modified Internal Rate of Return per **Cashflow Interval**, reconciling
the **Finance Rate**-discounted outflows with the **Reinvestment
Rate**-compounded inflows of the **Cashflows** series.

### Annual Interest Rate

The same rate restated as an equivalent effective annual rate, regardless
of the **Cashflow Interval** used, so it can be compared with annual rates
quoted elsewhere.

## Understanding the Calculation

All negative cash flows in the series are discounted back to the present
using the **Finance Rate**; all positive cash flows are compounded forward
to the final period using the **Reinvestment Rate**. The **Modified
Internal Rate of Return** is then the single periodic rate that would grow
the present value of the financed outflows into the future value of the
reinvested inflows over the same number of periods.

## Example

Using the default cash flow series -40000, 5000, 8000, 12000, 30000 (one
entry per year), a Finance Rate of 10% per year, and a Reinvestment Rate
of 12% per year, the calculator finds a **Periodic Interest Rate** and
**Annual Interest Rate** of approximately 10.90% per year — close to, but
distinct from, the plain IRR of about 10.58% for the same series, because
of the differing assumed reinvestment rate.

Raising the **Reinvestment Rate** to 20% per year (leaving everything else
unchanged) raises the result to approximately 12.71% per year, showing
that a more optimistic assumption about reinvesting the project's positive
cash flows increases its measured rate of return.

## Important Assumptions and Interpretation

-   Unlike the plain IRR, MIRR always produces a single, well-defined
    result for a normal cash flow series, since it no longer depends on
    solving a polynomial that can have multiple roots.
-   Choosing realistic **Finance Rate** and **Reinvestment Rate** values
    matters — MIRR is only as reliable as these two assumptions. Overly
    optimistic reinvestment rates will produce an overly optimistic MIRR.
-   The result describes the rate implied by the cash flows and the two
    rates you provide; it is not a forecast of future project performance.
