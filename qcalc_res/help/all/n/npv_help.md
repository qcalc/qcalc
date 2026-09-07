# Net Present Value (NPV) of Future Cashflows

## Purpose

This calculator discounts a series of future cash flows back to today's
value at a given interest rate, and sums them to give a single **Net
Present Value**. It is useful for judging whether a project or investment's
future cash flows are worth more or less than the initial outlay, once the
time value of money is taken into account.

## Background

### Discounting cash flows to today

Money received in the future is worth less than the same amount today,
because money today can be invested to earn a return. NPV converts every
cash flow in a series — usually starting with an initial outlay (a
negative value) followed by a series of returns (positive values) — into
today's-money terms by discounting each one at the given **Interest Rate**,
based on how many periods away it occurs. Adding up all of these discounted
values gives the **Net Present Value**: a positive NPV means the
discounted returns exceed the initial outlay (the investment adds value at
that rate); a negative NPV means they fall short.

## Inputs

### Interest Rate

The discount rate used to convert future cash flows to present value (for
example, `5 pct/yr`). A higher rate reduces the present value of later
cash flows more than earlier ones, since it compounds over more periods.

### Cashflow Interval

The time period between entries in the **Cashflows** series (for example,
`yr` for one entry per year).

### Cashflows

A single column of cash flow amounts, one per period, in order, starting
from period 0. The first entry is typically the initial outlay (a negative
number); later entries are the returns received in each subsequent period.

## Results

### Net Present Value

The sum of every cash flow in the **Cashflows** series, each discounted
back to period 0 at the **Interest Rate**. A positive value means the
series is worth more, in today's terms, than doing nothing; a negative
value means it is worth less. An NPV of (approximately) zero means the
**Interest Rate** entered is exactly the series' own Internal Rate of
Return.

## Understanding the Calculation

Each cash flow is discounted according to how many periods from the start
it occurs:

$$NPV = \sum_{i=0}^{n} \dfrac{\text{Cashflow}_i}{(1+r)^{i}}$$

where $\text{Cashflow}_0$ is the first entry (discounted by 1, since it
occurs immediately), $r$ is the **Interest Rate** converted to a rate per
**Cashflow Interval**, and $i$ counts periods from the first entry.

## Example

Using the default cash flow series -40000, 5000, 8000, 12000, 30000 (one
entry per year) at an Interest Rate of 5% per year, the calculator returns
a **Net Present Value** of approximately 7,065.27 — the series is worth
about 7,065 more, in today's terms, than the initial 40,000 outlay alone,
at a 5% discount rate.

Raising the Interest Rate to 15% per year turns the result negative,
about -4,560.23, since the later, larger cash flows are discounted much
more heavily at the higher rate. At the series' own Internal Rate of
Return (about 10.58% per year — see the IRR calculator), the Net Present
Value comes out to (effectively) zero, exactly as expected: the IRR is,
by definition, the rate at which a series' NPV is zero.

## Important Assumptions and Interpretation

-   The first **Cashflows** entry is discounted as occurring at period 0
    (today), not one period from now; make sure your initial outlay is
    entered as the first row if that is the intended timing.
-   NPV depends heavily on the chosen **Interest Rate** — always state
    which rate was used to discount when comparing NPV figures, since the
    same cash flows can show a positive NPV at one rate and a negative NPV
    at another.
-   Comparing NPVs across cash flow series is only meaningful when they
    use the same **Interest Rate** and **Cashflow Interval**.
-   The result is a valuation based on estimated future cash flows and an
    assumed constant discount rate; it is not a guarantee of actual
    project or investment performance.
