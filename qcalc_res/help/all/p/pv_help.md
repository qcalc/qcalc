# Present Value (PV) of a Future Cash and Periodic Payment

## Purpose

This calculator answers the reverse of a future-value question: **what is a
future lump sum, plus a series of regular payments, worth today?** It is
useful for evaluating a loan, an annuity, or any arrangement where you know
a target future amount and a stream of periodic payments, and want to know
their combined value in today's terms at a given interest rate.

## Background

### Discounting future money back to today

Money received or paid in the future is worth less today than the same
amount in hand now, because money today can earn interest. This calculator
discounts both the **Future Value** and every **Periodic Payment** back to
the present using the given **Interest Rate**, and adds them together. A
payment due sooner is discounted less (worth closer to its face amount)
than one due later.

### Direction of cash flows

Both **Future Value** and **Periodic Payment** are marked as either
**Incoming** (money you receive) or **Outgoing** (money you pay), using the
**Future Value Direction** and **Periodic Payment Direction** settings. The
calculated **Present Value** is always shown as a positive amount, with a
separate **Cash Flow** result telling you whether that present-day amount
is money you would pay (**Outgoing**) or receive (**Incoming**), based on
the combined directions of what you entered.

## Inputs

### Future Value

The lump sum due at the end of the **Duration**.

### Future Value Direction

Whether the **Future Value** is **Incoming** (money you will receive) or
**Outgoing** (money you will owe or pay).

### Interest Rate

The annual nominal interest rate used to discount future amounts back to
today (for example, `6 pct/yr`). It is converted internally to a rate per
**Payment Interval**.

### Duration

The total length of time from today until the **Future Value** is due (for
example, `5 yr`). Together with **Payment Interval**, this determines the
number of discounting/payment periods.

### Periodic Payment

The fixed amount paid or received at every **Payment Interval** throughout
the **Duration**.

### Periodic Payment Direction

Whether the **Periodic Payment** is **Incoming** (money you receive each
period) or **Outgoing** (money you pay each period).

### Payment Interval

How often the **Periodic Payment** occurs and discounting is applied (for
example, every month).

### Payment When

Whether each **Periodic Payment** is made at the **Period Start** (an
annuity due) or the **Period End** (an ordinary annuity). This affects how
much each payment is discounted, since a payment at the start of a period
is worth slightly more today than one at the end of the same period.

## Results

### Present Value

The value today of the **Future Value** and all **Periodic Payment**
amounts combined, each discounted back from when it occurs. Always shown as
a positive amount.

### Cash Flow

States whether the **Present Value** represents money **Outgoing** (you
would need to pay it today) or **Incoming** (you would receive it today),
based on the combined direction of the **Future Value** and **Periodic
Payment** you entered.

## Understanding the Calculation

The annual **Interest Rate** is converted to an equivalent rate per
**Payment Interval**. The number of periods is **Duration** divided by
**Payment Interval**. The **Present Value** is then:

$$PV = \dfrac{FV}{(1+r)^{n}} + PMT \times (1 + r \times w) \times \dfrac{1-(1+r)^{-n}}{r}$$

where $FV$ and $PMT$ are the signed **Future Value** and **Periodic
Payment** (positive if **Incoming**, negative if **Outgoing**), $r$ is the
rate per period, $n$ is the number of periods, and $w$ is 1 for payments at
**Period Start** or 0 for payments at **Period End**.

## Example

Using the default inputs — a Future Value of 100,000 (Incoming), an
Interest Rate of 6% per year, a Duration of 5 years, and a Periodic Payment
of 1,000 (Outgoing) made monthly at the start of each month — the
calculator returns a **Present Value** of approximately 22,549.25, with
**Cash Flow** shown as **Outgoing**.

For comparison, making the same monthly payments at the end of each period
instead (**Payment When** = Period End) slightly increases the result to
about 22,802.00, since payments made later are discounted a little more,
reducing how much they offset the incoming future value's present worth.
Removing the periodic payments entirely (**Periodic Payment** = 0) leaves
only the discounted future value, giving a **Present Value** of about
74,725.82.

## Important Assumptions and Interpretation

-   **Periodic Payment** is assumed to be a fixed, evenly spaced amount for
    every period; irregular payments are not supported.
-   The **Interest Rate** is assumed constant for the entire **Duration**.
-   Getting **Future Value Direction** and **Periodic Payment Direction**
    right matters for interpreting **Cash Flow** correctly, even though
    **Present Value** itself is always reported as a positive number.
-   The result is a present-day valuation based on the assumed constant
    interest rate; it is not a market price and does not account for risk,
    fees, or taxes.
