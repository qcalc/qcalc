# Unit Converter

## Purpose

Use the Unit Converter `conv2` to convert a value between compatible units, such as
length, mass, time, or temperature. It can also compare a measurement with a
qCalc reference quantity, such as the average distance between the Earth and
the Moon.

Select a quantity category first. qCalc then shows the units and, where
available, reference quantities that can be used for that category.

## Inputs

### Quantity

Choose the type of measurement to convert, such as length or mass. Changing
this selection updates the available units and reference quantities.

### Mode

Choose how to convert:

- **Unit -> Unit** converts a value from one unit to one or more compatible
  units.
- **Unit -> Quantity** shows how many of a selected reference quantity equal
  the entered value and unit.
- **Quantity -> Unit** converts a selected reference quantity into one or more
  units.
- **Quantity -> Quantity** compares one reference quantity with another.

The quantity-to-quantity modes are available only when qCalc has reference
quantities for the selected category.

### Value

Enter the number to convert. You can enter a number or a simple qCalc
expression, such as `92/3+15`.

### From Unit and To Units

For **Unit -> Unit**, choose one source unit and one or more target units.
For **Unit -> Quantity**, choose the source unit. For **Quantity -> Unit**,
choose one or more target units.

### From Quantity and To Quantity

In a quantity mode, select the reference quantity to compare. qCalc describes
each available reference quantity in the selection list.

### Unit Cost

For **Unit -> Unit**, you can enter a cost per source unit to calculate a total
cost for the entered value. Leave the default placeholder unchanged when no
cost calculation is needed.

## Results

### Conversion of

Shows the measurement category of the conversion.

### Converting from and Converting to

Show the selected source and target units or reference quantities.

### Converted Value

Shows the converted result. When more than one target unit is selected, qCalc
returns a result for each selected unit.

### Total Cost

For a unit-to-unit conversion with a unit cost, this shows the cost of the
entered amount. When no unit cost is supplied, there is no total-cost value to
use.

## Examples

To convert 5.5 feet to metres, choose **Length**, select **Unit -> Unit**, set
**Value** to `5.5`, select `ft` for **From Unit**, and select `m` for **To
Units**.

To compare a distance with the Earth-Moon distance, choose **Length**, select
**Unit -> Quantity**, enter a value and source unit, then choose **Average
distance between the Earth and the Moon** as the target quantity. The result
shows how many Earth-Moon distances are represented by the entered distance.

## Note

Only compatible units and quantities can be converted. The result is a unit
conversion based on qCalc's stored unit definitions; it does not account for
measurement uncertainty or context-specific standards.