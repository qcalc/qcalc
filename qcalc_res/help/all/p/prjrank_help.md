# Project Ranking based on Cashflows

## Purpose

This calculator compares several candidate projects, each with its own
series of cash flows over time, and ranks them as **Bad**, **OK**, or
**Best**, based on standard investment appraisal measures — Net Present
Value (NPV) and Internal Rate of Return (IRR) — against a required
**Discount Rate**. It is useful for deciding which of several competing
projects or investments is worth pursuing, and which single one is the
strongest choice.

> It supports cash flows at irregular periods, so **Period** values do not need to be consecutive.

## Background

### NPV, IRR, and the discount rate

Each project's cash flows include an initial outlay (a negative value) and
a series of returns afterward (positive values). **Net Present Value**
discounts all of these cash flows back to today at the **Discount Rate**
and sums them: a positive NPV means the project is expected to return more
than the discount rate requires, in absolute money terms. **Internal Rate
of Return** is the discount rate at which a project's own NPV would be
exactly zero — in effect, the project's own break-even rate of return.
Comparing a project's IRR to the **Discount Rate** tells you whether it
clears the bar you require; comparing NPVs across projects tells you which
one adds the most value overall.

## Inputs

### Discount Rate

The minimum acceptable annual rate of return, used both to discount cash
flows for NPV and as the bar each project's IRR must clear (for example,
`10 pct/yr`).

### Cashflow Interval

The time period between entries in each project's cash flow series (for
example, `yr` for one entry per year).

### Cashflows

A table with **Period** as the first column and one or more project
columns after it.

-   **Period** must be the first column and provides the project timeline
    (for example, 1, 10, 15, 25, 26).
-   Each project column contains cashflow values aligned to those periods.
-   **Period** values used for a project must be unique and increasing.
-   Each project must have at least one valid numeric cashflow row.

## Results

### Ranking

A table with one row per project:

-   **Project** — the project's column name from the **Cashflows** table.
-   **Count** — the number of cash flow entries used for that project
    (that is, how many valid cash flow rows were used for that project).
-   **End Period** — the last valid period value used for that project.
-   **NPV** — the project's Net Present Value at the **Discount Rate**,
    over its project timeline.
-   **IRR** — the project's Internal Rate of Return, expressed as an
    annual rate regardless of the **Cashflow Interval** used.
-   **Rank** — **Bad** if the project's NPV is negative or its IRR falls
    below the **Discount Rate**; otherwise **OK**; and among all the **OK**
    projects, the single one with the highest NPV is marked **Best**.

## Understanding the Calculation

For each project, the calculator builds that project's cash flow series,
then computes **NPV** at the **Discount Rate** and **IRR** (annualized to a
per-year rate for comparison, even if **Cashflow Interval** is not yearly).

-   Timing comes from the **Period** values and can be irregular.
-   Rows with non-numeric **Period** or project cashflow values are ignored
    for that project.

A project is marked **Bad** if either its NPV is negative or its annualized
IRR is below the **Discount Rate** — failing either test disqualifies it.
Every remaining project is marked **OK**, and whichever **OK** project has
the highest NPV is upgraded to **Best**.

## Example

Using the default inputs — a Discount Rate of 10% per year, a yearly
cashflow interval, a Period column of 1, 2, 3, 4, 5, and three projects
(Project1: -40000, 5000, 8000, 12000, 30000 over 5 years; Project2:
-25000, 3000, 5000, 25000 over 4 years; Project3: -10000, 2000, 6000,
7000 over 4 years) — the calculator returns:

-   **Project1**: Count 5, End Period 5, NPV ≈ 663.21, IRR ≈ 10.58%/yr,
    Rank **OK**
-   **Project2**: Count 4, End Period 4, NPV ≈ 642.37, IRR ≈ 11.07%/yr,
    Rank **OK**
-   **Project3**: Count 4, End Period 4, NPV ≈ 2036.06, IRR ≈ 19.38%/yr,
    Rank **Best**

All three projects clear the 10% discount rate and have positive NPV, so
none are ranked **Bad**. Project3 is marked **Best** because its NPV
(2036.06) is the highest of the three, even though it requires the smallest
initial investment.

## Important Assumptions and Interpretation

-   A **Rank** of **Bad** means the project fails to meet the required
    **Discount Rate**, is expected to destroy value (negative NPV), or
    both — it does not mean the project has no positive cash flows at all.
-   Only one project can be marked **Best** per calculation — the one with
    the highest NPV among those ranked **OK**. Other **OK** projects may
    still be worth pursuing if you are not limited to a single choice.
-   Project rows are selected from numeric, nonblank cashflow entries;
    a cashflow of 0 is valid and does not terminate the series.
-   The calculator raises an error when a project's usable **Period**
    values are duplicated or not increasing.
-   NPV values across projects are only directly comparable when the
    projects are evaluated over the same **Cashflow Interval**; the table
    does not adjust NPV for differing project lengths beyond discounting
    each series on its own timeline.
