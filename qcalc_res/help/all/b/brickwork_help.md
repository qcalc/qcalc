# Estimate Brick, Cement and Sand for Brickwork

## Purpose

This calculator estimates the material quantities and labour effort for a rectangular brickwork volume. It helps you answer a practical planning question: for a given wall or block size, brick size, mortar assumptions, and wastage rate, how many bricks, how much cement and sand, and how many mandays of labour are required.

Use it as a quantity-estimation tool for planning and comparison. It does not directly calculate money cost in this step.

## Background

### What this estimate represents

Brickwork is treated as a solid rectangular work volume. The calculator estimates:

- Brick count based on brick dimensions plus mortar thickness around each brick.
- Mortar quantity from the gap between brick-with-mortar volume and brick-only volume.
- Cement and sand split from mortar dry volume using the entered cement-to-sand parts.
- Skilled and unskilled labour effort from entered productivity rates.

## Inputs

- **Brick Length**: Enter brick length.
- **Brick Width**: Enter brick width.
- **Brick Height**: Enter brick height.
- **Work Thickness**: Enter brickwork thickness.
- **Work Length**: Enter the work length.
- **Work Width**: Enter the work width.
- **Cement Sand Ratio**: Enter the cement part of the mortar mix ratio.
- **Sand Part**: Enter the sand part of the mortar mix ratio.
- **Mortar Dry Volume Factor**: Enter the dry-volume adjustment factor for mortar.
- **Mortar Thickness**: Enter mortar thickness used around the brick dimensions.
- **Cement Bag Volume**: Enter bag volume for cement conversion.
- **Brick Wastage**: Enter expected brick wastage as a fraction or percent.
- **Skilled Labour**: Enter skilled labour productivity as volume per manday.
- **Unskilled Labour**: Enter unskilled labour productivity as volume per manday.

## Results

- **Brick**: Estimated total number of bricks (`nos`) after wastage is applied.
- **Cement**: Estimated cement requirement (`bag`) from the mortar dry volume and entered mix parts.
- **Sand**: Estimated sand requirement (`cft`) from the mortar dry volume and entered mix parts.
- **Brick Work Volume**: Total brickwork volume (`cft`) from work length, width, and thickness.
- **Skilled Labour**: Estimated skilled labour (`manday`) from work volume divided by skilled productivity.
- **Unskilled Labour**: Estimated unskilled labour (`manday`) from work volume divided by unskilled productivity.

## Understanding the Calculation

The calculator converts dimensional inputs to inches internally, then computes work and material quantities.

1. Brick volumes:

- Brick-only volume:
  
  $$V_{brick}=L_b\times W_b\times H_b$$

- Brick-with-mortar volume:
  
  $$V_{bm}=(L_b+t_m)\times(W_b+t_m)\times(H_b+t_m)$$

2. Work volume:

$$V_{work}=L_w\times W_w\times T_w$$

3. Bricks used before wastage:

$$N_{used}=\frac{V_{work}}{V_{bm}}$$

4. Total brick count after wastage:

$$N_{total}=\text{int}\left(N_{used}\times(1+w)\right)$$

where $w$ is brick wastage in unit form (for example, `7 pct` = 0.07).

5. Mortar wet volume:

$$V_{mortar,wet}=(V_{bm}-V_{brick})\times N_{used}$$

6. Mortar dry volume:

$$V_{mortar,dry}=V_{mortar,wet}\times f_{dry}$$

7. Cement and sand split (for cement part $c$ and sand part $s$):

$$V_{cement}=\frac{V_{mortar,dry}\times c}{c+s}$$

$$V_{sand}=\frac{V_{mortar,dry}\times s}{c+s}$$

Cement is converted to bags using Cement Bag Volume. Sand is reported in cubic feet.

8. Labour mandays:

$$M_{skilled}=\frac{V_{work}}{R_{skilled}}\quad , \quad M_{unskilled}=\frac{V_{work}}{R_{unskilled}}$$

where $R$ values are entered labour productivity rates.

## Example

Example scenario:

- Work Length `10 ft`, Work Width `7 ft`, Work Thickness `5.5 inch`
- Brick size `9.5 inch x 4.5 inch x 2.75 inch`
- Mortar Thickness `0.5 inch`, Mortar Dry Volume Factor `1.4`
- Mix parts: Cement Sand Ratio `1.0`, Sand Part `4.0`
- Brick Wastage `7 pct`
- Labour productivity: Skilled `30 cft/manday`, Unskilled `20 cft/manday`

Expected interpretation:

- `Brick` increases if work volume increases or brick dimensions decrease.
- `Cement` and `Sand` increase if mortar thickness, dry volume factor, or work volume increases.
- `Skilled Labour` and `Unskilled Labour` increase if work volume increases, and decrease if productivity rates are higher.

## Important Assumptions and Interpretation

- The model treats the work as a rectangular solid with uniform thickness.
- Mortar thickness is applied to all three brick dimensions for brick-with-mortar volume.
- Brick count is truncated to an integer using `int(...)` after wastage is applied.
- Cement and sand are estimated from entered ratio parts and dry-volume factor; changing those assumptions can materially change output.
- Labour results are effort estimates in mandays from simple productivity division; they are not crew-size schedules.
- No explicit input-range validation is applied in this function for non-physical or extreme values. Enter realistic values and units.
- This result is a planning estimate and does not include price, logistics, site loss beyond entered wastage, or quality/workmanship effects.