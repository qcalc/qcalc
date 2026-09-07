# User Preferences

## Purpose

Use this calculator to save personal qCalc settings. These settings control
the appearance of qCalc, number formatting, calculator memory, search,
charts, and the maximum time allowed for a calculation.

Select the settings you want, then choose **Save**. qCalc confirms the change
with **Preferences Saved**.

## Appearance and Number Display

### Theme

Choose the visual theme used by qCalc.

### Interactive

Interactive mode applies only to calculators that support it. When enabled,
qCalc recalculates the result automatically when you change an input, so you
do not need to click on **Calculate** button.

### Decimal, Quantity Decimal, and Currency Decimal

Choose how many decimal places to show for ordinary numbers, quantities, and
currency values. Each setting accepts from 2 to 16 decimal places.

### Ignore Decimal Format

When enabled, qCalc displays values without applying the decimal-place format
preferences.

### Thousands Separator

Choose whether qCalc uses a thousands separator when displaying numbers.

### Exponent Threshold Min and Exponent Threshold Max

Set the range in which numbers are normally displayed as ordinary
decimal values. Values outside that range will be shown in scientific notation.
The minimum is from `1e-16` to `1e-6`; the maximum is from `1e9` to `1e16`.

### Default Currency

Choose the default currency unit used by qCalc where a default currency is
needed.

## Memory and Search

### Memory

Set how many calculator inputs qCalc can remember, from 0 to 100. Setting this
value to `0` clears the currently stored calculator memory when you save the
preferences.

### Fuzzy Search and Semantic Search

Enable or disable the corresponding search options in qCalc.

## Chart Settings

### Chart Color Scheme

Choose the colour scheme used for charts.

### Chart Width and Chart Height

Set the chart dimensions in pixels. Each value can be from 128 to 3000.

### Chart Legend

Choose where the legend appears on supported charts.

## Calculation Settings

### Strict Assign

When enabled, qCalc protects its built-in calculator names from assignment in
the expression console.

### Execution Timeout

Set the maximum time allowed for a calculator execution, in seconds. qCalc
limits this value to at least 1 second and no more than 900 seconds; an invalid
value uses the configured default before that limit is applied.

## Note

Preferences are saved for your user session and are applied to subsequent
calculator use. If you are logged in, preferences will be saved into your account. Formatting preferences change how numbers are displayed; they
do not change the underlying calculated values.