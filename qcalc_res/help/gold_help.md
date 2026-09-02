# Estimate Cost of Gold Jewelry

## Overview

The **Estimate Cost of Gold Jewelry** calculator estimates the total
cost of a gold jewelry item from its gold weight and gold price.

The calculation includes:

-   value of the gold;
-   VAT;
-   making charge;
-   grand total.

You can enter the gold weight using either **international units**, such
as grams, or **traditional units**, such as vori, anna, roti, and point.

## Inputs

### Gold Weight

Enter the weight of the gold.

Two weight input methods are available:

-   **International weight** --- for example, `10 g`
-   **Traditional weight** --- using `vori`, `anna`, `roti`, and `point`

Only one weight input is used. If an international weight is provided,
the traditional weight values if any will be cleared out and vice versa.

For example:

``` text
10 g
```

or:

``` text
1 vori, 2 anna, 3 roti, 4 point
```

### Gold Price

Enter the gold price.

### Gold Price Per

Specify the weight unit to which the gold price applies.

For example:

``` text
Gold Price = 79 USD
Gold Price Per = g
```

means 79 USD per gram.

### VAT %

Enter the VAT percentage applied to the gold value.

For example, `5` means 5% VAT.

### Making Charge %

Enter the making-charge percentage applied to the gold value.

For example, `6` means a 6% making charge.

## How the calculation works

The calculator first determines the gold weight from the selected weight
input.

It then calculates:

**Gold Value = Gold Price × Gold Weight**

VAT is calculated as:

**VAT = Gold Value × VAT % / 100**

The making charge is calculated as:

**Making Charge = Gold Value × Making Charge % / 100**

Finally:

**Grand Total = Gold Value + VAT + Making Charge**

The calculated values are expressed in the currency represented by the
entered gold price.

## Results

### Gold Weight

The gold weight used in the calculation.

If traditional units are entered, qCalc handles the quantity conversion
automatically.

### Gold Value

The estimated value of the gold itself, before VAT and making charge.

### VAT on Gold

The VAT amount calculated from the gold value and the VAT percentage.

### Making Charge

The making charge calculated from the gold value and the making-charge
percentage.

### Grand Total

The estimated total cost:

``` text
Gold Value + VAT + Making Charge
```

This is the main result of the calculator.


## Traditional gold-weight units

The calculator can work with traditional gold-weight quantities using:

-   **vori**
-   **anna**
-   **roti**
-   **point**

You can enter a combination such as:

``` text
1 vori, 2 anna, 3 roti, 4 point
```

The quantity is interpreted by qCalc and used directly in the gold-value
calculation.

## Important considerations

This calculator provides an **estimate based on the supplied inputs**.

Actual jewelry prices may differ because a jeweler may apply additional
charges or pricing rules that are not included here.

The calculator specifically accounts for:

-   gold value;
-   VAT;
-   making charge.

Other possible charges, discounts, wastage, stones or gemstones,
additional labor charges, or other adjustments are not included.

VAT and making charge are both calculated **on the gold value**.

## Interpreting the result

The **Gold Value** represents the underlying value of the gold.

**VAT on Gold** and **Making Charge** are additional amounts calculated
from that gold value.

The **Grand Total** is the sum of all three.

When comparing jewelry offers, it can therefore be useful to compare the
gold price, VAT, and making-charge percentage separately rather than
comparing only the final total.
