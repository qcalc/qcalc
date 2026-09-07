# Compound Interest Rate without Periodic Payment

## Purpose

This calculator works backward from a known starting amount and a known
ending amount to find the compound interest rate that explains the growth
between them, with no additional deposits or withdrawals along the way. It
is useful for figuring out what rate of return an investment actually
earned, or what rate you would need to grow a present amount into a target
future amount over a chosen period.

## Background

### Solving for the rate instead of the future value

Most compound-interest calculations start with a rate and compute a future
value. This calculator does the reverse: given the **Present Value**, the
**Future Value**, and the time between them, it solves for the constant
compounding rate that would turn one into the other, assuming no payments
are made or received in between. It reports that rate both per compounding
period and as an equivalent annual rate, so you can compare it with rates
quoted on other terms.

## Inputs

### Present Value

The starting amount.

### Future Value

The ending amount after the stated **Duration**.

### Duration

The total time between the **Present Value** and the **Future Value** (for
example, `6 yr`).

### Interest Interval

How often interest is assumed to compound over that duration (for example,
every month or every year). Together with **Duration**, this determines the
number of compounding periods used to solve for the rate.

## Results

### Periodic Interest Rate

The constant compound growth rate per **Interest Interval** that would grow
the **Present Value** into the **Future Value** over the calculated number
of periods, expressed as a percentage per interval (for example, percent
per month).

### Annual Interest Rate

The same growth rate restated as an equivalent effective annual rate,
regardless of the **Interest Interval** used. This makes it easy to compare
the result with an annual rate quoted elsewhere, even if the underlying
compounding happened monthly, quarterly, or on some other interval.

## Understanding the Calculation

The number of compounding periods is the **Duration** divided by the
**Interest Interval** (for example, 6 years at a monthly interval gives 72
periods). The **Periodic Interest Rate** per period is then the rate that
satisfies:

$$\text{Future Value} = \text{Present Value} \times (1 + r)^{\text{periods}}$$

solved for $r$:

$$r = \left(\dfrac{\text{Future Value}}{\text{Present Value}}\right)^{1/\text{periods}} - 1$$

The **Annual Interest Rate** is the effective annual rate equivalent to
compounding at rate $r$ every **Interest Interval** throughout a full year —
it will equal the **Periodic Interest Rate** only when **Interest Interval**
is already a year.

## Example

Using the default inputs — a Present Value of 100, a Future Value of 200,
a Duration of 6 years, and interest compounding monthly — the calculator
finds a **Periodic Interest Rate** of about 0.967% per month, equivalent to
an **Annual Interest Rate** of about 12.25% per year. This means an
investment compounding at roughly 0.967% every month would double in value
over 6 years.

As a sanity check, doubling an investment in exactly 1 year with monthly
compounding gives a **Periodic Interest Rate** of about 5.95% per month and
an **Annual Interest Rate** of exactly 100% per year — as expected, since
doubling in one year is a 100% annual return regardless of how often it
compounds within that year.

## Important Assumptions and Interpretation

-   The calculation assumes no deposits, withdrawals, or payments occur
    between the **Present Value** and the **Future Value** — only pure
    compounding.
-   The compounding rate is assumed constant across every period; the
    calculator does not solve for a rate that changes over time.
-   Make sure **Duration** divides evenly by **Interest Interval** so the
    number of compounding periods is a whole number.
-   The result describes the rate implied by the two values and the time
    between them; it is not a forecast of future returns.
