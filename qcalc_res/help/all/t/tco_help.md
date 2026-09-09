# Total Cost of Ownership (TCO) Comparison

## Purpose

This calculator answers a common procurement question: **which supplier or
alternative actually costs the least once every cost over its useful life is
counted, not just the sticker price?** It is useful for anyone comparing
equipment, machinery, vehicles, or other capital purchases from two or more
suppliers - purchasing managers, engineers, and business owners weighing a
cheaper-to-buy option against a cheaper-to-run one.

You enter each supplier's costs - purchase price, freight, installation,
recurring operating and maintenance costs, financing, disposal, and residual
(resale) value - in a single table, one column per supplier. The calculator
discounts every cost to a common present value, adds them up into a **Total
Cost of Ownership (TCO)** per supplier, and identifies which supplier has the
lowest TCO.

## Background

### Why sticker price alone can be misleading

The supplier with the lowest purchase price is not always the cheapest
choice. A lower-priced machine can cost more over time if it uses more
energy, needs more maintenance, or has a lower resale value at the end of its
useful life. TCO analysis puts every cost - one-time and recurring - on the
same footing so alternatives can be compared fairly.

### Present value and discounting

A cost paid five years from now is worth less today than the same amount
paid today, because money received sooner could otherwise be invested. The
calculator converts every future cost (and the residual value received back
at the end of the analysis period) into today's money using the **Discount
Rate**, so the comparison reflects the time value of money rather than
simply adding up raw dollar amounts.

### Cost escalation

Operating and maintenance costs often rise over time due to inflation, wear,
or rising energy/labor prices. The **Cost Escalation Rate** lets you model
recurring costs (operating, maintenance, financing) growing by a fixed
percentage every year, rather than assuming they stay flat for the entire
analysis period.

## Inputs

### Cost Component Table

A table with one row per standard cost category and one column per
supplier (or alternative). The first column holds the cost category label;
each additional column is a supplier whose costs you are comparing. You can
compare any number of suppliers by adding or removing columns.

The calculator recognizes each row by matching a keyword in its label
(case-insensitive), so rows can be renamed, reworded, or reordered as long as
each retains its keyword:

- **Purchase** (e.g. "Purchase Price") - the upfront purchase price.
- **Freight** - shipping/delivery cost to get the item in place.
- **Installation** - one-time setup or commissioning cost.
- **Operating** (e.g. "Annual Operating Cost") - recurring yearly cost to run
  the item (for example energy or consumables).
- **Maintenance** (e.g. "Annual Maintenance") - recurring yearly upkeep cost.
- **Financing** (e.g. "Annual Financing Cost") - recurring yearly cost of
  financing the purchase (for example loan interest), if applicable.
- **Disposal** - a one-time cost paid at the end of the analysis period to
  retire or dispose of the item.
- **Residual** (e.g. "Residual Value") - the amount recovered (for example
  resale value) at the end of the analysis period. This is a benefit, not a
  cost, and is subtracted from the total.

**Purchase**, **Freight**, and **Installation** are treated as one-time costs
paid today (not discounted). **Operating**, **Maintenance**, and
**Financing** are treated as recurring costs paid every year for the whole
analysis period. **Disposal** and **Residual** are treated as one-time
amounts occurring at the end of the analysis period. Enter `0` for any row
that does not apply to a given supplier.

### Analysis Period

The number of years over which ownership costs are compared (for example
`5 yr`). A longer period gives more weight to recurring operating and
maintenance costs relative to the one-time purchase cost, and discounts the
residual value further into the future (reducing its present value). A
shorter period does the opposite, giving more weight to the upfront cost.

### Discount Rate

The annual rate used to convert future costs and the residual value into
today's money (for example `8 pct/yr`). A higher discount rate reduces the
present value of every future cost and of the residual value, which
generally favors the supplier with the lower purchase price over the
supplier with lower running costs. A lower discount rate does the opposite.

### Cost Escalation Rate

The annual rate at which **Operating**, **Maintenance**, and **Financing**
costs are assumed to grow each year (for example `0 pct/yr` for flat costs,
or `4 pct/yr` if you expect these costs to rise with inflation). It does not
apply to **Purchase**, **Freight**, **Installation**, **Disposal**, or
**Residual Value**, which are one-time amounts.

### Usage

The expected annual usage of the item, for example `2000 hr/yr`. This is
used only to compute the **Cost / Hour** result; it converts the Annualized
TCO into a cost per hour of use. If usage is left as zero, **Cost / Hour**
is left blank because it cannot be computed.

## Results

### TCO Comparison

A table with one column per supplier and one row per metric, described
below.

#### Initial Cost

**Purchase** + **Freight** + **Installation** for that supplier, paid today
(not discounted).

#### Operating Cost (PV), Maintenance Cost (PV), Financing Cost (PV)

The present value of that supplier's recurring annual cost over the whole
**Analysis Period**, discounted at the **Discount Rate** and, if set, grown
each year at the **Cost Escalation Rate**. Each is `0` if the corresponding
input row was `0`.

#### Disposal Cost (PV)

The present value of the one-time **Disposal** cost, assumed to be paid at
the end of the **Analysis Period** and discounted back to today.

#### Residual Value (PV)

The present value of the one-time **Residual Value** received at the end of
the **Analysis Period**, discounted back to today. This amount is a benefit
and is subtracted from, not added to, the total.

#### Total Cost of Ownership (TCO)

**Initial Cost** + **Operating Cost (PV)** + **Maintenance Cost (PV)** +
**Financing Cost (PV)** + **Disposal Cost (PV)** - **Residual Value (PV)**.
This is the main figure for comparing suppliers: the supplier with the
lowest TCO is the cheapest choice over the stated Analysis Period, given the
stated assumptions.

#### Annualized TCO

The Total Cost of Ownership expressed as an equivalent level (constant)
annual cost over the Analysis Period, using the Discount Rate. This makes it
easier to compare alternatives that might have different analysis periods,
or to compare against an annual budget.

#### Cost / Hour

**Annualized TCO** divided by **Usage** (converted to hours per year) - the
effective cost per hour of use. Blank if **Usage** is zero.

#### % vs Lowest TCO

How much higher that supplier's **Total Cost of Ownership** is compared to
the supplier with the lowest TCO, as a percentage. The lowest-TCO supplier
always shows `0`; every other supplier shows how much more expensive it is
in relative terms.

#### Rank

`Best` for the supplier with the lowest **Total Cost of Ownership**; `OK`
for every other supplier. This does not evaluate quality, risk, or
non-cost factors - only the computed TCO.

### Lowest TCO Supplier

The name of the supplier column with the lowest **Total Cost of Ownership**
- the single recommended answer to "which is cheapest overall?" under the
stated assumptions.

### Chart

A bar chart plotting each supplier's Total Cost of Ownership, for a quick
visual comparison alongside the table.

## Understanding the Calculation

For each supplier:

1. **Initial Cost** = Purchase + Freight + Installation (undiscounted).
2. Each recurring cost (Operating, Maintenance, Financing) is discounted as a
  growing annuity: if the annual cost is `C`, the discount rate is `r`, the
  escalation rate is `g`, and the analysis period is `n` years, its present
   value is

$$PV = C \times \dfrac{1 - \left(\dfrac{1+g}{1+r}\right)^n}{r - g}$$

&nbsp;&nbsp;&nbsp;&nbsp;(when `r` equals `g`, this simplifies to `PV = C
	imes n \div (1+r)`; when `g = 0` this is the standard flat annuity present
value formula.)
3. **Disposal Cost (PV)** and **Residual Value (PV)** are each discounted as
  a single amount received/paid at year `n`: `PV = \text{amount} \times
  (1+r)^{-n}`.
4. **Total Cost of Ownership** = Initial Cost + Operating PV + Maintenance PV
   + Financing PV + Disposal PV - Residual Value PV.
5. **Annualized TCO** = Total Cost of Ownership × capital recovery factor,
  where the capital recovery factor is `r \div \left(1 - (1+r)^{-n}\right)`
  (or `1 \div n` when the discount rate is `0`). This annualization uses
   only the Discount Rate, not the Cost Escalation Rate.
6. **Cost / Hour** = Annualized TCO ÷ Usage (in hours/year).

The supplier with the smallest **Total Cost of Ownership** is reported as
the **Lowest TCO Supplier** and marked `Best` in the **Rank** row; every
other supplier's **% vs Lowest TCO** shows how much more it costs in
percentage terms.

## Example

### Default comparison (5-year analysis period)

With the default table (Supplier A, B, and C) and default assumptions -
**Analysis Period** `5 yr`, **Discount Rate** `8 pct/yr`, **Cost Escalation
Rate** `0 pct/yr` - the calculator produces approximately:

| Metric | Supplier A | Supplier B | Supplier C |
|---|---|---|---|
| Initial Cost | 95,000 | 93,000 | 88,000 |
| Operating Cost (PV) | 23,956 | 35,934 | 29,945 |
| Maintenance Cost (PV) | 7,985 | 15,971 | 9,982 |
| Residual Value (PV) | 3,403 | 2,042 | 2,722 |
| **Total Cost of Ownership (TCO)** | **123,539** | **142,863** | **125,205** |
| % vs Lowest TCO | 0% | 15.6% | 1.3% |
| Rank | Best | OK | OK |

Supplier A has the highest **Initial Cost** (95,000) but the lowest
recurring costs, and ends up with the lowest **Total Cost of Ownership**
(123,539) - about 1.3% cheaper than Supplier C and 15.6% cheaper than
Supplier B. **Lowest TCO Supplier** reports "Supplier A".

### Changing the Analysis Period flips the winner

Supplier A and Supplier C are close competitors: Supplier A costs more
upfront but less to run, while Supplier C costs less upfront but more to
run. Shortening the **Analysis Period** to `3 yr` (leaving every other input
at its default) gives more weight to the upfront cost and less to the
recurring costs, since there are fewer years of operating and maintenance
cost to discount:

| Metric | Supplier A | Supplier B | Supplier C |
|---|---|---|---|
| Initial Cost | 95,000 | 93,000 | 88,000 |
| Operating Cost (PV) | 15,463 | 23,194 | 19,328 |
| Maintenance Cost (PV) | 5,154 | 10,308 | 6,443 |
| Residual Value (PV) | 3,969 | 2,381 | 3,175 |
| **Total Cost of Ownership (TCO)** | **111,648** | **124,121** | **110,596** |
| % vs Lowest TCO | 0.95% | 12.2% | 0% |
| Rank | OK | OK | Best |

With only 3 years to recover its lower running costs, Supplier A's TCO
(111,648) is now slightly higher than Supplier C's (110,596), and **Lowest
TCO Supplier** switches to "Supplier C". This shows how the same cost data
can point to a different "cheapest" supplier depending on how long you plan
to keep the asset - a short ownership period favors the low-upfront-cost
supplier, while a longer one favors the low-running-cost supplier. The same
kind of flip can happen by raising the **Discount Rate** instead, since a
higher rate also reduces the weight given to future recurring costs.

## Important Assumptions and Interpretation

- The comparison only reflects the cost rows you provide. Costs left at `0`
  (for example Financing or Disposal in the default table) are simply
  excluded from that supplier's total; the calculator does not estimate or
  infer missing costs.
- **Operating**, **Maintenance**, and **Financing** costs are assumed to
  occur every year for the entire Analysis Period and, if a Cost Escalation
  Rate is set, to grow by that same fixed rate every year - actual future
  costs may vary from this simplified pattern.
- **Disposal** and **Residual Value** are assumed to occur in a single lump
  sum at the very end of the Analysis Period, not gradually.
- The result identifies the supplier with the lowest calculated cost under
  the stated assumptions - it does not account for quality, reliability,
  delivery risk, warranty terms, or other non-cost factors that may also
  matter in a purchasing decision.
- This is a financial estimate that depends heavily on the accuracy of the
  cost inputs and the chosen Discount Rate and Cost Escalation Rate; treat
  results as a decision aid rather than a guaranteed outcome, and revisit the
  comparison if any of these assumptions change materially.
