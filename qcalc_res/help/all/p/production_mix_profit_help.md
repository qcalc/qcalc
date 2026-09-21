# Production Mix Profitability

## Purpose

This calculator finds a monthly production plan that maximizes total contribution profit across multiple products.

It compares your current plan with an optimized plan while respecting machine-time, labor-time, demand, and ramp-change limits.

## Inputs

- `Products`: Enter one row per product with these columns:

- `Product`
- `Selling Price`
- `Variable Cost`
- `Machine Time`
- `Labor Time`
- `Max Demand`
- `Current Production Quantity`
- `Max Ramp Change`

- `Guidance`:

- Use compatible units (for example `USD/unit`, `min/unit`, `unit/mo`).
- `Max Ramp Change` limits how far the optimized quantity can move from current quantity in one planning cycle.

- `Available Machine Time`: Total machine hours available per month for all products together.
- `Available Labor Time`: Total labor hours available per month for all products together.

## Results

- `Executive Summary`: A short decision table with:

- Current vs Optimized monthly contribution profit
- Current vs Optimized annual contribution profit
- Current vs Optimized machine utilization
- Current vs Optimized labor utilization
- Current vs Optimized total production
- Products at Ramp Limit

- `Optimal Production Mix`: Detailed product-level output including:

- `Current Quantity`, `Optimal Quantity`, `Quantity Gap`
- `Max Ramp Change` and `Ramp Limit Binding`
- `Machine/Labor time per unit` and used totals
- Current vs Optimized contribution profit and gap

- `Key Totals`: Additional outputs show total production, time usage, unused capacity, utilization, and profit improvement.

## How to Interpret

- If `Ramp Limit Binding` is true for a product, change limits are restricting the optimizer.
- If `Unused Machine Time` is near zero, machine capacity is likely a binding bottleneck.
- If `Unused Labor Time` is near zero, labor capacity is likely a binding bottleneck.
- `Contribution Profit Improvement` shows achievable monthly improvement under the current constraints.

## Example (Default Data)

With the default 3-product table and capacities:

- Available Machine Time: `1000 hr/mo`
- Available Labor Time: `800 hr/mo`

Current vs Optimized Snapshot:

Using the current default input, the calculator shows:

- Current monthly contribution profit: `212200 USD/mo`
- Optimized monthly contribution profit: `248333.3335 USD/mo`
- Improvement: `36133.3335 USD/mo`
- Products at ramp limit: `2`

This is the practical value of optimization: instead of manually guessing changes product by product, the model reallocates volume within all active constraints and finds the best feasible plan for this cycle.

In this default case, Products A and B increase up to their ramp limits, while Product C is reduced. That pattern reflects the combined effect of contribution margins, machine/labor time intensity, demand caps, and ramp limits.

## Important Assumptions

- Linear contribution model: contribution per unit is constant.
- Time per unit is constant within the planning period.
- Demand is a hard upper bound.
- Ramp constraint is symmetric: both increase and decrease are limited by `Max Ramp Change`.
- Quantities are continuous (not forced to integers).

## Formula References

Objective:

Maximize

$$
\max \sum_i Q_i (P_i - C_i)
$$

Constraints:

$$
\sum_i Q_i M_i \le M
$$

$$
\sum_i Q_i L_i \le L
$$

$$
0 \le Q_i \le D_i
$$

$$
Q_i \le Q_i^{(cur)} + R_i
$$

$$
Q_i \ge Q_i^{(cur)} - R_i
$$

Derived comparison metrics:

$$
\Delta Q_i = Q_i^{*} - Q_i^{(cur)}
$$

$$
\Delta \Pi_i = Q_i^{*}(P_i - C_i) - Q_i^{(cur)}(P_i - C_i)
$$

Where:

- `Q_i`: optimized quantity for product `i`
- `Q_i*`: same optimized quantity (star notation)
- `Q_i^(cur)`: current quantity for product `i`
- `P_i`: selling price per unit
- `C_i`: variable cost per unit
- `M_i`: machine time per unit
- `L_i`: labor time per unit
- `M`: available machine time
- `L`: available labor time
- `D_i`: max demand
- `R_i`: max ramp change
- `Π_i`: contribution profit for product `i`
