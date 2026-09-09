# Loan Prepayment Savings

## Purpose

This calculator estimates how much interest and repayment time you save by adding the same extra amount to every monthly loan payment.

## Background

A fixed-rate amortizing loan charges interest each month on the unpaid principal. Your regular scheduled payment first covers that month's interest, and the rest reduces the balance. An extra payment is applied entirely to principal after the regular payment, so later months begin with a smaller balance and accrue less interest.

Use `loan` calculator (**Periodic Payment for a Loan**) when you need to find the required payment for a loan amount, rate, and chosen payment interval. Use this calculator (`loan_prepay`) when you already have the original loan terms and want to compare the normal schedule with one that includes a recurring extra monthly principal payment. Unlike the periodic-payment calculator, this calculator reports the interest and payoff time saved; it is specifically monthly and does not model a one-time lump-sum prepayment.

## Inputs

### Loan Amount

The original principal borrowed. Its currency determines the currency used for the extra payment and all monetary results.

### Annual Interest Rate

The fixed nominal annual interest rate, such as `6 pct/yr`. The calculator divides it by 12 to find the monthly rate.

### Loan Term Years

The original repayment term in whole years. The normal scheduled monthly payment is calculated to repay the loan within this term.

### Extra Monthly Payment

The additional amount paid every month, alongside the scheduled payment. It is treated as extra principal; it does not replace part of the scheduled payment.

## Results

### Scheduled Monthly Payment

The required monthly payment under the original loan terms, before the extra payment is added.

### Original Total Interest and Prepayment Total Interest

The interest paid with the regular schedule and with the extra monthly payment, respectively.

### Interest Saved

The original total interest less the total interest after prepaying.

### Original Payoff Time, Prepayment Payoff Time, and Time Saved

The number of monthly payments in each scenario and the reduction in repayment time. Time Saved is also shown in years and remaining months.

## Understanding the Calculation

The scheduled payment is calculated from the standard amortizing-loan formula:

$$
\text{Scheduled Payment} = \frac{P r}{1 - (1 + r)^{-n}}
$$

where `P` is the loan amount, `r` is the monthly interest rate, and `n` is the original number of monthly payments. For each month, the calculator adds interest to the outstanding balance, subtracts the regular payment plus the extra payment, and repeats until the balance is zero. The final payment is limited to the amount actually owed.

For a 0% interest loan, the scheduled payment is simply the loan amount divided by the original number of months.

## Example

With the defaults of a 300,000 USD loan, 6% annual interest, a 30-year term, and an extra 200 USD each month, the scheduled payment is about 1,798.65 USD. The loan pays off in 279 months instead of 360 months, saving 81 months (6 years, 9 months) and about 91,173.43 USD in interest.

## Important Assumptions and Interpretation

- The interest rate and scheduled monthly payment remain fixed for the entire loan term.
- The extra amount is made every month from the first payment onward and is applied directly to principal.
- Payments are made at the end of each month; interest is calculated before that month's payment.
- The calculation excludes fees, taxes, insurance, penalties, escrow, rate changes, and lender-specific prepayment rules.
- This calculator models recurring extra payments. A one-time lump-sum prepayment may produce a different result depending on when it is made.