# Amortization Schedule Calculation

## Purpose

This calculator produces a month-by-month repayment schedule for a
fixed-rate loan, showing how each payment splits between interest and
principal, how the loan balance declines over time, and the running totals
paid. It is useful for anyone planning or reviewing a mortgage, auto loan,
or other installment loan who wants to see exactly how the debt is paid
off.

## Background

### How a fixed-rate loan is repaid

A standard amortizing loan charges a fixed **Monthly Payment** for the
entire term. Each payment first covers the interest owed on the
**Remaining Principal** for that month; whatever is left over reduces the
principal itself. Early in the loan, most of each payment goes to
interest, because the outstanding balance is largest then. As the balance
shrinks, less of each payment goes to interest and more goes to principal,
even though the payment amount itself never changes.

## Inputs

### Loan Amount

The total amount borrowed at the start of the loan.

### Annual Interest Rate

The loan's nominal annual interest rate, entered as a percentage (for
example, `5.0` for 5%). It is converted internally to a monthly rate by
dividing by 12.

### Loan Term Years

The number of years over which the loan is repaid. Together with 12
monthly payments per year, this determines the total number of payments.

## Results

### Amortization Schedule

A table with one row per monthly payment, from **Payment Number** 1 through
the total number of payments (Loan Term Years × 12):

-   **Payment Number** — the sequence number of the payment.
-   **Monthly Payment** — the fixed amount paid every month; it is the same
    on every row.
-   **Principal Payment** — the portion of that month's payment that
    reduces the loan balance.
-   **Interest Payment** — the portion of that month's payment that covers
    interest on the remaining balance; it shrinks from row to row as the
    balance declines.
-   **Total Principal** — the cumulative principal paid from Payment 1
    through this row.
-   **Total Interest** — the cumulative interest paid from Payment 1
    through this row.
-   **Total Payment** — Total Principal plus Total Interest, the cumulative
    amount paid so far.
-   **Remaining Principal** — the loan balance still owed after this
    payment; it reaches (approximately) zero on the final row.

### Amortization Chart

A line chart plotting **Total Principal**, **Total Interest**, **Total
Payment**, and **Remaining Principal** against the payment number, so you
can see at a glance how cumulative payments grow and the balance declines
over the life of the loan.

## Understanding the Calculation

The monthly interest rate is the **Annual Interest Rate** divided by 12
(and by 100 to convert from a percentage). The number of payments is
**Loan Term Years** × 12. The fixed **Monthly Payment** is calculated with
the standard amortization formula so that exactly this many equal payments
pay off the **Loan Amount** in full, including all interest:

$$\text{Monthly Payment} = \dfrac{\text{Loan Amount} \times r}{1 - (1+r)^{-n}}$$

where $r$ is the monthly interest rate and $n$ is the number of payments.

For each payment, in order: **Interest Payment** = Remaining Principal ×
monthly rate; **Principal Payment** = Monthly Payment − Interest Payment;
**Remaining Principal** is then reduced by that **Principal Payment** before
moving to the next row.

## Example

Using the default inputs — a Loan Amount of 100,000, an Annual Interest
Rate of 5.0%, and a Loan Term of 10 years (120 monthly payments) — the
calculator finds a fixed **Monthly Payment** of 1,060.66 for every payment.
The schedule shows, for example:

-   **Payment 1**: Interest Payment 416.67, Principal Payment 643.99,
    Remaining Principal 99,356.01.
-   **Payment 3**: Total Interest 1,241.94, Total Principal 1,940.03,
    Remaining Principal 98,059.97.
-   **Payment 120** (the final payment): Principal Payment 1,056.25,
    Interest Payment 4.40, Total Principal 100,000.00, Total Interest
    27,278.62, Total Payment 127,278.62, Remaining Principal effectively 0.

This shows that over the life of the loan, total interest paid (27,278.62)
adds about 27% on top of the original 100,000 borrowed, and that the split
between principal and interest shifts steadily toward principal as the
balance is paid down.

## Important Assumptions and Interpretation

-   The loan is assumed to be fixed-rate, with equal monthly payments and
    no extra payments, fees, insurance, or taxes included.
-   Interest is assumed to compound and accrue monthly on the remaining
    principal only, using the annual rate divided evenly by 12.
-   Rounding to two decimal places in the schedule and chart values means
    the very last row's **Remaining Principal** may show as a small
    residual (for example, `-0.00`) rather than exactly zero.
-   Results assume the interest rate and payment amount stay constant for
    the entire term; they do not reflect adjustable-rate loans, refinancing,
    or prepayments.
