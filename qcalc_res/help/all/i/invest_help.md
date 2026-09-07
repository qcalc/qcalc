# Periodic Payment for a Future Cash

## Purpose

This calculator answers a savings-goal question: **how much do I need to
set aside every period to reach a target amount by a future date**, given
an expected interest rate? It is useful for planning contributions toward a
future goal — such as a down payment, a large purchase, or a sinking fund —
when you know the target amount, the rate you expect to earn, and how long
you have.

## Background

### Saving toward a target (a sinking fund)

Instead of starting with a lump sum and letting it grow, this calculator
assumes you contribute an equal amount every period, and each contribution
earns interest from the time it is made until the target date. It solves
for the contribution size that makes the accumulated value — contributions
plus the interest they earn — equal exactly the **Future Value** you want,
after the stated **Number of Periods**.

## Inputs

### Future Value

The target amount you want to have accumulated by the end of the period.

### Interest Rate

The interest rate your contributions are expected to earn, entered with a
time basis (for example, `6.0 pct/yr`). It is converted proportionally to
match the time unit of **Number of Periods** — for example, an annual rate
is divided by 12 to get a monthly rate. This is a simple proportional
conversion, not a compounding conversion, so entering the rate directly in
the same time unit as **Number of Periods** (for example, a monthly rate
when periods are months) gives the same result and avoids any ambiguity.

### Number of Periods

How many equal contribution periods there are until the **Future Value**
is needed (for example, `12.0 mo`). Its time unit also determines how
**Interest Rate** is converted, as described above.

## Results

### Payment Per Period

The fixed amount to contribute at the end of every period so that, with
interest, the contributions grow to exactly the **Future Value** by the end
of **Number of Periods**.

### Total Payment

**Payment Per Period** multiplied by **Number of Periods** — the sum of all
contributions before counting the interest they earn. It is always less
than the **Future Value**, with the difference being the interest earned
over the periods.

## Understanding the Calculation

The interest rate is first expressed as a rate per period matching the time
unit of **Number of Periods**. The required periodic contribution is then:

$$\text{Payment Per Period} = \dfrac{r \times FV}{(1+r)^{n} - 1}$$

where $r$ is the interest rate per period, $FV$ is the **Future Value**, and
$n$ is the **Number of Periods**. This is the standard sinking-fund payment
formula — the amount whose repeated deposits, compounding each period,
exactly reach $FV$ after $n$ periods.

## Example

Using the default inputs — a Future Value of 100,000, an Interest Rate of
6.0% per year, and 12.0 months of contributions — the calculator converts
6% per year to 0.5% per month, and returns a **Payment Per Period** of
approximately 8,106.64 (per month) and a **Total Payment** of approximately
97,279.72. The gap between the Total Payment and the 100,000 Future Value
— about 2,720.28 — is the interest earned on the contributions over the
year.

## Important Assumptions and Interpretation

-   **Payment Per Period** is assumed to be made at the end of each period,
    a fixed and evenly spaced amount, with no missed or irregular
    contributions.
-   **Interest Rate** is assumed constant across every period.
-   Because the rate conversion to match **Number of Periods** is a simple
    proportional split rather than a compounding-equivalent conversion,
    for the clearest results enter **Interest Rate** already in the same
    time unit as **Number of Periods** (for example, a monthly rate for
    monthly periods) if you want to avoid any approximation from the
    conversion step.
-   The result is a savings plan estimate based on a constant assumed rate;
    actual investment returns will vary.
