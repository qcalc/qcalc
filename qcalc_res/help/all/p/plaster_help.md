# Estimate Cement and Sand for Plaster work

## Purpose

This calculator estimates cement, sand, plastered area, and labour mandays for plaster work from entered dimensions, number of sides, and mortar assumptions.

It helps you quickly assess material and labour requirements for one-side or both-side plastering.

## Background

### One-side vs both-side plastering

Plaster quantity depends strongly on whether plaster is applied to one face or both faces. This calculator uses the selected side count directly in both area and volume calculations.

## Inputs

- **Work Thickness**: Plaster thickness.
- **Work Length**: Surface length.
- **Work Width**: Surface width.
- **Work Side**: Select `One Side` or `Both Side` (implemented values `1` or `2`; initial selection is `Both Side`).
- **Cement Sand Ratio**: Cement part of mortar mix.
- **Sand Part**: Sand part of mortar mix.
- **Mortar Dry Volume Factor**: Dry-volume multiplier for mortar.
- **Cement Bag Volume**: Volume per bag for cement conversion.
- **Skilled Labour**: Skilled productivity as area per manday.
- **Unskilled Labour**: Unskilled productivity as area per manday.

## Results

- **Cement**: Estimated cement requirement in `bag`.
- **Sand**: Estimated sand requirement in `cft`.
- **Plaster Work Area**: Total plastered area in `sft`.
- **Skilled Labour**: Estimated skilled labour effort in `manday`.
- **Unskilled Labour**: Estimated unskilled labour effort in `manday`.

## Understanding the Calculation

All dimensions are converted to inches internally.

1. Convert Work Side to an integer side multiplier ($n$), either 1 or 2.

2. Compute wet plaster volume:

$$V_{work}=L\times W\times T\times n$$

3. Compute plastered area:

$$A_{work}=L\times W\times n$$

4. Dry mortar volume:

$$V_{dry}=V_{work}\times f_{dry}$$

5. Split dry mortar into cement and sand, with cement part $c$ and sand part $s$:

$$V_{cement}=V_{dry}\times \frac{c}{c+s}$$

$$V_{sand}=V_{dry}\times \frac{s}{c+s}$$

Cement is converted to bags using Cement Bag Volume. Sand is displayed in cubic feet.

6. Labour mandays are based on area productivity:

$$M_{skilled}=\frac{A_{work}}{R_{skilled}}\quad , \quad M_{unskilled}=\frac{A_{work}}{R_{unskilled}}$$

## Example

Example scenario:

- Work Length `12 ft`, Work Width `10 ft`, Work Thickness `0.5 inch`
- Work Side `Both Side`
- Mix parts: Cement Sand Ratio `1.0`, Sand Part `4.0`
- Mortar Dry Volume Factor `1.5`
- Labour productivity: Skilled `75 sft/manday`, Unskilled `50 sft/manday`

Expected interpretation:

- Switching from one side to both sides doubles both area-driven and volume-driven requirements.
- Increasing thickness increases Cement and Sand, but does not increase Plaster Work Area.
- Increasing labour productivity rates reduces required mandays.

## Important Assumptions and Interpretation

- Work is treated as a rectangle with uniform thickness.
- Work Side is applied as a direct multiplier (1 or 2).
- Labour outputs are manday estimates, not staffing schedules.
- The function does not enforce explicit validation against non-physical values; use realistic entries and units.
- This calculator estimates quantity and effort, not direct cost.
