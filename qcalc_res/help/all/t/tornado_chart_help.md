# Tornado Chart

## Purpose

`tornado_chart()` compares low/high impacts by factor around a baseline.

Use it when you already have scenario values and want a fast visual ranking
of which factors move the result the most.

---

## Inputs

### Data table (`data`)

Provide:

```text
Factor | Low | High
```

- `Factor`: driver name
- `Low`: low-case output value
- `High`: high-case output value

### Baseline (`baseline`)

Impacts are computed as:

- `Low Impact = Low - baseline`
- `High Impact = High - baseline`

### Options

- `sort_by`: `absolute`, `low`, `high`, or `none`
- `top_n`: keep top N factors
- `show_values`: show numeric labels on bars

---

## Output

Returns a horizontal tornado chart with:

- low-impact bars,
- high-impact bars,
- a zero reference line.

---

## Example

Input:

| Factor | Low | High |
|---|---:|---:|
| Price | 95 | 105 |
| Volume | 80 | 130 |
| FX | 98 | 102 |

with `baseline = 100` highlights `Volume` as the strongest driver.

---

## Tip

Use **Sensitivity Analysis** for end-to-end sampling + ranking + charting.
