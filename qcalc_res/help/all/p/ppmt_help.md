# Periodic Payment

## Purpose

This calculator solves for the fixed payment made at regular intervals that
reconciles a starting amount, a target ending amount, and an interest
rate — the same calculation behind loan installments, mortgage payments, or
regular contributions needed to reach a savings goal. It is useful whenever
you know the present and future amounts involved and need to find the
regular payment that connects them.

## Background

### One payment, many uses

The same formula answers very different questions depending on how you set
the inputs. Set **Future Value** to 0 and treat **Present Value** as money
you receive (a loan) to find a loan installment. Set **Present Value** to 0
and give a target **Future Value** to find the regular contribution needed
to reach a savings goal. Mixing a nonzero **Present Value** and **Future
Value** finds the payment needed to bridge between a starting and ending
amount over the **Duration**, at the given **Interest Rate**.

### Direction of cash flows

Both **Present Value** and **Future Value** are marked as either
**Incoming** (money you receive) or **Outgoing** (money you pay), using the
**Present Value Direction** and **Future Value Direction** settings. The
calculated **Periodic Payment** is always shown as a positive amount, with
a separate **Cash Flow** result telling you whether that payment is money
you would pay (**Outgoing**) or receive (**Incoming**), based on the
combined directions of what you entered.

## Inputs

### Present Value

The amount at the start of the **Duration**.

### Present Value Direction

Whether the **Present Value** is **Outgoing** (money you pay or invest) or
**Incoming** (money you receive, such as loan proceeds).

### Future Value

The amount at the end of the **Duration**.

### Future Value Direction

Whether the **Future Value** is **Incoming** (money you will receive) or
**Outgoing** (money you will owe or pay).

### Interest Rate

The annual nominal interest rate that applies throughout the **Duration**
(for example, `6 pct/yr`). It is converted internally to a rate per
**Payment Interval**.

### Duration

The total length of time from the **Present Value** to the **Future
Value** (for example, `5 yr`). Together with **Payment Interval**, this
determines the number of payments.

### Payment Interval

How often payments are made (for example, every month).

### Payment When

Whether each payment is made at the **Period Start** (an annuity due) or
the **Period End** (an ordinary annuity, the usual convention for loan
installments).

## Results

### Periodic Payment

The fixed amount to be paid or received at every **Payment Interval** that
reconciles the **Present Value** growing (or being paid down) to the
**Future Value** over the **Duration**, at the given **Interest Rate**.
Always shown as a positive amount.

### Cash Flow

States whether the **Periodic Payment** is money **Outgoing** (you would
pay it each period) or **Incoming** (you would receive it each period),
based on the combined direction of the **Present Value** and **Future
Value** you entered.

## Understanding the Calculation

The annual **Interest Rate** is converted to a rate per **Payment
Interval**, and the number of payments is **Duration** divided by
**Payment Interval**. The **Periodic Payment** is then the fixed payment
amount that satisfies the standard time-value-of-money relationship
linking a present value, a future value, and a series of equal payments,
given whether each payment falls at the start or end of its period
(**Payment When**). **Present Value** and **Future Value** are treated as
signed amounts (positive if **Incoming**, negative if **Outgoing**) when
solving for the payment.

## Example

Using the default inputs — a Present Value of 100,000 (Outgoing), a Future
Value of 200,000 (Incoming), an Interest Rate of 6% per year, a Duration of
5 years, paid monthly at the start of each month — the calculator finds a
**Periodic Payment** of approximately 928.64, with **Cash Flow** shown as
**Outgoing**.

As a loan example: borrowing 100,000 (Incoming to you) at 6% per year over
5 years, to be fully repaid (Future Value of 0) with equal payments at the
end of each month, gives a **Periodic Payment** of approximately 1,933.28,
shown as **Outgoing** — the familiar monthly installment for that loan.

## Important Assumptions and Interpretation

-   **Interest Rate** is assumed constant, and payments are assumed equal
    and evenly spaced, for the entire **Duration**.
-   Getting **Present Value Direction** and **Future Value Direction**
    right matters for interpreting **Cash Flow** correctly, even though
    **Periodic Payment** itself is always reported as a positive number.
-   The result is a calculated payment based on the assumed constant rate;
    it does not include fees, taxes, or changes to the rate over time.
