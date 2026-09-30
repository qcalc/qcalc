# RCC Column Material Requirement

## Purpose

This calculator estimates reinforcement steel, concrete volume, sand volume, khoa volume, and stirrup count for an RCC column.

It is useful for early quantity planning when you have basic column dimensions and reinforcement bar details.

## Background

### What is included in this estimate

The estimate includes longitudinal bars and stirrups in total reinforcement steel. Concrete ingredient splitting uses a nominal mix assumption and a dry-volume factor built into the calculator logic.

## Inputs

- **Column Length**: Column height/length.
- **Column Width**: Column width.
- **Column Depth**: Column depth.
- **Number of longitudinal bars**: Count of main vertical bars.
- **Bar Size**: Diameter of longitudinal bars.
- **Stirrup Spacing**: Center-to-center spacing of stirrups.
- **Stirrup Size**: Diameter of stirrup bar.

## Results

- **Longitudinal steel**: Weight of main vertical reinforcement in `kg`.
- **Stirrup steel**: Weight of stirrup reinforcement in `kg`.
- **Total reinforcement steel**: Combined longitudinal + stirrup steel in `kg`.
- **Concrete volume**: Net concrete volume in `m3` after subtracting reinforcement volume.
- **Sand**: Sand volume in `m3` from nominal concrete mix assumptions.
- **Khoa**: Khoa (coarse aggregate) volume in `m3` from nominal concrete mix assumptions.
- **Number of stirrups**: Calculated stirrup count as an integer.

## Understanding the Calculation

The calculator uses these built-in assumptions from implementation metadata and code:

- Steel density: $7850\ \text{kg/m}^3$
- Nominal cover: $40\ \text{mm}$
- Concrete nominal mix: $1:1.5:3$
- Dry volume factor: $1.54$
- Stirrup hooks: total allowance $20d$ per stirrup (two hooks, $10d$ each)

Main steps:

1. Longitudinal steel:

$$L_{long}=L\times n$$

$$A_{bar}=\frac{\pi d_{bar}^2}{4}$$

$$W_{long}=A_{bar}\times L_{long}\times \rho_{steel}$$

2. Stirrup geometry:

$$b_s=b-2c-d_s$$

$$d_s'=d-2c-d_s$$

$$L_{st}=2b_s+2d_s'+20d_s$$

3. Stirrup count (including both ends):

$$N_{st}=\text{int}\left(\frac{L}{s}\right)+1$$

4. Stirrup steel weight:

$$W_{st}=\left(\frac{\pi d_s^2}{4}\times L_{st}\times N_{st}\right)\times \rho_{steel}$$

5. Concrete volume:

$$V_{gross}=L\times b\times d$$

$$V_{rebar}=V_{long}+V_{st}$$

$$V_{conc}=V_{gross}-V_{rebar}$$

6. Ingredient split from dry volume:

$$V_{dry}=V_{conc}\times 1.54$$

$$V_{sand}=V_{dry}\times \frac{1.5}{5.5}$$

$$V_{khoa}=V_{dry}\times \frac{3}{5.5}$$

## Example

Example scenario:

- Column Length `3 m`, Column Width `300 mm`, Column Depth `300 mm`
- Number of longitudinal bars `8`
- Bar Size `16 mm`
- Stirrup Spacing `150 mm`, Stirrup Size `8 mm`

Expected interpretation:

- Increasing column dimensions increases concrete and reinforcement requirements.
- Increasing Number of longitudinal bars or Bar Size increases longitudinal steel and total steel.
- Reducing Stirrup Spacing increases Number of stirrups and stirrup steel.

## Important Assumptions and Interpretation

- Longitudinal bar length is approximated as column length only; anchorage/lap is not included.
- Stirrup dimensions are center-line approximations from section size, cover, and stirrup diameter.
- Stirrup count uses `int(length / spacing) + 1`, including both ends.
- Concrete volume is net of reinforcement volume.
- Sand and Khoa are based on fixed nominal mix and fixed dry-volume factor in this implementation.
- Results are planning estimates and do not include design-code checks, seismic detailing rules, lap zoning, wastage allowances, or costing.
