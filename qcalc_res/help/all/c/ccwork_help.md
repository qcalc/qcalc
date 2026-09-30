# Estimate Gravel, Cement and Sand for Plain Cement Concrete work

## Purpose

This calculator estimates material quantities and labour effort for a plain cement concrete (PCC) block based on entered dimensions, mix parts, and productivity assumptions.

It helps you plan how much cement, sand, gravel, and labour mandays are needed for a defined concrete volume.

## Background

### What this estimate represents

The calculator treats the concrete work as a rectangular volume. It then applies a dry-volume factor and splits that dry volume into cement, sand, and gravel according to the entered mix parts.

## Inputs

- **Work Thickness**: Concrete thickness.
- **Work Length**: Concrete length.
- **Work Width**: Concrete width.
- **Cement Sand Gravel Ratio**: Cement part of the concrete mix.
- **Sand Part**: Sand part of the concrete mix.
- **Gravel Part**: Gravel part of the concrete mix.
- **Mortar Dry Volume Factor**: Multiplier used to convert wet concrete volume to dry material volume.
- **Cement Bag Volume**: Volume represented by one bag of cement for bag conversion.
- **Skilled Labour**: Skilled productivity as volume per manday.
- **Unskilled Labour**: Unskilled productivity as volume per manday.

## Results

- **Cement**: Estimated cement quantity in `bag`.
- **Sand**: Estimated sand quantity in `cft`.
- **Gravel**: Estimated gravel quantity in `cft`.
- **CC Work Volume**: Total concrete work volume in `cft`.
- **Skilled Labour**: Estimated skilled labour effort in `manday`.
- **Unskilled Labour**: Estimated unskilled labour effort in `manday`.

## Understanding the Calculation

All entered dimensions are converted to inches internally.

1. Work volume:

$$V_{work}=L\times W\times T$$

2. Dry material volume:

$$V_{dry}=V_{work}\times f_{dry}$$

3. Mix parts total:

$$P=c+s+g$$

where $c$ is Cement Sand Gravel Ratio, $s$ is Sand Part, and $g$ is Gravel Part.

4. Material split:

$$V_{cement}=V_{dry}\times \frac{c}{P}$$

$$V_{sand}=V_{dry}\times \frac{s}{P}$$

$$V_{gravel}=V_{dry}\times \frac{g}{P}$$

Cement is converted to bags using Cement Bag Volume. Sand and gravel are converted to cubic feet for display.

5. Labour mandays:

$$M_{skilled}=\frac{V_{work}}{R_{skilled}}\quad , \quad M_{unskilled}=\frac{V_{work}}{R_{unskilled}}$$

where $R$ values are the entered productivity rates.

## Example

Example scenario:

- Work Length `10 ft`, Work Width `15 inch`, Work Thickness `3 inch`
- Mix parts: Cement Sand Gravel Ratio `1.0`, Sand Part `2.0`, Gravel Part `4.0`
- Mortar Dry Volume Factor `1.4`
- Labour productivity: Skilled `10 cft/manday`, Unskilled `10 cft/manday`

Expected interpretation:

- Increasing work dimensions increases all material outputs and labour mandays.
- Increasing Mortar Dry Volume Factor increases Cement, Sand, and Gravel.
- Increasing labour productivity rates decreases required mandays.

## Important Assumptions and Interpretation

- The work shape is modeled as a rectangular block.
- Mix parts are proportional shares of dry volume.
- Labour outputs are effort estimates from simple division, not project schedules.
- The function does not enforce explicit input validation for unrealistic values; use physically meaningful units and quantities.
- This step estimates quantities and effort, not direct money cost.
