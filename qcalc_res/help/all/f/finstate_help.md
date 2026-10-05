# Financial Statements Builder

## Purpose

`finstate()` builds a compact pro-forma financial statement model from a small set of inputs and presents the main profitability, efficiency, and cash-conversion metrics in a single report.

Use it when you want a quick statement-style summary of a business period without building a full spreadsheet model. The calculator is especially useful for:

- checking whether a business is generating enough operating profit,
- comparing sales, cost structure, and financing burden across a period,
- reviewing the balance-sheet snapshot behind the results, and
- seeing the main valuation-style ratios in one place.

## Background

The calculator separates the model into a few practical groups:

- **Basis**: tax rate, interest rate, and period length in months.
- **Operating Inputs**: sales, cost of goods sold, selling, general and administrative expenses, and depreciation and amortization.
- **Balance Inputs**: cash, receivables, inventory, property, payables, debt, and equity items.
- **Additional Drivers**: other operating income, other operating expense, and shares outstanding.

From those inputs, the calculator builds an income statement, a balance sheet, and a ratio table. The outputs are designed to be read like a management summary rather than a raw accounting ledger.

## Attribution

The default values and overall design of `finstate()` draw on material from the *MITx MicroMasters in Supply Chain Management* program offered by the **MIT Center for Transportation and Logistics**.

## Inputs

### Basis

- **Tax Rate**: The percentage of pre-tax profit paid as tax.
- **Interest Rate**: The rate used to estimate interest expense on long-term debt.
- **Period (Months)**: The length of the reporting period used to convert turnover ratios into day-based measures such as DSO, DIO, and DPO.

### Operating Inputs

- **Sales**: Revenue for the reporting period.
- **Cost of Goods Sold**: Direct cost of producing or buying the goods sold in the period.
- **SG&A Expense**: Selling, general, and administrative expense.
- **Depreciation & Amortization**: Non-cash operating expense that spreads asset cost over time.

### Balance Inputs

- **Cash & Equivalents**: Liquid cash resources.
- **Accounts Receivable**: Amount owed by customers.
- **Inventories**: Stock on hand not yet sold.
- **Net Property/Plant/Equipment**: Net book value of long-lived productive assets.
- **Accounts Payable**: Amount owed to suppliers.
- **Long Term Debt**: Interest-bearing long-term borrowings.
- **Common Stock**: Paid-in equity capital.
- **Retained Earnings**: Cumulative undistributed profit retained in the business.

### Additional Drivers

- **Other Operating Income**: Extra operating income outside the core sales line.
- **Other Operating Expense**: Extra operating cost outside the core cost lines.
- **Shares Outstanding**: Used to compute earnings per share.

## Output Structure

The calculator returns three tables:

- **Income Statement**: A period-based statement of profit and loss.
- **Balance Sheet**: A period-end asset, liability, and equity snapshot.
- **Ratios**: Performance, efficiency, and cash-conversion metrics.

## Representative Output Table

The representative tables below show the formula beside each calculated row, so the guide stays close to the report layout.

### Income Statement

| Line Item | Acronym | Period | Formula |
|---|---:|---:|---|
| Sales |  | Input | Input value |
| Cost of Goods Sold |  | Input | Input value |
| Gross Profit |  | Calculated | = *Sales - Cost of Goods Sold* |
| Selling, General and Administrative Expenses | SG&A | Input | Input value |
| Other Operating Income |  | Input | Input value |
| Other Operating Expense |  | Input | Input value |
| Earnings Before Interest, Taxes, Depreciation and Amortization | EBITDA | Calculated | = *Earnings Before Interest and Taxes + Depreciation & Amortization* |
| Depreciation & Amortization |  | Input | Input value |
| Earnings Before Interest and Taxes | EBIT | Calculated | = *Gross Profit - SG&A - Depreciation & Amortization + Other Operating Income - Other Operating Expense* |
| Interest Expense |  | Calculated | = *Long Term Debt × Interest Rate* |
| Earnings Before Taxes | EBT | Calculated | = *EBIT - Interest Expense* |
| Income Taxes |  | Calculated | = *Earnings Before Taxes × Tax Rate* |
| Net Income |  | Calculated | = *Earnings Before Taxes - Income Taxes* |

### Balance Sheet

| Line Item | Period | Formula                                                  |
|---|---:|----------------------------------------------------------|
| Cash & Equivalents | Input | Input value                                              |
| Accounts Receivable | Input | Input value                                              |
| Inventories | Input | Input value                                              |
| Total Current Assets | Calculated | = *Cash & Equivalents + Accounts Receivable + Inventories* |
| Net Property/Plant/Equipment | Input | Input value                                              |
| Total Assets | Calculated | = *Total Current Assets + Net Property/Plant/Equipment*    |
| Accounts Payable | Input | Input value                                              |
| Total Current Liabilities | Calculated | = *Accounts Payable*                                       |
| Long Term Debt | Input | Input value                                              |
| Total Liabilities | Calculated | = *Total Current Liabilities + Long Term Debt*             |
| Common Stock | Input | Input value                                              |
| Retained Earnings | Input | Input value                                              |
| Total Stockholder's Equity | Calculated | = *Common Stock + Retained Earnings*                       |
| Total Liabilities & Equity | Calculated | = *Total Liabilities + Total Stockholder's Equity*         |

### Ratios

| Metric | Acronym | Value | Formula / Meaning |
|---|---:|---:|---|
| Gross Margin |  | Percentage | = *Gross Profit / Sales* |
| Operating Margin |  | Percentage | = *Earnings Before Interest and Taxes / Sales* |
| Net Margin |  | Percentage | = *Net Income / Sales* |
| Asset Turnover |  | Multiple | = *Sales / Total Assets* |
| Inventory Turnover |  | Multiple | = *Cost of Goods Sold / Inventories* |
| Accounts Receivable Turnover |  | Multiple | = *Sales / Accounts Receivable* |
| Accounts Payable Turnover |  | Multiple | = *Cost of Goods Sold / Accounts Payable* |
| Days Sales Outstanding | DSO | Days | = *Accounts Receivable / Sales × Period Days* |
| Days Inventory Outstanding | DIO | Days | = *Inventories / Cost of Goods Sold × Period Days* |
| Days Payables Outstanding | DPO | Days | = *Accounts Payable / Cost of Goods Sold × Period Days* |
| Return on Assets | ROA | Percentage | = *Net Income / Total Assets* |
| Return on Equity | ROE | Percentage | = *Net Income / Total Equity* |
| Net Operating Profit After Tax | NOPAT | Currency | = *Earnings Before Interest and Taxes × (1 - Tax Rate)* |
| Invested Capital = Interest Bearing Debt + Equity |  | Currency | = *Long Term Debt + Total Equity* |
| Return on Invested Capital | ROIC | Percentage | = *Net Operating Profit After Tax / Invested Capital* |
| Return on Net Operating Assets | RONA | Percentage | = *Net Operating Profit After Tax / Net Operating Assets* |
| Earnings Per Share | EPS | Currency per share | = *Net Income / Shares Outstanding* |

## Why the Ratios Matter

### Gross Margin

Shows how much of each sales unit remains after direct production cost. A higher gross margin usually means stronger pricing power or lower production cost.

### Operating Margin

Shows how much operating profit the business keeps after core operating expenses. It is a strong indicator of operating efficiency.

### Net Margin

Shows how much of sales becomes bottom-line profit after interest and taxes. It is the clearest all-in profit measure for the period.

### Asset Turnover

Shows how efficiently the company uses assets to generate sales. Higher turnover usually means better asset utilization.

### Inventory Turnover

Shows how quickly inventory is sold and replaced. A higher number generally means inventory is moving faster and less cash is tied up.

### Accounts Receivable Turnover

Shows how quickly the company collects from customers. A higher number usually means faster collections.

### Accounts Payable Turnover

Shows how quickly the company pays suppliers. Lower turnover can mean the company is using supplier credit for longer.

### Days Sales Outstanding (DSO)

Shows the approximate number of days sales remain uncollected.
A lower DSO usually means faster customer collections and less cash tied up in receivables.

### Days Inventory Outstanding (DIO)

Shows the approximate number of days inventory remains on hand before being sold.
A lower DIO generally means leaner inventory management.

### Days Payables Outstanding (DPO)

Shows the approximate number of days the company takes to pay suppliers.
A higher DPO often means the business is using supplier credit for longer.

### Return on Assets (ROA)

Shows how effectively the company turns its asset base into profit.
It is useful for comparing asset-heavy businesses and capital-light businesses on a normalized basis.

### Return on Equity (ROE)

Shows how much profit is earned for each unit of equity invested.
It is especially useful for owners and shareholders because it measures the return on the capital they have provided.

### Net Operating Profit After Tax (NOPAT)

Shows operating profit after tax but before financing effects.
It is useful when comparing operational performance across companies with different capital structures.

### Invested Capital

Shows the amount of long-term capital deployed in the business.
This helps frame the scale of the capital base used to generate operating returns.

### Return on Invested Capital (ROIC)

Shows how efficiently the company generates operating profit from invested capital.
A higher ROIC generally means the business is creating more value from the money tied up in the operation.

### Return on Net Operating Assets (RONA)

Measures operating profit relative to the net operating asset base.
This is useful for understanding how well operating assets are being used after working-capital and fixed-asset investment.

### Earnings Per Share (EPS)

Shows profit available per share of stock.
This is one of the most familiar per-share profitability measures and is useful for equity valuation and comparison.

## Notes on Interpretation

- Percentage ratios in the output are displayed as percentages with two decimal places.
- DSO, DIO, and DPO are only meaningful because the calculator includes a period length in months and converts it into an approximate number of days.
- EBITDA, EBIT, and EBT are accounting profitability stages rather than percentages.
- NOPAT, invested capital, and EPS are shown as value measures, not percentages.
- The calculator gives a compact financial summary; it does not replace a full audited financial model.

## Example

Using the default-style values in the calculator, the report can be read as follows:

- Sales are the starting revenue line.
- Cost of goods sold is subtracted to arrive at gross profit.
- SG&A, depreciation and amortization, and other operating items lead to EBITDA and EBIT.
- Interest expense takes EBIT to EBT.
- Taxes take EBT to net income.
- The balance sheet shows how the operating base is financed.
- The ratio table summarizes profitability, efficiency, cash conversion, and capital productivity.

This makes it easy to answer questions such as:

- Is the company generating enough operating profit?
- How much cash is tied up in receivables, inventory, and payables?
- Is the capital base producing an acceptable return?
- Are margins improving or weakening over the selected period?
