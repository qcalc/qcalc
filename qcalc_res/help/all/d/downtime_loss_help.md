# Downtime Loss Calculator

## Purpose

This calculator estimates how much production and contribution margin you lose due to planned and unplanned downtime.

It helps answer: how much downtime is costing per month, per year, and specifically from unplanned events.

## Inputs

- `Planned Downtime`: Scheduled downtime (for example maintenance), entered as time per month.
- `Unplanned Downtime`: Unexpected downtime (for example breakdowns), entered as time per month.
- `Production Rate`: Average production speed in units per hour.
- `Contribution Margin`: Contribution margin per unit (currency per unit). The currency you enter here is used for financial outputs.
- `Recovery Rate`: Share of lost production recovered through catch-up actions (for example overtime or rescheduling).
- `Events per Month`: Average number of downtime events per month.
- `Cost per Event`: Fixed cost per downtime event (for example call-out, restart, and setup losses).

## Results

- `Total Downtime`: Planned plus unplanned downtime.
- `Planned Production Loss`: Units not produced during planned downtime.
- `Unplanned Production Loss`: Units not produced during unplanned downtime.
- `Production Loss`: Total units not produced from all downtime.
- `Recovered Production`: Units recovered from the gross production loss using the recovery rate.
- `Net Production Loss`: Production loss after subtracting recovered units.
- `Event Cost per Month`: Monthly fixed downtime-event cost.
- `Financial Loss`: Monthly total loss = margin loss after recovery + event cost.
- `Annual Financial Loss`: Yearly contribution-margin loss from total downtime.
- `Cost of Unplanned Downtime`: Monthly unplanned downtime cost plus monthly event cost.
- `Annual Cost of Unplanned Downtime`: Yearly contribution-margin loss caused only by unplanned downtime.

## Understanding the Calculation

- Lost production = downtime x production rate
- Recovered production = lost production x recovery rate
- Net production loss = lost production - recovered production
- Margin loss after recovery = net production loss x contribution margin
- Event cost per month = events per month x cost per event
- Financial loss = margin loss after recovery + event cost per month
- Annual values are monthly values converted to per-year units

## Example

Using defaults:

- Planned Downtime: 2 hr/mo
- Unplanned Downtime: 5 hr/mo
- Production Rate: 120 unit/hr
- Contribution Margin: 8 USD/unit
- Recovery Rate: 0 pct
- Events per Month: 4 nos/mo
- Cost per Event: 150 USD/nos

Results:

- Production Loss = 840 unit/mo
- Financial Loss = 7320 USD/mo
- Annual Financial Loss = 87840 USD/yr
- Cost of Unplanned Downtime = 5400 USD/mo

## Important Assumptions and Interpretation

- Downtime-driven production loss is linear, but total financial loss also includes fixed event costs and recovery effects.
- It uses contribution margin, not full accounting profit.
- It assumes production rate and margin stay constant during the period.
- Recovery is modeled as a single percentage, not by shift-level constraints.
- It does not model bottlenecks or downstream constraints.
