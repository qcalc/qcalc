# Number of Periodic Payments

## Purpose

This calculator answers "how long will it take?" for a recurring
financial plan: given a starting amount, a target ending amount, a fixed
periodic payment, and an interest rate, it finds how many payment periods
are needed to get from the starting amount to the target. It is useful for
estimating how long it will take to pay off a loan at a chosen payment
amount, or how long it will take to reach a savings goal with regular
contributions.

## Background

### Two directions, one formula

The same calculation works whether money is flowing toward you or away
from you. Set the **Present Value** to a loan received (Incoming) and the
**Periodic Payment** to your instalment (Outgoing), with a **Future
Value** of 0, to find how many payments it takes to pay off a loan. Or set
**Present Value** to 0 (or a starting balance) and **Future Value** to a
savings goal (Incoming), with **Periodic Payment** as your contribution
(Outgoing), to find how many contributions it takes to reach the goal.

### Direction of cash flows

**Present Value**, **Future Value**, and **Periodic Payment** are each
marked as either **Incoming** (money you receive) or **Outgoing** (money
you pay), using their respective direction settings.

## Inputs

### Present Value

The amount at the start of the plan.

### Present Value Direction

Whether the **Present Value** is **Incoming** (for example, a loan you
receive) or **Outgoing** (for example, an initial deposit you make).

### Future Value

The target amount at the end of the plan (0 for a loan that is fully paid
off).

### Future Value Direction

Whether the **Future Value** is **Incoming** (a savings goal you will
receive) or **Outgoing** (a remaining balance you would owe).

### Interest Rate

The annual nominal interest rate that applies throughout (for example,
`6 pct/yr`). It is converted internally to a rate per **Payment
Interval**.

### Periodic Payment

The fixed amount paid or received at every **Payment Interval**.

### Periodic Payment Direction

Whether the **Periodic Payment** is **Incoming** (money you receive each
period) or **Outgoing** (money you pay each period).

### Payment Interval

How often the **Periodic Payment** is made (for example, every month).

### Payment When

Whether each **Periodic Payment** is made at the **Period Start** (an
annuity due) or the **Period End** (an ordinary annuity).

## Results

### Number of Periods

The number of **Payment Interval**-length periods needed to go from the
**Present Value** to the **Future Value** at the given **Interest Rate**
and **Periodic Payment**. This can include a fraction of a period, meaning
the final payment would be smaller than the regular periodic amount.

### Number of Years

**Number of Periods** converted to years, for easy comparison regardless
of the **Payment Interval** used.

### Total Payment

**Number of Periods** multiplied by **Periodic Payment** — the total
amount paid (or contributed) over the whole plan, before accounting for
interest. Comparing this to the **Present Value** or **Future Value**
shows how much of the outcome comes from the payments themselves versus
interest.

## Understanding the Calculation

The annual **Interest Rate** is converted to a rate per **Payment
Interval**. The calculator then solves for the number of periods $n$ that
satisfies the standard time-value-of-money relationship linking the signed
**Present Value**, **Future Value**, and **Periodic Payment** (positive if
**Incoming**, negative if **Outgoing**) at that periodic rate, given
whether payments fall at the **Period Start** or **Period End**.

## Example

Using the default inputs — a Present Value of 100,000 (Incoming, a loan
received), a Future Value of 0, an Interest Rate of 6% per year, and a
Periodic Payment of 1,000 (Outgoing) made monthly at the start of each
month — the calculator finds a **Number of Periods** of about 136.42
months, or **Number of Years** of about 11.37 years, with a **Total
Payment** of about 136,419.64.

Raising the **Periodic Payment** to 2,000 per month (all else unchanged)
reduces the **Number of Periods** to about 57.11 months (about 4.76
years), with a **Total Payment** of about 114,229.27 — paying more each
month clears the same loan faster and with less total interest paid.

As a savings example: starting from 0, contributing 500 per month
(Outgoing) at 5% per year, to reach a target of 50,000 (Incoming), takes
about 83.77 months (about 6.98 years), with a **Total Payment** (total
contributed) of about 41,882.73 — the remaining 8,117.27 of the 50,000
goal comes from interest earned on the contributions.

## Important Assumptions and Interpretation

-   **Periodic Payment** is assumed to be a fixed, evenly spaced amount for
    every period; irregular payments are not supported.
-   **Interest Rate** is assumed constant for the entire plan.
-   **Number of Periods** can come out as a fraction — treat it as an
    estimate of how many regular payments are needed, with a possible
    smaller final payment to finish exactly on target.
-   Getting the direction settings right for **Present Value**, **Future
    Value**, and **Periodic Payment** is essential; an inconsistent mix of
    directions can produce a result with no realistic meaning or a
    calculation error.
