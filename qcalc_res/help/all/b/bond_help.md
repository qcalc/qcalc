# Bond Pricing

## Purpose

This calculator estimates the fair price of a bond today, given its face
value, its coupon rate, how often it pays interest, how long until it
matures, and the prevailing market interest rate. It is useful for
investors and analysts who want to know what a bond is worth based on
discounting its future coupon payments and final repayment at a current
market rate.

## Background

### Why a bond's price can differ from its face value

A bond promises to pay a series of fixed coupon payments and then repay its
**Face Value** at maturity. Its price today is the present value of those
future payments, discounted at the prevailing **Interest Rate** for a bond
of similar risk and maturity. When the **Coupon Rate** equals the
**Interest Rate**, the bond prices at (or very near) its face value. When
the **Coupon Rate** is higher than the **Interest Rate**, the bond is worth
more than its face value (it trades at a premium), because it pays more
than the market currently requires. When the **Coupon Rate** is lower than
the **Interest Rate**, the bond is worth less than face value (it trades at
a discount).

## Inputs

### Face Value

The amount the bond repays at maturity, and the amount its coupon payments
are calculated on.

### Coupon Rate

The bond's stated annual interest rate, used to calculate each coupon
payment. Enter it as a rate per year (for example, `5 pct/yr`).

### Interest Payment Interval

How often coupon payments are made — for example, every half year, quarter,
or year. This determines both the size of each coupon payment (the annual
**Coupon Rate** is applied proportionally to the length of the interval)
and how many payments occur before maturity.

### Duration

The time remaining until the bond matures, entered with a time unit (for
example, `2 yr`). Together with **Interest Payment Interval**, this
determines the total number of coupon payments.

### Interest Rate

The prevailing annual market interest rate used to discount the bond's
future payments back to today's value. Like **Coupon Rate**, it is entered
as a rate per year and applied proportionally to each payment interval.

## Results

### Bond Price

The estimated fair price of the bond today: the present value of all coupon
payments plus the present value of the face value repaid at maturity,
discounted at the **Interest Rate**. Compare this to the **Face Value** to
see whether the bond prices at a premium (Bond Price above Face Value),
at a discount (Bond Price below Face Value), or at par (Bond Price close to
Face Value).

## Understanding the Calculation

The annual **Coupon Rate** and **Interest Rate** are each converted to a
per-period rate by multiplying by the length of one **Interest Payment
Interval** (for example, an annual rate applied over a half-year interval
gives half the annual rate per period). The number of payment periods is
the **Duration** divided by the **Interest Payment Interval**.

For each period from 1 to the total number of periods, the coupon payment
(**Coupon Rate** per period × **Face Value**) is discounted back to today
using the per-period **Interest Rate**:

$$\text{Bond Price} = \sum_{i=1}^{n} \dfrac{\text{Coupon Rate} \times \text{Face Value}}{(1+\text{Interest Rate})^{i}} \;+\; \dfrac{\text{Face Value}}{(1+\text{Interest Rate})^{n}}$$

where both rates are per-period values and $n$ is the total number of
payment periods. The last term discounts the return of the **Face Value**
itself at maturity.

## Example

Using the default inputs — a Face Value of 1000, a Coupon Rate of 5% per
year, interest paid every half year, a Duration of 2 years (4 half-year
periods), and an Interest Rate of 3% per year — the calculator returns a
**Bond Price** of approximately 1038.54. Since the 5% Coupon Rate exceeds
the 3% Interest Rate, the bond is worth more than its 1000 Face Value — it
trades at a premium of about 38.54.

For comparison, if the Coupon Rate and Interest Rate are both set to 3%
(all other inputs unchanged), the Bond Price comes out to essentially 1000
— the bond prices at par, as expected when the coupon exactly matches the
market rate.

## Important Assumptions and Interpretation

-   The calculation assumes coupon payments are made exactly on schedule at
    the stated **Interest Payment Interval**, with no missed or irregular
    payments, and no default risk.
-   The **Interest Rate** used for discounting is assumed constant over the
    entire remaining **Duration**; it does not model a changing yield curve.
-   **Duration** should divide evenly by the **Interest Payment Interval**
    for a whole number of payment periods; check both inputs use consistent
    time units.
-   The result is an estimated fair price based on the inputs given, not a
    quoted market price, which can also be affected by liquidity, credit
    risk, and other market factors not modeled here.
