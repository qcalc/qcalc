# Compound Interest Rate with Periodic Payment

## Purpose

This calculator solves for the compound interest rate implied by a
starting amount, an ending amount, and a series of regular payments in
between — for example, an investment that starts with a lump sum, adds a
fixed contribution every month, and reaches a target value after several
years. It reports the rate both per payment period and as an equivalent
annual rate.

## Background

### Solving for the rate with cash flows in and out

Unlike a simple lump-sum growth calculation, this scenario has money moving
both at the start/end (**Present Value** and **Future Value**) and
periodically in between (**Periodic Payment**). Each of these amounts can
be either money going out of your pocket or money coming in, and the
calculator needs to know which is which to solve correctly. It then
searches numerically for the single compound rate per period that makes all
these cash flows consistent with each other — the same approach used to
solve for a loan's interest rate when you know the loan amount, the
payment, and the payoff amount.

## Inputs

### Present Value

The amount at the start of the period.

### Present Value Direction

Whether the **Present Value** is **Incoming** (received by you, such as a
loan you take out) or **Outgoing** (paid by you, such as an initial
investment).

### Future Value

The amount at the end of the **Duration**.

### Future Value Direction

Whether the **Future Value** is **Incoming** (received by you, such as an
investment payout or savings goal) or **Outgoing** (paid by you, such as a
loan balance you must pay off).

### Duration

The total time from the **Present Value** to the **Future Value** (for
example, `5 yr`).

### Periodic Payment

The fixed amount paid or received at every **Payment Interval** throughout
the **Duration**.

### Periodic Payment Direction

Whether the **Periodic Payment** is **Incoming** (received by you) or
**Outgoing** (paid by you, such as a regular contribution or loan
installment).

### Payment Interval

How often the **Periodic Payment** occurs (for example, every month).
Together with **Duration**, this determines the total number of payments.

### Payment When

Whether each **Periodic Payment** is made at the **Period Start** (an
annuity due, common for contributions made at the beginning of a period)
or the **Period End** (an ordinary annuity, common for loan payments made
at the end of a period).

### Starting Guess

An initial estimate of the annual interest rate, used to start the
numerical search for the actual rate. The default is usually sufficient;
adjust it only if the calculation fails to converge.

### Tolerance

How precise the calculated rate must be before the numerical search stops.
Smaller values give a more precise answer but may need more iterations.

### Maximum Iteration

The maximum number of attempts the numerical search will make to find a
rate precise enough to meet the **Tolerance**. If this limit is reached
without converging, the result may be unreliable — try a different
**Starting Guess**.

## Results

### Periodic Interest Rate

The compound interest rate per **Payment Interval** that reconciles the
**Present Value**, **Future Value**, and **Periodic Payment**, given their
directions and timing, expressed as a percentage per interval.

### Annual Interest Rate

The same rate restated as an equivalent effective annual rate, useful for
comparing against annual rates quoted elsewhere, regardless of how often
payments and compounding actually occur.

## Understanding the Calculation

The number of payment periods is the **Duration** divided by the
**Payment Interval**. The calculator treats **Present Value**, **Future
Value**, and **Periodic Payment** as signed cash flows — incoming amounts
are positive, outgoing amounts are negative, based on each amount's
direction setting — and numerically searches for the periodic rate $r$ that
satisfies the standard time-value-of-money relationship linking a present
value, a series of equal payments, and a future value, starting from the
**Starting Guess** and refining the estimate until it is within
**Tolerance** or **Maximum Iteration** is reached. The **Annual Interest
Rate** is then the effective annual rate equivalent to compounding at $r$
every **Payment Interval**.

## Example

Using the default inputs — a Present Value of 100,000 (Outgoing, an initial
investment), a Future Value of 200,000 (Incoming, the payout after 5
years), a Periodic Payment of 1,000 (Outgoing, contributed every month at
the start of each month) — the calculator finds a **Periodic Interest
Rate** of about 0.451% per month, equivalent to an **Annual Interest Rate**
of about 5.54% per year. This is the rate of return that reconciles putting
in 100,000 up front and 1,000 every month, for it to grow to 200,000 after
5 years.

As a check, if the **Periodic Payment** is set to 0 and the **Future
Value** is set equal to the **Present Value** (no growth needed and no
payments made), the calculated rate comes out essentially 0% — confirming
the solver correctly reduces to "no growth" when there is nothing to
explain.

## Important Assumptions and Interpretation

-   Getting the **Present Value Direction**, **Future Value Direction**,
    and **Periodic Payment Direction** settings right is essential — mixing
    up incoming and outgoing will produce a meaningless or unsolvable
    result.
-   The **Periodic Payment** amount and **Payment Interval** are assumed
    constant and evenly spaced throughout the **Duration**; irregular
    contributions are not supported.
-   Because the rate is found by numerical search, an unusual combination
    of inputs (or a poor **Starting Guess**) may fail to converge within
    **Maximum Iteration** — try adjusting the **Starting Guess** or
    **Tolerance** if the result looks implausible.
-   The result describes the rate implied by the cash flows given; it is
    not a forecast of future investment or loan performance.
