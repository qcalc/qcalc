# Internal Rate of Return (IRR)

## Purpose

This calculator finds the **Internal Rate of Return** implied by a series
of cash flows over time — the single discount rate at which those cash
flows exactly break even (a Net Present Value of zero). It is useful for
judging an investment or project's own rate of return, so it can be
compared against a required return or against other opportunities.

## Background

### What the IRR tells you

A typical cash flow series starts with an outlay (a negative value — money
spent or invested) followed by a series of returns (positive values). The
**Internal Rate of Return** is the break-even discount rate for that
series: at exactly that rate, the present value of the returns equals the
initial outlay. A project's IRR above your required rate of return
suggests it is worth pursuing; an IRR below your required rate suggests it
is not. A follow-up **Net Present Value** button is offered after this
calculation, letting you check the present value of the same cash flows
at a discount rate of your choosing.

## Inputs

### Cashflow Interval

The time period between entries in the **Cashflows** series (for example,
`yr` for one entry per year).

### Cashflows

A single column of cash flow amounts, one per period, in order. The first
entry is normally the initial outlay (a negative number); later entries
are the returns received in subsequent periods.

## Results

### Periodic Interest Rate

The break-even discount rate per **Cashflow Interval** — the rate at which
the given cash flow series has a Net Present Value of zero.

### Annual Interest Rate

The same rate restated as an equivalent effective annual rate, regardless
of the **Cashflow Interval** used, so it can be compared with annual rates
quoted elsewhere.

## Understanding the Calculation

The calculator searches for the periodic discount rate $r$ that makes the
Net Present Value of the **Cashflows** series equal to zero:

$$\sum_{i=0}^{n} \dfrac{\text{Cashflow}_i}{(1+r)^{i}} = 0$$

where $\text{Cashflow}_0$ is the first entry (typically the initial
outlay) and $i$ counts periods from there. The resulting rate $r$ is the
**Periodic Interest Rate**; the **Annual Interest Rate** restates it as an
effective annual rate.

## Example

Using the default cash flow series -40000, 5000, 8000, 12000, 30000 (one
entry per year), the calculator finds a **Periodic Interest Rate** and
**Annual Interest Rate** of approximately 10.58% per year. This means an
initial outlay of 40,000 followed by those four annual returns breaks even
at a 10.58% annual discount rate — any required return below 10.58% would
make this series worth pursuing on an IRR basis; any required return above
10.58% would not.

## Important Assumptions and Interpretation

-   IRR assumes every positive cash flow it produces is reinvested at the
    same rate as the IRR itself, which can overstate the attractiveness of
    projects with large interim cash flows — see the Modified Internal
    Rate of Return calculator for an alternative that lets you set a
    separate reinvestment rate.
-   A cash flow series with more than one sign change (for example,
    negative, then positive, then negative again) can have more than one
    mathematically valid IRR, or none; treat results from such series with
    caution.
-   The result describes the rate implied by the cash flows given; it is
    not a forecast of future project performance.
