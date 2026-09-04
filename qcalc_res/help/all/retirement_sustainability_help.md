# Retirement Withdrawal Sustainability

## Overview

The **Retirement Withdrawal Sustainability** calculator estimates whether a retirement portfolio can support regular withdrawals over a chosen retirement period.

It accounts for:

- Investment returns
- Tax on investment returns
- Inflation
- Inflation-adjusted annual withdrawals
- Retirement duration

The calculator also estimates a sustainable initial annual withdrawal and provides a year-by-year portfolio projection.

## Inputs

### Portfolio

The starting value of the retirement portfolio.

The calculator uses the portfolio currency as the currency for all monetary results and for the projection table. If the portfolio is entered in EUR, for example, the withdrawal and all monetary outputs are also calculated in EUR.

### Withdrawal

The initial annual amount withdrawn from the portfolio.

The input is expressed as currency per year, such as `30000 USD/yr`.

The withdrawal increases each year according to the inflation rate.

### Investment Return

The expected annual investment return before tax.

For example, `7 pct/yr` means an expected annual return of 7%.

### Inflation

The expected annual inflation rate.

Inflation is used to increase the withdrawal amount each year so that the withdrawal maintains approximately the same purchasing power over time.

### Investment Tax

The tax rate applied to investment gains.

The calculator assumes that the specified percentage of the investment return is paid as tax.

### Retirement Period

The number of years over which the portfolio needs to support withdrawals.

For example, `30 yr` represents a 30-year retirement period.

## Results

### After-Tax Return

The investment return remaining after tax.

**After-Tax Return = Investment Return × (1 − Investment Tax Rate)**

For example, with a 7% investment return and a 15% tax rate, the after-tax return is 5.95%.

### Initial Withdrawal Rate

The first-year withdrawal expressed as a percentage of the starting portfolio.

**Initial Withdrawal Rate = Initial Annual Withdrawal ÷ Portfolio × 100**

This provides a quick indication of how large the initial withdrawal is relative to the portfolio.

### Sustainable Withdrawal

The estimated initial annual withdrawal that can be supported for the full retirement period, assuming the specified after-tax investment return and inflation rate.

The calculation treats withdrawals as an inflation-growing series, with the first withdrawal occurring in the first retirement year.

### Final Balance

The portfolio balance remaining at the end of the projection period.

A positive value means that the portfolio still has funds remaining after the projected withdrawals.

A zero value indicates that the portfolio has been depleted during the projection.

### Depletion Year

The year in which the portfolio reaches zero.

If the portfolio remains positive throughout the requested retirement period, no depletion year is reported.

## Projection

The projection table shows the portfolio year by year.

| Column | Description |
|---|---|
| Year | Retirement year |
| Starting Balance | Portfolio balance at the beginning of the year |
| Investment Return | Gross investment gain during the year |
| Investment Tax | Tax applied to the investment gain |
| Withdrawal | Inflation-adjusted annual withdrawal |
| Ending Balance | Portfolio balance after investment gain, tax, and withdrawal |

The calculator also provides a chart showing the **Starting Balance** and **Ending Balance** over the retirement period.

## How the Projection Works

For each year, the calculator:

1. Starts with the portfolio balance at the beginning of the year.
2. Calculates the gross investment gain.
3. Calculates tax on that investment gain.
4. Subtracts the investment tax from the gain.
5. Increases the withdrawal for inflation from the second year onward.
6. Subtracts the withdrawal from the portfolio.
7. Records the resulting ending balance.

The annual calculation can be represented as:

**Ending Balance = Starting Balance + After-Tax Investment Gain − Withdrawal**

where:

**After-Tax Investment Gain = Starting Balance × Investment Return × (1 − Investment Tax Rate)**

and the withdrawal grows with inflation:

**Withdrawal in Year n = Initial Withdrawal × (1 + Inflation Rate)ⁿ⁻¹**

## Sustainable Withdrawal Calculation

The sustainable withdrawal is calculated by treating the withdrawals as an annuity that grows with inflation.

The calculator first determines the after-tax investment return:

**After-Tax Return = Investment Return × (1 − Investment Tax Rate)**

The sustainable withdrawal is then determined from the present value of the inflation-adjusted withdrawals over the requested retirement period.

This means the sustainable withdrawal is not simply calculated by dividing the portfolio by the number of years. It considers both investment growth and the increasing withdrawals caused by inflation.

## Example

Suppose the inputs are:

- Portfolio: `500000 USD`
- Initial withdrawal: `30000 USD/yr`
- Investment return: 7% per year
- Inflation: 3% per year
- Investment tax: 15%
- Retirement period: 30 years

The calculator first reduces the 7% investment return for the 15% tax on investment gains, producing an after-tax return of 5.95%.

The initial withdrawal is `$30,000` per year. The withdrawal then increases by 3% each year to account for inflation.

The projection shows how the portfolio changes after investment growth, investment tax, and the inflation-adjusted withdrawal each year.

## Understanding Sustainability

A portfolio can be considered sustainable for the selected period when the projected balance remains above zero throughout the retirement period.

If the balance reaches zero before the end of the selected period, the reported depletion year indicates when the portfolio is exhausted.

The sustainable withdrawal result provides a useful benchmark for comparing the planned initial withdrawal with an estimated withdrawal that can be supported over the entire period under the selected assumptions.

## Important Assumptions

This calculator is a simplified projection and does not model all real-world retirement factors.

In particular:

- Investment returns are assumed to be constant each year.
- Inflation is assumed to be constant each year.
- Tax is applied to investment gains at the specified rate.
- Withdrawals increase annually with inflation.
- The calculation does not model investment volatility or sequence-of-returns risk.
- The tax treatment is simplified and does not represent a specific country's tax system.
- Fees, transaction costs, changing tax rates, pensions, Social Security, other income, and additional contributions are not included.

Because actual investment returns and inflation vary over time, the results should be treated as an estimate rather than a guarantee of retirement income.
