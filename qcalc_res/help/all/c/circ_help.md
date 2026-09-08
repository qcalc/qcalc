# Compound Interest Rate Conversion

## Purpose

This calculator converts a compound interest rate quoted for one time
period into the equivalent effective rate for a different time period —
for example, turning a 12% annual rate into its equivalent monthly rate,
or a monthly rate back into its equivalent annual rate. It is a general
conversion tool used throughout qCalc's finance calculators whenever a rate
needs to be restated in different time units without changing the actual
return it represents.

## Background

### Why you can't just divide by 12

A naive way to get a "monthly rate" from an annual rate is to divide by
12, but that understates true compounding: money growing at a genuine 12%
annual effective rate does **not** grow by exactly 1% every month, because
each month's growth itself earns further growth in later months. This
calculator finds the true equivalent periodic rate — the one that, when
compounded the right number of times, reproduces exactly the original
rate's effect over a year (or whatever the original period is). Converting
in either direction and back again reproduces the original rate.

## Inputs

### Interest Rate

The rate you already have, together with its time unit (for example,
`12 pct/yr` for 12% per year, or `0.95 pct/mo` for 0.95% per month).

### Interest Rate For

The time unit you want the equivalent rate expressed in (for example,
`mo` for monthly, `qrtr` for quarterly, or `yr` for annual).

## Results

### Periodic Interest Rate

The rate, in the units requested by **Interest Rate For**, that compounds
to exactly the same overall growth as the original **Interest Rate** over
its own period. For example, converting `12 pct/yr` to `mo` gives the
monthly rate that, compounded 12 times, produces exactly the same 12%
annual effective growth.

## Understanding the Calculation

The **Interest Rate** is first expressed as a decimal (for example, 12%
becomes 0.12). The calculator determines how many target periods
(**Interest Rate For**) fit within the original rate's own time unit (for
example, 12 months fit within a year), then solves for the periodic rate
$p$ that satisfies:

$$(1 + p)^{\text{periods}} = 1 + \text{Interest Rate (as a decimal)}$$

so that compounding the periodic rate the calculated number of times
exactly reproduces the original rate's total growth. This is the standard
effective-rate conversion used consistently by qCalc's other finance
calculators whenever a rate needs to be restated in different time units.

## Example

Converting an **Interest Rate** of 12% per year to a monthly rate (setting
**Interest Rate For** to `mo`) gives a **Periodic Interest Rate** of
approximately 0.949% per month — noticeably less than the naive 1% (12% ÷
12), because monthly compounding needs a slightly smaller rate to reach the
same 12% annual growth.

Converting back the other way — taking that same 0.949% per month rate and
setting **Interest Rate For** to `yr` — returns approximately 12% per year
again, confirming the two conversions are exact inverses of each other.
Converting a rate to its own existing time unit (for example, `12 pct/yr`
to `yr`) simply returns the same rate unchanged.

## Important Assumptions and Interpretation

-   The conversion assumes compounding occurs exactly at the frequency
    implied by **Interest Rate For**, with no additional fees or
    adjustments.
-   A rate of exactly 0% converts to 0% in any target time unit, as
    expected (there is no growth to compound in any period).
-   This calculator only re-expresses an existing rate in different time
    units — it does not itself calculate a present value, future value, or
    payment; use the dedicated calculators for those, which apply this same
    conversion internally wherever a rate needs to match a different
    payment or cash-flow interval.
