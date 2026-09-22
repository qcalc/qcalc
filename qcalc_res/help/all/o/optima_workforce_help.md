# Optimization: Workforce Shift Scheduling

## Purpose

This calculator assigns workers to shifts at minimum labor cost, subject to
worker max-shift limits and optional skill matching. It can optionally allow
shortages with a penalty.

In practice, it answers a scheduling question every roster owner deals with:
given who's available, what they're qualified for, and what they cost, who
should actually work which shift so coverage is met at the lowest labor cost?

## Background

### Problem Domain

Workforce scheduling here is a binary assignment model with optional unmet
demand variables. Shift rostering is famously one of the trickier assignment
problems in practice — airlines and hospitals run entire scheduling teams
around it — because skill requirements and per-worker limits interact in ways
that are hard to reason about by hand.

### Real-World Uses

- **Operations/retail shift scheduling**: Every shift has a minimum headcount,
  but worker availability is limited. Use the model to cover demand at minimum
  labor cost.
- **Skill-aware staffing**: Some shifts require specific skills and not all
  workers qualify. Use the model to create feasible worker-shift matches with
  skill compliance.
- **Contact-center rostering**: Shift demand fluctuates and agent costs vary.
  Use the model to optimize staffing cost while respecting maximum shifts per
  worker.
- **Understaffing contingency planning**: Demand can exceed feasible staffing in
  peak conditions. Use the model to quantify shortages and penalty impact when
  full coverage is not possible.

## Inputs

- `workforce_staff`: Input table with columns `Worker`, `Max Shifts`, and
  `Cost per Shift`, plus optional `Skills` (comma-separated tags).
  `Max Shifts` is typically a count of assignable shift slots per worker.
- `workforce_shift_demand`: Input table with `Shift` and `Required`, plus
  optional `Required Skill`. When a required skill is set, only workers whose
  skill tags include it are eligible for that shift. `Required` is typically a
  headcount/assignment count per shift.
- `allow_shortage`: Coverage policy.
  Use `Yes` to allow unmet demand with penalty; use `No` to force exact shift
  coverage.
- `shortage_penalty`: Penalty cost per unfilled shift-assignment unit when
  shortage is allowed.
- `show_zero`: Controls output display.
  Turn on to include zero-assignment rows; turn off to show only active
  assignments.

## Results

- `Summary`: Staffing outcome totals (`Required`, `Assigned`, `Shortage`,
  `Labor Cost`, `Shortage Cost`, objective) so you can quickly judge cost and
  service-level balance.
- `Decision Table`: Worker-shift assignment lines with line labor cost; this is
  the direct schedule allocation output.
- `Coverage Table`: Shift-level service view (`Required`, `Assigned`,
  `Shortage`, `Coverage %`) to spot understaffed periods immediately.
- `Worker Utilization`: Per-worker load and utilization against max shifts,
  helping identify overused or underused staff.
- `Constraint Slack`: Slack on worker-limit and shift-coverage constraints,
  showing where capacity additions would have impact.

## Understanding the Calculation

Objective:

- Minimize labor assignment cost + shortage penalty cost.

Constraints:

- Worker assignment count does not exceed `Max Shifts`.
- Shift demand equation:
  - with shortage: assigned + shortage = required
  - without shortage: assigned = required.

## Example

Default run returns `Optimal` with objective `470`, total required `5`, total
assigned `5`, total shortage `0`.

Interpretation: all shifts can be fully staffed with available workers/skills at
minimum labor cost. If a shift ever shows shortage while cheaper workers sit
unused, check `Required Skill` first — skill mismatch, not cost, is the most
common reason an available worker can't be assigned.


## Important Assumptions and Limitations

- A worker-shift assignment is binary (0/1).
- No shift overlap, rest-period, or labor-law constraints modeled.
- Single-period scheduling abstraction (no explicit date sequence).
