The calculator is a multi-period planning model. At a high level, it decides how much to produce for each product in each period so that demand is met as well as possible while respecting capacity, inventory flow, and optional backlog.

It uses four table inputs:

- product master
- demand by period
- period capacity
- bill of materials / material requirements

The product master carries the economics and limits for each product:

- Opening Inventory
- Safety Stock
- Production Cost
- Holding Cost
- Max Production
- Backlog Penalty
- optional Setup Cost

The BOM / material-requirements table links each product to the materials it consumes per unit of production. When procurement is enabled, the calculator multiplies those coefficients by the solved production plan to derive material demand automatically and passes that demand into the procurement submodel.

How it works:

- For each product and period, it creates production, inventory, and fulfilled-demand variables.
- If backlog is enabled, it also creates backlog variables.
- If setup cost is positive, it creates setup binary variables and links them to production.
- It enforces:

    - production cannot exceed product max production
    - total production in a period cannot exceed period capacity
    - inventory flows forward period to period
    - inventory cannot fall below safety stock
    - backlog, if enabled, carries unmet demand forward

The objective you choose changes what the model tries to optimize:

- Minimize Total Cost: production cost + holding cost + backlog cost + optional setup cost
- Maximize Service Level: maximize fulfilled demand
- Minimize Inventory: minimize total inventory held across the horizon

The form layout is tabbed and organized into:

- Settings
- Product Master
- Demand
- Capacity

The outputs are:

- Summary: overall status, objective value, service level, and cost breakdown
- Period Plan: period-by-product decision table
- Capacity Utilization: how much each period’s capacity was used
- Product Summary: totals by product
- Material Requirement Detail: product-by-material consumption implied by the solved production plan
- Material Demand: aggregated material demand sent to procurement
- Constraint Slack: solver slack values for diagnostics

 service-level floor field is revealed when the objective is cost minimization.

One important thing to keep in mind: this is still a planning model, not a full enterprise S&OP suite yet. It covers production, inventory, demand, capacity, and optional backlog in a clean core form. Later expansions can add procurement, supplier logic, overtime, and other planning dimensions around this base.
