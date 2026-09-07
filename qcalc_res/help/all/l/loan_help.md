# Periodic Payment for a Loan

## Purpose

This calculator computes the fixed payment required each period to fully
repay a loan, along with the total amount paid over the life of the loan.
It is useful for quickly estimating a monthly (or other periodic)
installment for a mortgage, auto loan, or any loan repaid in equal
instalments.

## Background

### Amortizing a loan to zero

A standard loan is repaid with equal payments at the end of every period
until the balance reaches exactly zero. Each payment covers the interest
owed on the remaining balance for that period, with the rest reducing the
principal. This calculator finds the single fixed payment amount that
achieves that outcome over the stated **Number of Periods**, given the
**Loan Amount** and **Interest Rate**.

## Inputs

### Loan Amount

The total amount borrowed.

### Interest Rate

The loan's nominal interest rate, entered with a time basis (for example,
`6.0 pct/yr`). It is converted proportionally to match the time unit of
**Number of Periods** — for example, an annual rate is divided by 12 to
get a monthly rate. This is a simple proportional conversion, not a
compounding conversion, so entering the rate directly in the same time
unit as **Number of Periods** (for example, a monthly rate when periods
are months) gives the same result and avoids any ambiguity.

### Number of Periods

The total number of equal payments over which the loan is repaid (for
example, `12.0 mo`). Its time unit also determines how **Interest Rate**
is converted, as described above.

## Results

### Payment Per Period

The fixed amount to pay at the end of every period so the loan is fully
repaid, with interest, by the end of **Number of Periods**.

### Total Payment

**Payment Per Period** multiplied by **Number of Periods** — the total of
all payments over the life of the loan. It is always more than the
**Loan Amount**, with the difference being the total interest paid.

## Understanding the Calculation

The interest rate is first expressed as a rate per period matching the
time unit of **Number of Periods**. The required periodic payment is then:

$$\text{Payment Per Period} = \dfrac{r \times \text{Loan Amount}}{1 - (1+r)^{-n}}$$

where $r$ is the interest rate per period and $n$ is the **Number of
Periods**. This is the standard loan amortization formula — the fixed
payment whose repeated application, with interest charged on the declining
balance, brings the balance to exactly zero after $n$ payments.

## Example

Using the default inputs — a Loan Amount of 100,000, an Interest Rate of
6.0% per year, and 12.0 monthly periods — the calculator converts 6% per
year to 0.5% per month, and returns a **Payment Per Period** of
approximately 8,606.64 (per month) and a **Total Payment** of
approximately 103,279.72. The gap between the Total Payment and the
100,000 borrowed — about 3,279.72 — is the total interest paid over the
year.

## Important Assumptions and Interpretation

-   **Payment Per Period** is assumed to be made at the end of each
    period, a fixed and evenly spaced amount, with no missed or extra
    payments.
-   **Interest Rate** is assumed constant across every period; this is a
    fixed-rate loan calculation, not an adjustable-rate one.
-   Because the rate conversion to match **Number of Periods** is a simple
    proportional split rather than a compounding-equivalent conversion,
    for the clearest results enter **Interest Rate** already in the same
    time unit as **Number of Periods** (for example, a monthly rate for
    monthly periods) if you want to avoid any approximation from the
    conversion step.
-   The result does not include fees, insurance, taxes, or prepayments —
    it reflects only principal and interest on the stated terms.
