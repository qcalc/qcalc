# Simple Currency Converter

## Purpose

Use the Simple Currency Converter to express an amount in one currency as an
equivalent amount in another currency, using qCalc's stored currency rates.

## Inputs

### Amount

Enter the amount to convert. You can enter a number or a simple qCalc
expression, such as `92/3+15`.

### From Currency

Choose the currency of the amount you entered.

### To Currency

Choose the currency in which to show the converted amount. The default value,
`UNC`, means your qCalc **Default Currency** preference.

## Results

### Converted Amount

This is the entered amount expressed in the selected target currency.

### Currency Rate as of

This shows the date and time of the currency-rate data used for the conversion.
Check this result when the timing of the rate matters.

## Example

To convert 100 US dollars to euros, enter `100` for **Amount**, enter `USD`
for **From Currency**, and `EUR` for **To Currency**. The converted
amount depends on the currency rate stored in qCalc at that time.

## Note

Currency rates change over time. qCalc updates its stored rate data at a set
frequency during the day, currently every couple of hours depending on the rate
provider. This calculator uses the rate data available in qCalc at the time of
conversion and is a conversion aid, not a quotation for a bank, card provider,
foreign-exchange service, or other transaction. Fees, exchange spreads, taxes,
and provider-specific rates are not included.