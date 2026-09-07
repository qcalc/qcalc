# Future Value (FV) of a Principal and Periodic Payment

## Purpose

This calculator projects how much a starting amount and a series of regular
contributions will grow to by a future date, given a compound interest
rate. It is useful for planning savings goals, retirement contributions, or
any scenario where you invest a lump sum and add to it periodically.

## Background

### Two sources of growth

The future value combines two things: the starting **Present Value**
compounding on its own at the given **Interest Rate**, plus a series of
equal **Periodic Payment** contributions, each of which also compounds from
the time it is made until the end of the **Duration**. A payment made
earlier has more time to grow than one made later, which is why *when*
during each period the payment happens (**Payment When**) affects the
result slightly.

### Direction of cash flows

Both **Present Value** and **Periodic Payment** are marked as either
**Outgoing** (money you put in) or **Incoming** (money you receive), using
the **Present Value Direction** and **Periodic Payment Direction**
settings. The calculated **Future Value** is shown as a positive
amount with a direction as well, with a separate **Cash Flow** result telling you whether that final amount is money you would receive (**Incoming**) or a balance you would owe (**Outgoing**), based on what you had put in or received.

## Inputs

### Present Value

The lump sum invested (or borrowed) at the start.

### Present Value Direction

Whether the **Present Value** is **Outgoing** (money you invest or deposit)
or **Incoming** (money you receive, such as loan proceeds).

### Interest Rate

The annual nominal interest rate at which the balance compounds (for
example, `6 pct/yr`). It is converted internally to a rate per **Payment
Interval**.

### Duration

The total length of time the investment grows for (for example, `5 yr`).
Together with **Payment Interval**, this determines the number of
compounding/payment periods.

### Periodic Payment

The fixed amount contributed (or withdrawn) at every **Payment Interval**
throughout the **Duration**.

### Periodic Payment Direction

Whether the **Periodic Payment** is **Outgoing** (money you contribute) or
**Incoming** (money you receive).

### Payment Interval

How often the **Periodic Payment** is made and compounding is applied (for
example, every month).

### Payment When

Whether each **Periodic Payment** is made at the **Period Start** (an
annuity due — the payment has a little extra time to earn interest within
that period) or the **Period End** (an ordinary annuity).

## Results

### Future Value

The projected total value at the end of the **Duration**: the **Present
Value** compounded over the full period, plus all **Periodic Payment**
contributions compounded from when each was made. Always shown as a
positive amount.

### Cash Flow

States whether the **Future Value** represents money **Incoming** (you
would receive it) or **Outgoing** (you would owe it), based on the combined
direction of the **Present Value** and **Periodic Payment** you entered.

## Understanding the Calculation

The annual **Interest Rate** is converted to an equivalent rate per
**Payment Interval**. The number of periods is **Duration** divided by
**Payment Interval**. The **Future Value** is then:

$$FV = PV \times (1+r)^{n} + PMT \times (1 + r \times w) \times \dfrac{(1+r)^{n} - 1}{r}$$

where $PV$ and $PMT$ are the signed **Present Value** and **Periodic
Payment** (negative if **Outgoing**, positive if **Incoming**), $r$ is the
rate per period, $n$ is the number of periods, and $w$ is 1 for payments at
**Period Start** or 0 for payments at **Period End**.

## Example

Using the default inputs — a Present Value of 100,000 (Outgoing), an
Interest Rate of 6% per year, a Duration of 5 years, a Periodic Payment of
1,000 (Outgoing) made monthly at the start of each month — the calculator
returns a **Future Value** of approximately 203,646.57, with **Cash Flow**
shown as **Incoming** (since both the initial deposit and the monthly
contributions were outgoing, the resulting balance is money you would
receive).

For comparison, making the same monthly payments at the end of each period
instead (**Payment When** = Period End) slightly reduces the result to
about 203,308.34, since each contribution then has slightly less time to
compound. Removing the periodic payments entirely (**Periodic Payment** =
0) leaves only the initial deposit compounding on its own, reducing the
**Future Value** to about 133,822.56.

## Important Assumptions and Interpretation

-   **Periodic Payment** is assumed to be a fixed, evenly spaced amount for every period; irregular contributions are not supported.
-   The **Interest Rate** is assumed constant for the entire **Duration**.
-   Getting **Present Value Direction** and **Periodic Payment Direction** right matters for interpreting **Cash Flow** correctly, even though **Future Value** itself is always reported as a positive number.
