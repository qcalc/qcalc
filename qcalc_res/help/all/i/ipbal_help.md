# Interest for Periodic Balance

## Purpose

This calculator computes the interest earned or charged on an account
whose balance changes over time as deposits and withdrawals occur — the
same kind of day-by-day balance calculation banks use to reconcile
interest on a running account. It is useful for reconciling a bank
statement, checking interest charged on an overdrawn account, or verifying
interest credited on a savings account with fluctuating balances.

## Background

### Interest on a changing balance

Rather than applying one rate to a single average balance, this calculator
tracks the balance after every deposit or withdrawal and charges or credits
interest for exactly the number of days that balance was held before the
next transaction. A positive balance earns credit interest at the
**Credit Interest Rate**; a negative (overdrawn) balance is charged debit
interest at the **Debit Interest Rate**. Adding these up across every
transaction in the statement gives the total interest for the period.

## Inputs

### CSV File

A transaction file (uploaded, or given as a URL) with one row per
transaction, in three columns:

-   **Date** — the transaction date, in the format given by **Date
    Format** (by default, day-abbreviated month-2-digit year, for example
    `20-Jan-23`).
-   **Deposit** — the amount deposited on that date, left blank if the
    transaction is a withdrawal.
-   **Withdrawl** — the amount withdrawn on that date, left blank if the
    transaction is a deposit.

Rows should be listed in date order, since the balance and interest are
calculated by walking through the rows in the order given.

### Initial Balance

The account balance immediately before the first transaction in the CSV
file.

### Debit Interest Rate

The annual interest rate charged when the running balance is negative
(overdrawn), entered as an annual percentage (for example, `9.0`).

### Credit Interest Rate

The annual interest rate credited when the running balance is positive,
entered as an annual percentage (for example, `3.0`).

### Date Format

The date format used to read the **Date** column (for example,
`%d-%b-%y` for `20-Jan-23`). Change this to match the format of your own
CSV file if it differs from the default. Some common formats:

| Date Format   | Example       |
|---------------|---------------|
| `%d-%b-%y`    | `20-Jan-23`   |
| `%d-%b-%Y`    | `20-Jan-2023` |
| `%d/%m/%Y`    | `20/01/2023`  |
| `%m/%d/%Y`    | `01/20/2023`  |
| `%Y-%m-%d`    | `2023-01-20`  |
| `%d %B %Y`    | `20 January 2023` |

## Results

### Total DR Interest

The total debit interest charged across the whole statement — the sum of
interest accrued on every day the balance was negative. This is 0 if the
balance never goes negative.

### Total CR Interest

The total credit interest earned across the whole statement — the sum of
interest accrued on every day the balance was positive. This is 0 if the
balance never goes positive.

### Total Interest Earned

**Total CR Interest** minus **Total DR Interest** — the net interest for
the period. A positive value means the account earned more credit interest
than it was charged in debit interest overall.

### Calculation

A detailed table with one row per transaction, adding these columns to the
original **Date**, **Deposit**, and **Withdrawl**:

-   **Balance** — the running balance immediately after that transaction.
-   **Days** — the number of days that balance was held before the next
    transaction (0 for the last row, since there is no following
    transaction to measure against).
-   **DR Interest** — the debit interest accrued during those **Days**, if
    the **Balance** was negative; otherwise 0.
-   **CR Interest** — the credit interest accrued during those **Days**, if
    the **Balance** was positive; otherwise 0.

## Understanding the Calculation

For each transaction row, in order: the **Balance** is updated by adding
that row's **Deposit** and subtracting its **Withdrawl**. The **Days**
value is the number of calendar days until the next transaction's
**Date** (0 for the final row). Interest for that row is then:

$$\text{Interest} = \dfrac{|\text{Balance}| \times \text{Days} \times \text{Rate}}{36{,}500}$$

using the **Debit Interest Rate** if the **Balance** is negative, or the
**Credit Interest Rate** if positive (dividing by 36,500 applies the
annual percentage rate over a 365-day year). **Total DR Interest** and
**Total CR Interest** are the sums of these amounts down the whole table,
and **Total Interest Earned** is their difference.

## Example

Using the default demo CSV — starting from an Initial Balance of 0, a
first deposit of 17,000 on 1-Jan-23, followed by a series of further
deposits and withdrawals through 30-Jun-23, with a Debit Interest Rate of
9.0% and a Credit Interest Rate of 3.0% — the balance stays positive
throughout the period. The result is:

-   **Total DR Interest**: 0.00 (the balance never went negative)
-   **Total CR Interest**: 172.58
-   **Total Interest Earned**: 172.58

The **Calculation** table shows, for example, a balance of 17,000.00 held
for 19 days after the first deposit, earning 26.55 in credit interest for
that stretch, before the next transaction on 20-Jan-23 changes the balance.

## Important Assumptions and Interpretation

-   The last row's **Days** is always 0, so no interest is calculated on
    the balance for the time after the final listed transaction — include
    a final row (even with no deposit or withdrawal) dated at the end of
    your statement period if you want interest counted through that date.
-   Transaction rows must already be in date order; the calculator does not
    sort them for you.
-   Interest uses a 365-day year convention (dividing by 36,500) regardless
    of leap years.
-   This calculator reconciles interest based on the transactions provided;
    it does not verify that the CSV file is complete or accurate.
