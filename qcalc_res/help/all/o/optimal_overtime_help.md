# Optimal Overtime Level

## Purpose

This calculator finds the overtime level that minimizes total monthly production-related cost.

It balances three competing effects:

- Overtime raises labor cost.
- More overtime reduces production shortfall and penalty cost.
- Overtime efficiency deteriorates at higher overtime levels, so each extra overtime hour can produce less output.

## Inputs

- `Required Production`: Target production quantity for the month.
- `Available Normal Hours`: Regular production hours available in the month.
- `Maximum Overtime Hours`: Upper bound for overtime search. The optimizer evaluates overtime from zero up to this limit.
- `Production Rate`: Base production rate per hour.
- `Normal Hourly Cost`: Labor cost per normal production hour.
- `Overtime Hourly Cost`: Labor cost per overtime hour.
- `Shortfall Penalty`: Cost charged per unit of unmet required production.
- `Fixed Production Cost`: Monthly fixed production-related cost added to total cost.
- `Efficiency Deterioration`: Controls how quickly overtime productivity declines as overtime approaches its maximum.
- `Optimization Points`: Number of overtime trial points used to locate the minimum-cost point.
- `Scenario Points`: Number of points used in the scenario table and optimization chart.

## Results

- `Optimal Overtime`: Best overtime level found by the optimizer.
- `Normal Production`, `Overtime Production`, `Total Production`: Production split and combined output at the optimal overtime level.
- `Production Shortfall`: Unmet required production at the optimum.
- `Overtime Efficiency Factor`: Effective overtime productivity multiplier at the optimum.
- `Normal Labor Cost`, `Overtime Labor Cost`, `Shortfall Cost`, `Total Cost`: Cost components and final monthly total at the optimum.
- `Cost per Unit Produced`: Total cost divided by total produced quantity at the optimum.
- `Optimization Chart`: Visual cost curve versus overtime hours, including `Total Cost`, `Overtime Labor Cost`, and `Shortfall Cost`.
- `Overtime Scenarios`: Point-by-point scenario table across the overtime range.

## Understanding the Calculation

- Normal production is based on available normal hours and production rate.
- Overtime output uses a reduced effective overtime rate when efficiency deterioration is nonzero.
- For each overtime level, the calculator computes total production, shortfall, and costs.
- It returns the overtime level with the minimum total cost.

### Optimization Process Note

- The calculator searches overtime from `0` to `Maximum Overtime Hours` using evenly spaced trial points.
- The number of trial points is controlled by `Optimization Points`.
- At each trial point, it computes `Overtime Production`, `Production Shortfall`, and all cost components.
- It selects the trial point with the lowest `Total Cost` as `Optimal Overtime`.
- `Scenario Points` controls only the reporting granularity for the scenario table and chart, not the search resolution.
- A higher `Optimization Points` value gives a finer search and can slightly shift the reported optimum.

## Example (Current Defaults)

Using the current defaults, the calculator finds approximately:

- Optimal Overtime: 45.98 hr/mo
- Normal Production: 1600 unit/mo
- Overtime Production: 343.15 unit/mo
- Total Production: 1943.15 unit/mo
- Production Shortfall: 56.85 unit/mo
- Total Cost: 3116.01 USD/mo
- Cost per Unit Produced: 1.6036 USD/unit

Interpretation:

- Zero or low overtime leaves too much shortfall penalty.
- Excessive overtime becomes less productive due to efficiency deterioration and raises overtime labor cost.
- The optimizer selects a middle region where combined cost is lowest.

## Important Assumptions and Interpretation

- Overtime efficiency decay follows the built-in quadratic pattern.
- Production rate is otherwise constant.
- Shortfall penalty is linear per unit short.
- The optimizer uses a discrete search grid based on Optimization Points; a finer grid can slightly change the reported optimum.
- Results are monthly planning estimates, not shift-by-shift scheduling instructions.
