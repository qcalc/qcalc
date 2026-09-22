# Optimization: Assignment

## Purpose

This calculator assigns tasks to agents at minimum total cost while honoring
agent capacity limits.

It is designed for one-to-one task coverage: each task must be assigned exactly
once. In practice, it answers a concrete question: given everyone's cost or
effort profile, who should be paired with which task so total cost stays as
low as possible while nobody is overloaded?

## Background

### Problem Domain

Assignment optimization is a binary integer program where each decision is
either assign (`1`) or do not assign (`0`). The classic one-to-one version of
this problem can be solved in polynomial time by the Hungarian algorithm; this
model generalizes it with per-agent capacity, so one agent can take on
several tasks.

### Real-World Uses

- **Staff-to-ticket assignment**: Workload is uneven and handling cost differs
	by staff member. Use the model to assign one owner per ticket at minimum
	total cost.
- **Machine-to-work-order assignment**: Each machine has limited capacity and
	different processing efficiency by job. Use the model to find a feasible,
	low-cost machine-job mapping.
- **Field engineer dispatch**: Several engineers can handle each call, but
	travel/time cost differs. Use the model to assign calls at lowest cost while
	keeping engineer load within capacity.
- **Reviewer/proctor allocation**: Every task must be covered, but reviewer
	bandwidth is finite. Use the model to guarantee full coverage at minimum
	assignment cost.

## Inputs

- `agents`: Input table with columns `Agent` and `Capacity`.
	`Capacity` is the maximum number of tasks that each agent can take.
- `tasks`: Input table with column `Task`, listing all tasks to be assigned.
- `assign_cost`: Input table with columns `Agent`, `Task`, and `Cost`.
	`Cost` is the assignment cost for that agent-task pair. This table must
	contain the complete Agent-Task pair grid.
- `show_zero`: Controls output display.
	Turn on to include `Assigned = 0` rows; turn off to show only selected
	assignments.

## Results

- `Summary`: High-level optimization outcome with `Status`, minimum
	`Objective`, and `Decision Count`. This is your quick feasibility and
	performance checkpoint before acting on detailed rows.
- `Decision Table`: Pair-level assignment output (`Agent`, `Task`, `Assigned`,
	`Cost`). This is the actionable allocation plan to execute.
- `Resource Utilization`: Per-agent workload view (`Assigned Tasks`, `Capacity`,
	`Utilization %`) showing where agents are underused or near saturation.
- `Constraint Slack`: Tightness of task-coverage and agent-capacity constraints.
	Helps identify whether cost is being driven by scarce capacity.

## Understanding the Calculation

The model solves:

- Minimize: $\sum_{a,t} c_{at} x_{at}$
- Task coverage: $\sum_a x_{at} = 1$ for each task
- Agent capacity: $\sum_t x_{at} \leq \text{Capacity}_a$
- Binary: $x_{at} \in \{0,1\}$.

## Example

With defaults, solution is `Optimal` with objective `10` and assignments:

- `A1 -> T2`
- `A2 -> T1`
- `A3 -> T3`

Interpretation: all tasks are covered exactly once at minimum total cost.
A single changed cost cell can flip an entire assignment pattern, which is why
it's worth re-running this model whenever pricing or effort estimates shift.

## Important Assumptions and Limitations

- Each task is assigned once, not fractionally.
- Agent capacities are upper bounds only.
- No skill/precedence/time-window constraints in this model.
