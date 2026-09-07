# Finance Calculator Helper

## Purpose

This tool does not calculate a financial result itself — it helps you find
the **right qCalc calculator** to use for a time-value-of-money problem. You
tell it what you want to solve for (for example, an interest rate) and
which values you already know (for example, a present value, a future
value, and a duration); it then recommends the best-matching calculator(s)
from the finance catalog, ranked by how well your known values fit each
one's inputs, with a button to add the recommended calculator directly.

## Background

### Many calculators, one relationship

qCalc's finance section has several related calculators — for present
value, future value, interest rate, number of periods, payments, bond
pricing, and rate-of-return problems — each built around the same
underlying time-value-of-money relationship, but expecting a different
combination of known and unknown values. Rather than requiring you to know
which specific calculator fits your situation, this helper matches your
stated unknown against the calculators that can solve for it, and ranks
them by how many of your known values they actually use.

## Inputs

### Unknown Parameter (what you want to find)

Choose the single value you want to calculate: **Present Value**, **Future
Value**, **Interest Rate**, **Number of Periods**, or **Periodic Payment**.

### Known Parameters (what you already have)

Check every value you already know from: **Present Value**, **Future
Value**, **Interest Rate**, **Interest Interval**, **Reinvestment Rate**,
**Duration**, **Periodic Payment**, **Payment Interval**, **Payment When**,
and **Loan Amount**. Select as many as apply to your situation — the more
you check, the better the helper can distinguish between similar
calculators.

## Results

### Recommend

A ranked list of buttons, each linking to a calculator whose output matches
your chosen **Unknown Parameter**. The calculator using the most of your
checked **Known Parameters** is listed first; calculators that use fewer of
your known values follow. Click a button to add that calculator to your
workspace and continue with the actual calculation there. If no calculator
in the catalog solves for the chosen **Unknown Parameter**, the helper
reports that no calculator was found.

## Understanding the Calculation

For each calculator in the finance catalog, the helper knows which single
value it solves for and which set of inputs it uses. It filters the
catalog down to only the calculators whose solved-for value matches your
**Unknown Parameter**, then counts, for each of those, how many of your
checked **Known Parameters** overlap with that calculator's actual inputs.
The results are sorted with the highest overlap count first. When two or
more calculators tie on overlap count, their relative order is not
significant.

## Example

Choosing **Interest Rate** as the Unknown Parameter, and checking
**Present Value**, **Future Value**, **Duration**, **Periodic Payment**,
and **Payment Interval** as Known Parameters, the helper recommends, in
order:

1.  **Compound Interest Rate with Periodic Payment** (uses all 5 of the
    checked values)
2.  **Compound Interest Rate without Periodic Payment** (uses 3 of the
    checked values — present value, future value, and duration)
3.  **Modified Internal Rate of Return (IRRM)** and **Internal Rate of
    Return (IRR)** (use none of the checked values — they instead expect a
    cash-flow table)

This shows the helper correctly favors the calculator built around exactly
the inputs available (periodic payments included), while still listing the
other rate calculators as lower-priority alternatives.

## Important Assumptions and Interpretation

-   This helper only recommends a calculator — it does not itself produce
    a present value, future value, rate, payment, or period count. Open the
    recommended calculator to enter your full inputs and get an actual
    result.
-   A high match count means the recommended calculator's inputs align
    with what you know; it does not by itself guarantee that calculator is
    the right model for your specific financial situation (for example,
    whether a loan, an investment stream, or a cash-flow schedule best
    describes your case).
-   If your desired unknown is not offered as a choice, or no match is
    found, review whether the value you want is actually produced by one of
    the other finance calculators in the catalog directly.
