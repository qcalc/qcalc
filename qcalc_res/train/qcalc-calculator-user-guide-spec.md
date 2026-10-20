You are writing an accurate, clear, and practical end-user guide for a qCalc
calculator. Your audience is a capable general user who may know the subject
area well, a little, or not at all. Explain both how to use the calculator and
what the calculation means.

Your guide must be grounded in the supplied source code. Treat the code as the
authority for the calculator's inputs, defaults, units, conversions, formulas,
timing conventions, result labels, result signs, edge cases, and assumptions.
Use general subject knowledge only to provide context that is consistent with
the implemented calculation. Do not describe functionality that the code does
not provide.

### Spec in a Nutshell

This spec defines a strict process for writing qCalc end-user guides from source code, with code behavior as the sole authority.

Key requirements:
1. Analyze implementation first, including __info metadata, schema labels, function logic, helper imports, returned dict keys, table columns/data, units, signs, defaults, branches, and edge cases.
2. Do not invent behavior. If something cannot be verified, explicitly list what file/function/runtime behavior is missing.
3. Preserve exact user-visible labels and conventions (including comparison order like A - B).
4. Describe inputs, outputs, units, timing assumptions, formulas, and interpretation exactly as implemented.
5. Separate calculator facts from external domain context; avoid unsupported advice or recommendations.
6. Write one Markdown guide named function_name_help.md with this structure:
   1. Title
   2. Purpose
   3. Background (optional for simple calculators)
   4. Inputs
   5. Results
   6. Understanding the Calculation
   7. Example (only reproducible or qualitative if unverified)
   8. Important Assumptions and Interpretation
7. Include clear sign interpretation, table/column interpretation, unit clarity, and scenario/convention impacts.
8. Final output should be only the finished guide, plus Verification Notes only when behavior is unresolved.


### Materials You Will Receive

You will receive:

1. The calculator's Python source file, normally under
   `../../../qcalc/calculators/all`.
2. Any imported helper functions, schemas, constants, tests, or supporting
   files needed to understand its behavior.
3. One or more existing qCalc guides in `../../help/all` as style
   references.

If essential behavior cannot be determined from the supplied material, say so
plainly. Do not invent an answer. List the precise missing file, function, or
runtime behavior that needs to be checked.

### First: Analyze the Implementation

Before drafting the guide, inspect the implementation and make a private
working note containing the following facts. Do not include this note in the
published guide unless requested.

- The calculator title, short description, and intended decision or question.
- Every user-facing input: Python parameter name, displayed label, default,
  accepted type, expected unit, valid range or validation rule, and meaning.
- Unit parsing and conversions, including which input establishes the output
  currency or other display unit.
- Every output, table, chart, and displayed column: its exact label, unit, and
  how it is calculated.
- Formulas, branches, loops, rounding, timing, and conventions that materially
  affect results. Translate them into plain language, but retain enough detail
  to be technically correct.
- Sign conventions and comparison directions. Establish exactly what positive,
  negative, zero, higher, and lower values mean before explaining results.
- Defaults and a reproducible example based on them when they are suitable.
- Assumptions explicitly made by the code, along with relevant factors that the
  calculator does not model.
- Exceptional or boundary behavior, such as zero denominators, missing data,
  non-positive values, unsupported units, fallback values, and conditional
  results.

Read `__info()` metadata and any `schema` entries as well as the calculator
function. Metadata can supply the displayed title and custom input labels;
function parameters alone may not match the interface wording. Follow imported
functions far enough to understand calculations that they control. Tests and
examples may confirm behavior, but do not let an outdated test override the
current implementation without noting the discrepancy.

When the source returns a dictionary, examine its keys, table `columns`, table
`data`, and quantity units. These normally determine the result headings that
must appear in the guide. When values use `Qty`, describe accepted units and
conversions only when verified from code or the documented quantity system.

### Accuracy Requirements

1. Use the exact user-visible input and result labels where known. Preserve
   capitalization, abbreviations, and comparison labels such as `Rent - Buy`.
2. Do not claim that an input is required, optional, constrained, rounded, or
   formatted unless the source or interface establishes it.
3. State timing assumptions precisely. Distinguish, for example, beginning of
   period from end of period, monthly from annual payments, nominal from
   effective rates, and historical values from scenario values.
4. Describe formulas only at the level useful to the user. Include a compact
   formula when it helps understanding, but ensure it matches the code.
5. Never label a result favorable, unfavorable, profitable, safe, healthy, or
   recommended without explaining the condition and the calculator's stated
   scope.
6. Separate facts calculated by qCalc from external background information.
   Do not present domain rules of thumb, legal requirements, medical guidance,
   tax treatment, market forecasts, or individualized advice as calculator
   output.
7. Do not manufacture precision. Use approximate language where the calculator
   estimates, simplifies, or depends heavily on user assumptions.
8. Do not mention internal implementation details, Python names, source paths,
   or code mechanics in the end-user guide unless they are needed to explain a
   visible calculator behavior.
9. Do not list default values for every input by default. Mention defaults
  selectively, only when a default materially affects interpretation,
  branching, conventions, or a common user decision.

### Write the Guide

Write a single self-contained Markdown file. Match the existing qCalc guides:
use a concise title, `##` sections, short paragraphs, and simple bullet lists.
For `Inputs` and `Results`, prefer bullet lists over creating a separate `###`
heading for every single input parameter or output field. Use `###`
subsections when grouping related inputs/results or explaining complex tables,
charts, or scenarios. Use plain English and define technical terms before
relying on them. Prefer a practical explanation over textbook-style exposition.
Avoid cluttering input bullets with minor defaults; surface only the defaults
that are important for understanding behavior.

Name the file `<function_name>_help.md`, using the calculator function name
exactly as it appears in the source. For example, the guide for `age` must be
named `age_help.md`. An HTML version may also be provided when needed, but
Markdown is preferred.

Use the structure below. Omit a subsection only when it truly does not apply;
do not add empty headings. Reorder small parts when necessary for clarity.

```md
# [Exact Calculator Title]

## Purpose

[In one or two paragraphs, state the real-world question the calculator helps
answer, who might use it, and the meaning of the comparison or estimate.]

## Background

### [Key concept]

[Explain the underlying topic, terms, relationship, or problem in language a
new user can follow. Include only background that improves use or
interpretation of this specific calculator.]

## Inputs

- **[Exact Input Label]**: [State what to enter, the expected unit or format
  where verified, why the calculator needs it, and the practical effect of a
  higher/lower value when that effect is clear from the implementation.]

[Repeat as bullet items for each input. Use `###` subsections only when
grouping related inputs is clearly better than a flat list.]

## Results

- **[Exact Result or Table Label]**: [Explain what it measures, how to read
  its unit and sign, and what comparison or action it can inform.]

[Repeat as bullet items for key outputs. For tables/charts, keep using `###`
subsections when a column-by-column explanation is needed.]

## Understanding the Calculation

[Explain the calculation flow, key formulas, timing, conversions, and scenario
logic. Keep this useful rather than reproducing code.]

## Example

[Give one coherent, reproducible example. Use source defaults only after
checking that they produce the stated result. State inputs and explain what the
result means. If no result has been executed or verified, explain the expected
directional result rather than inventing a numeric output.]

## Important Assumptions and Interpretation

[State material assumptions, exclusions, limitations, and sensible cautions.
Clarify when a result is an estimate or decision aid rather than a prediction
or professional advice.]
```

The `Background` section is optional for a very simple calculator, but include
it whenever understanding the topic is necessary to choose inputs or interpret
results. For complex calculators, use additional subsections such as
`Calculation Method`, `Scenario Results`, `Units`, or `Limitations` rather
than forcing unrelated material into one long section.

### Result Interpretation Rules

- Identify the main decision result early and explain it in direct language.
- For comparison columns, explicitly define the order of subtraction. For
  example, if a column is `A - B`, say which alternative is cheaper for a
  positive result and which is cheaper for a negative result.
- Explain tables column by column when a reader could otherwise confuse actual
  values, assumptions, scenarios, changes, totals, rates, or present values.
- Explain derived measures and acronyms in full on first use.
- Mention units beside results when they are not self-evident. Do not assume a
  currency, time basis, temperature scale, or measurement system that the code
  does not establish.
- Where an output depends on a user-selected convention, explain that convention
  and how changing it affects interpretation.

### Example Rules

- Use realistic, internally consistent values and units.
- Make every numerical claim reproducible from the supplied code.
- Mark rounded values as approximate when appropriate.
- Walk from the inputs to the conclusion. The example should teach
  interpretation, not merely display a result.
- Do not include a worked result if execution or manual verification is not
  available. A qualitative scenario is better than a plausible but unverified
  number.

### Final Quality Check

Before returning the guide, verify all of the following:

- Every visible input has been explained.
- Every important output, table column, and sign convention has been explained.
- Input labels and result labels agree with the implementation.
- Units, rates, timing, and conversions agree with the implementation.
- The guide distinguishes actual data, assumptions, scenarios, and calculated
  results wherever the calculator does.
- Formula descriptions and example numbers have been checked against the code.
- Important exclusions and limitations are stated without overstating risk.
- The prose is clear to a non-specialist, but no simplification changes the
  calculator's meaning.
- The Markdown is polished, self-contained, and contains no source-code
  commentary or unsupported claims.

Return only the finished Markdown guide, followed by a short `Verification
Notes` section if, and only if, a behavior could not be verified from the
available source. In that section, name the unresolved behavior and avoid
guessing about it.