# AC Running Cost

## Purpose

This calculator estimates how much electrical energy an air conditioner uses
and how much that energy costs. It is useful for testing different usage
patterns, electricity prices, and average operating loads.

The calculation uses the AC's rated electrical power. It does not use cooling
capacity such as BTU/h, and it does not calculate an efficiency rating such as
COP, EER, or SEER.

## Background

### Rated power and average operating load

Rated power is the electrical power shown for the AC when it is operating at
its rated load. Actual average power can be lower. A non-inverter AC may cycle
its compressor on and off, while an inverter AC may vary its power continuously.

The **Average operating load** input represents the average fraction of rated
power used during the stated usage. For example, `0.75` means that the
calculator estimates average power at 75% of the rated power.

## Inputs

### Rated electrical power

Enter the AC's electrical consumption, such as `1.2 kW` or `1200 W`. This is
electrical input power, not cooling capacity. The calculator converts it to
kilowatts before calculating.

The value must be non-negative.

### Usage per day

Enter the average AC usage with a time basis, such as `8 hr/day` or
`150 hr/mo` (if daily usage is not constatnt throughout the month).

### Electricity rate

Enter the effective electricity price, such as `0.12 USD/kWh`. The currency in
this input establishes the currency used for all cost results. 

This is a single effective rate. The calculator does not model utility tariff
slabs, taxes, fixed service charges, or different peak and off-peak rates.

### Average operating load

Enter a fraction from `0` to `1`. For example, `0.75` means 75% of rated
power on average. A value of `1` means the AC is estimated to use its rated
power throughout its usage; a value of `0` produces zero energy and cost.

The input is a load factor, not a COP, EER, SEER, or percentage efficiency
rating. Enter `75%` as `0.75` when using the decimal input field.

### Calculation period

Enter the number of days for the period estimate, such as `30 day`.

## Results

### Average Power Consumption

This is the rated power multiplied by the average operating load. It is shown
in `kW` and represents the estimated average electrical power while the AC is
being used.

### Energy per Hour

This is the estimated energy use for one hour of operation, shown in `kWh/hr`.

### Energy for Period

This is the estimated energy use over the selected **Calculation period** in
`kWh`.

### Cost per Period

This is the estimated cost over the selected **Calculation period**.

### Energy and Cost by Period

This table contains normalized daily, monthly, and yearly projections.

The table uses 30 days for a month and 365 days for a year. These projections
do not depend on the entered **Calculation period**.

## Understanding the Calculation

The calculator first converts rated power to `kW` and daily usage to `hr/day`.
It then applies the operating load:

$$
\text{average power} = \text{rated power} \times \text{operating load}
$$

Daily energy is estimated as:

$$
\text{daily energy} = \text{average power} \times \text{hours per day}
$$

The period energy result multiplies daily energy by the selected number of
days. The table's monthly and yearly energy values multiply daily energy by
30 days and 365 days respectively. Each energy result is expressed in `kWh`.

Cost is calculated by multiplying energy by the entered electricity rate:

$$
\text{cost} = \text{energy} \times \text{electricity rate}
$$

The period result uses the entered period. The table's monthly and yearly
costs use fixed 30-day and 365-day conventions.

## Example

Using the defaults:

- Rated electrical power: `1.2 kW`
- Usage per day: `8 hr/day`
- Electricity rate: `0.12 USD/kWh`
- Average operating load: `0.75`
- Calculation period: `30 day`

The estimated average power is `1.2 × 0.75 = 0.9 kW`. Daily energy is then
`0.9 × 8 = 7.2 kWh/day`. Over 30 days, the calculator estimates `216 kWh`.

At `0.12 USD/kWh`, the estimated cost is `0.864 USD/day` and `25.92 USD` for
the 30-day period. The table's normalized yearly estimate is `2,628 kWh` and
`315.36 USD/yr`.

## Important Assumptions and Interpretation

- The operating load is an average estimate supplied by the user. The
  calculator does not simulate compressor cycling, inverter behavior,
  thermostat settings, weather, room heat load, or changes in power over time.
- Changing a thermostat setting is represented only indirectly by changing
  **Usage per day** or **Average operating load**. There is no separate
  thermostat model.
- The calculation assumes the electricity rate remains constant throughout
  the selected period and the normalized month or year.
- Monthly and yearly results are projections, not readings from a meter or a
  utility bill.
- To compare two ACs, run the calculator once for each AC using the same usage,
  rate, and period, then compare their energy and cost results.