# Sales Discount Optimization

## Purpose

This calculator recommends a discount that maximizes expected monthly profit for a sales offer.

It captures a realistic trade-off:

- Higher discount can increase `Conversion Rate`.
- Higher discount also reduces `Unit Contribution Margin`.
- Capacity (`Maximum Fulfillable Units`) and policy limits (`Minimum Unit Margin`) can constrain the best decision.

## Inputs

- `Number of Prospects`: Potential customers exposed to the offer in the analysis period.
- `List Price`: Undiscounted selling price per unit.
- `Unit Cost`: Variable cost per unit.
- `Base Conversion Rate`: Conversion rate at zero discount.
- `Maximum Conversion Rate`: Saturation ceiling for conversion as discount increases.
- `Sensitivity Factor (k)`: Controls how quickly conversion rises with discount. This is dimensionless (not a percent input). Suggested practical range: `3` to `20`.
- `Sales Cost per Prospect`: Acquisition or outreach cost per prospect.
- `Current Discount`: Existing discount policy used for comparison outputs.
- `Minimum Discount`: Lower bound of the discount search range.
- `Maximum Discount`: Upper bound of the discount search range.
- `Maximum Fulfillable Units`: Capacity cap on sellable units in the period.
- `Minimum Unit Margin`: Minimum allowed unit margin for discount feasibility.
- `Optimization Points`: Number of trial discount points used in the optimization search.
- `Scenario Points`: Number of points shown in the scenario table and chart curves.

## Results

- `Recommended Discount`: Best discount found by optimization.
- `Current Discount`: Reference discount used for comparison.
- `Profit at Current Discount`: Expected profit at the current discount.
- `Profit at Optimal Discount`: Expected profit at the recommended discount.
- `Profit Lift vs Current Discount`: Absolute monthly gain from moving to the recommended discount.
- `Profit Lift % vs Current Discount`: Percent profit improvement versus current discount.
- `Expected Conversion Rate`: Expected conversion at recommended discount.
- `Expected Units Sold (Demand)`: Demand-side expected units before capacity cap.
- `Expected Units Sold (Capped)`: Units sold after applying capacity cap.
- `Net Selling Price`: Effective selling price after recommended discount.
- `Unit Contribution Margin`: Margin per sold unit at recommended discount.
- `Revenue`: Expected revenue at recommended discount.
- `Gross Contribution`: Units sold times unit contribution margin.
- `Sales Cost Total`: Prospect-level selling/acquisition cost for the period.
- `Profit per Prospect`: Profit normalized by number of prospects.
- `Profit at Zero Discount`: Baseline profit at zero discount.
- `Profit Lift vs Zero Discount`: Improvement versus zero-discount baseline.
- `Capacity-Limited at Optimum`: Indicates demand exceeds fulfillable units at optimum.
- `Margin-Floor Active at Optimum`: Indicates optimum is on the minimum-margin boundary.
- `Boundary Warning`: Indicates optimum occurs at search boundary (`Minimum Discount` or `Maximum Discount`).
- `Discount Scenarios`: Table across discount points with conversion, units, pricing, and profit metrics.

## Charts

The calculator prepares chart outputs for visual analysis:

- `Optimization Chart`: Profit/cost behavior versus discount.
- `Conversion vs Margin Chart`: Conversion response and margin compression versus discount.
- `Demand vs Capacity Chart`: Demand-side units versus capacity-capped sold units.

## Understanding the Optimization

- The model computes expected results for trial discounts from `Minimum Discount` to `Maximum Discount`.
- Only points satisfying `Minimum Unit Margin` are considered feasible.
- The feasible trial point with highest `Total Profit` becomes `Recommended Discount`.
- `Optimization Points` controls search resolution; larger values can slightly shift the reported optimum.
- `Scenario Points` controls reporting granularity (table/chart density), not optimization logic.

### Input Clarification

- `Sensitivity Factor (k)` is not a `%` field. Enter plain numeric values such as `5`, `10`, or `15`.
- Larger `k` means faster conversion response at low discount levels; smaller `k` means a flatter response curve.
- Start with `k` in the `3` to `20` range and calibrate from historical data.

## Example (Current Defaults)

With current defaults, the calculator returns approximately:

- `Recommended Discount`: `10.85 pct`
- `Current Discount`: `15.0 pct`
- `Profit at Current Discount`: `5816.31 USD/mo`
- `Profit at Optimal Discount`: `6762.62 USD/mo`
- `Profit Lift vs Current Discount`: `946.31 USD/mo` (`16.27 pct`)
- `Expected Conversion Rate`: `14.93 pct`
- `Expected Units Sold (Demand)`: `1493.15 unit/mo`
- `Expected Units Sold (Capped)`: `1493.15 unit/mo`
- `Capacity-Limited at Optimum`: `False`
- `Boundary Warning`: `False`

Interpretation:

- In this configuration, reducing discount from current policy improves profit by recovering margin faster than conversion drops.
- Capacity is not binding at the optimum (`Expected Units Sold (Demand)` equals `Expected Units Sold (Capped)`).

## Important Assumptions and Interpretation

- Conversion follows a saturating response curve with discount; it does not increase indefinitely.
- `Sales Cost per Prospect` is modeled as fixed per prospect and independent of discount.
- Capacity is represented as a hard cap (`Maximum Fulfillable Units`).
- This is a single-period offer optimization; seasonality, competitor response, and inventory dynamics are not modeled.
- Results are decision support estimates and should be validated with market/segment context.

## Formula References

Objective:

$$
\max_d\ Profit(d)
$$

Conversion model:

$$
CR(d)=CR_0 + (CR_{max}-CR_0)\left(1-e^{-k d}\right)
$$

Demand and sold units:

$$
Q_{demand}(d)=Prospects \times CR(d)
$$

$$
Q_{sold}(d)=\min\left(Q_{demand}(d),\ Q_{cap}\right)
$$

Price and margin:

$$
P_{net}(d)=P_{list}(1-d)
$$

$$
M(d)=P_{net}(d)-C_{unit}
$$

Profit:

$$
Profit(d)=Q_{sold}(d)\times M(d)-Prospects\times C_{sales}
$$

Feasibility rule:

$$
M(d) \ge M_{min}
$$