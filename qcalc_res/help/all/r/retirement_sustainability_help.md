# Retirement Withdrawal Sustainability

## Purpose

The **Retirement Withdrawal Sustainability** calculator estimates how a portfolio changes while supporting inflation-adjusted withdrawals over a selected retirement period.

It can model annual, monthly, or another supported withdrawal interval. It also distinguishes withdrawals made at the **start** of a period from those made at the **end**. This matters because money withdrawn earlier does not remain invested for that period.

The calculator is a deterministic scenario projection, not a forecast or a guarantee of retirement income.

## Background

Investment returns and inflation are supplied as rates for a larger time unit, normally a year. The calculator converts them to the selected withdrawal period using compound-rate conversion. For example, an effective annual rate is converted to an effective monthly rate before a monthly projection is run.

The withdrawal amount is increased by the converted inflation rate after the first period. Thus, a monthly scenario increases the withdrawal monthly, while an annual scenario increases it annually.

## Inputs

### Portfolio

The starting portfolio value, including its currency. The portfolio currency becomes the currency used for monetary results and projection values.

Example: `500000 USD`.

### Withdrawal

The initial withdrawal amount. Its rate unit should correspond to the selected **Withdrawal Period**, such as `30000 USD/yr` or `2500 USD/mo`. The calculator converts the amount to the portfolio currency per selected period.

The withdrawal is increased for inflation after the first period.

### Investment Return

The expected investment return before investment tax. The rate may be entered with a time unit, such as `7 pct/yr`.

The supplied rate is converted to a compound effective rate for the selected withdrawal period. It is not divided by the number of periods as a simple-rate approximation.

### Inflation

The expected inflation rate, such as `3 pct/yr`. It is converted to the selected withdrawal period and used to increase each later withdrawal.

### Investment Tax

The percentage of each calculated investment gain treated as tax. For example, `15 pct` means that 15% of the period's gross investment gain is removed as tax.

### Retirement Period

The total duration of the projection, such as `30 yr`. It is converted to the number of selected withdrawal periods and rounded to a whole number of periods.

### Withdrawal Period

The interval between withdrawals, such as `yr` or `mo`. This interval controls the periodic rate conversion, inflation adjustment, number of projection rows, and units of withdrawal-related results.

### Withdrawal When

Choose one of the dropdown values:

- `start`: withdraw at the beginning of each period, before that period's investment return.
- `end`: withdraw at the end of each period, after that period's investment return.

The default is `end`.

## Results

### After-Tax Return

The investment return for the selected withdrawal period after applying the investment tax rate. For example, an annual 7% return with 15% tax produces a 5.95% annual after-tax rate; the displayed unit changes to `pct/mo` in a monthly scenario.

### Initial Withdrawal Rate

The initial withdrawal expressed as a percentage of the starting portfolio:

$$
\text{Initial Withdrawal Rate} =
\frac{\text{Initial Withdrawal}}{\text{Portfolio}} \times 100
$$

It uses the initial withdrawal before later inflation adjustments.

### Sustainable Withdrawal

The estimated initial withdrawal per selected period that reduces the modeled portfolio to zero at the end of the full projection, assuming the supplied return, tax, inflation, interval, and timing assumptions.

The result uses the selected currency and period. For example, a monthly scenario returns a value in `USD/mo` when the portfolio is entered in USD.

This is a model-based benchmark, not a recommended withdrawal amount.

### Final Balance

The portfolio balance after the simulated periods. A positive value remains in the modeled portfolio. A zero value means the portfolio was depleted during the projection; balances are not allowed to become negative.

### Depletion Period

The quantity in the selected withdrawal period unit in which the simulated balance reaches zero. For example, a yearly withdrawal model may report `5 yr`. No depletion period is reported when the balance remains positive through the requested projection.

A comparison metric, `Depletion Period (0% Return, 0% Inflation)`, is also included to show the simple baseline case where the portfolio earns no return and inflation is zero. In that case, the depletion period is the straightforward portfolio/withdrawal ratio expressed in the same withdrawal period unit.

### Projection and Chart

The projection table and chart use one row or plotted point per selected withdrawal period.

| Column | Description |
|---|---|
| Period | Sequential period number, beginning at 1 |
| Starting Balance | Portfolio value at the beginning of the period |
| Investment Return | Gross investment gain for the period |
| Investment Tax | Tax removed from that gross gain |
| Withdrawal | Inflation-adjusted withdrawal for the period |
| Ending Balance | Balance after the period's return, tax, and withdrawal |

The chart shows **Starting Balance** and **Ending Balance** against **Period**.

## Understanding the Calculation

Let:

- `P` be the initial portfolio value.
- `W_0` be the initial withdrawal per selected period.
- `j` be the zero-based period index, where the first period is `j=0`.
- `n` be the total number of selected periods.
- `r_g` be the compound gross investment return per selected period.
- `i` be the compound inflation rate per selected period.
- `t` be the investment tax rate.
- `r` be the after-tax investment return per selected period.

The number of periods is calculated from the retirement duration and the selected withdrawal period, then rounded to a whole number:

$$
n = \operatorname{round}\left(
\frac{\text{Retirement Period}}{\text{Withdrawal Period}}
\right)
$$

The withdrawal in period `j` is:

$$
W_j = W_0(1+i)^j
$$

Thus, the first withdrawal is `W_0`, the second is `W_0(1+i)`, and so on.

### Periodic Rate Conversion

The supplied investment return and inflation rate are converted to the selected period as compound effective rates. If an effective annual rate is converted to `m` periods per year:

$$
r_{g,p} = (1+r_{g,y})^{1/m}-1
$$

For example, an annual investment return of 7% converted to monthly periods uses:

$$
r_{g,m} = (1+0.07)^{1/12}-1
$$

The same conversion is applied to inflation. The calculator does not use the simple approximation `r_y/12` for monthly compounding.

### Investment Tax and After-Tax Return

For each period, tax is calculated from that period's gross investment gain:

$$
G_j = B_{\text{invested},j}r_g
$$

$$
T_j = G_jt
$$

The after-tax gain is:

$$
G_{\text{after tax},j} = G_j - T_j
$$

Therefore, the periodic after-tax return used by the sustainable-withdrawal formula is:

$$
r = r_g(1-t)
$$

### Start-of-Period Withdrawal

When `withdrawal_when` is `start`, the withdrawal is made before investment growth:

$$
B_{\text{invested},j} = B_{\text{start},j} - W_j
$$

$$
B_{\text{end},j} =
B_{\text{invested},j} +
B_{\text{invested},j}r_g(1-t)
$$

Equivalently:

$$
B_{\text{end},j} =
(B_{\text{start},j}-W_j)(1+r)
$$

### End-of-Period Withdrawal

When `withdrawal_when` is `end`, the full starting balance remains invested during the period. The withdrawal is made after investment growth:

$$
B_{\text{invested},j} = B_{\text{start},j}
$$

$$
B_{\text{end},j} =
B_{\text{start},j} +
B_{\text{start},j}r_g(1-t) - W_j
$$

Equivalently:

$$
B_{\text{end},j} =
B_{\text{start},j}(1+r)-W_j
$$

After each period, a negative ending balance is replaced by zero. Once the balance reaches zero, the projection stops and reports that period as **Depletion Period**.

## Sustainable Withdrawal Calculation

The sustainable withdrawal is the value of `W_0` that makes the present value of all modeled withdrawals equal to the starting portfolio `P`. If `i` is periodic inflation, `r` is the periodic after-tax return, and `n` is the number of periods, the initial sustainable withdrawal is:

For end-of-period withdrawals:

$$
W_0 =
\frac{P}
{\displaystyle\sum_{k=0}^{n-1}
\frac{(1+i)^k}{(1+r)^{k+1}}}
$$

The first end-of-period withdrawal is discounted by one period, the second by two periods, and the final withdrawal by `n` periods.

For start-of-period withdrawals:

$$
W_0 =
\frac{P}
{\displaystyle\sum_{k=0}^{n-1}
\frac{(1+i)^k}{(1+r)^k}}
$$

The first start-of-period withdrawal is not discounted because it is made immediately. The later withdrawals are discounted by the number of periods that remain after each withdrawal.

The start-of-period result is normally lower than the end-of-period result under the same other assumptions because each withdrawal occurs before that period's investment return.

## Example

Using the defaults:

- Portfolio: `500000 USD`
- Withdrawal: `30000 USD/yr`
- Investment Return: `7 pct/yr`
- Inflation: `3 pct/yr`
- Investment Tax: `15 pct`
- Retirement Period: `30 yr`
- Withdrawal Period: `yr`
- Withdrawal When: `end`

The periodic after-tax return is 5.95% per year. The projection makes one withdrawal at the end of each year and increases later withdrawals by the 3% annual inflation rate. The sustainable-withdrawal result is the modeled first annual withdrawal that would exhaust the portfolio at the end of the 30-year scenario.

Changing **Withdrawal Period** to `mo` and entering an equivalent monthly withdrawal does not produce exactly the same projection as an annual scenario: the return and inflation are compounded monthly, and the cash leaves the portfolio at monthly dates. Changing **Withdrawal When** to `start` also reduces the amount of time each withdrawal remains invested.

## Important Assumptions and Interpretation

- Investment returns are constant for every selected period.
- Inflation is constant and compounds at the selected period.
- The supplied investment and inflation rates are converted as effective compound rates, not simple division by the number of periods.
- Tax is applied to each period's calculated investment gain.
- Withdrawals increase only from the second period onward.
- The model uses a fixed withdrawal schedule and does not simulate random market returns or sequence-of-returns risk.
- A depleted balance is capped at zero; the model does not represent debt or overdrafts after depletion.
- Fees, transaction costs, pensions, Social Security, other income, and additional contributions are not included.
- The tax calculation is a simplified scenario assumption and does not model a particular country's tax rules, tax lots, deductions, or tax-free accounts.
- Actual returns, inflation, taxes, and spending needs can differ from the assumptions, so the result should be treated as an estimate rather than a guarantee or individualized financial advice.
