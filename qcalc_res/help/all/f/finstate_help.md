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

- **Figures In**: The unit and scale of the monetary figures, e.g. `1000 USD` for thousands of US dollars. For information only; it does not affect any calculation.
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

| Line Item | Acronym | Value | Formula |
|---|---:|---:|---|
| Sales |  | Input | Input value |
| Cost of Goods Sold |  | Input | Input value |
| Gross Profit |  | Calculated | = *Sales - Cost of Goods Sold* |
| Selling, General & Administrative Expenses | SG&A | Input | Input value |
| Other Operating Income |  | Input | Input value |
| Other Operating Expense |  | Input | Input value |
| Earnings Before Interest, Taxes, D&A | EBITDA | Calculated | = *Earnings Before Interest and Taxes + Depreciation & Amortization* |
| Depreciation & Amortization |  | Input | Input value |
| Earnings Before Interest and Taxes | EBIT | Calculated | = *Gross Profit - SG&A - Depreciation & Amortization + Other Operating Income - Other Operating Expense* |
| Interest Expense |  | Calculated | = *Long Term Debt × Interest Rate* |
| Earnings Before Taxes | EBT | Calculated | = *EBIT - Interest Expense* |
| Income Taxes |  | Calculated | = *Earnings Before Taxes × Tax Rate* |
| Net Income |  | Calculated | = *Earnings Before Taxes - Income Taxes* |

### Balance Sheet

The balance sheet is divided by heading rows (`=== ASSETS ===`, `=== LIABILITIES ===` and `=== EQUITY ===`).

The Acronym column is present for consistency with the income statement; it is filled only for commonly used acronyms.

| Line Item | Acronym | Value | Formula                                                  |
|---|---|---:|----------------------------------------------------------|
| Cash & Equivalents |  | Input | Input value                                              |
| Accounts Receivable | AR | Input | Input value                                              |
| Inventories |  | Input | Input value                                              |
| Total Current Assets |  | Calculated | = *Cash & Equivalents + Accounts Receivable + Inventories* |
| Net Property/Plant/Equipment |  | Input | Input value                                              |
| Total Assets |  | Calculated | = *Total Current Assets + Net Property/Plant/Equipment*    |
| Accounts Payable | AP | Input | Input value                                              |
| Total Current Liabilities |  | Calculated | = *Accounts Payable*                                       |
| Long Term Debt |  | Input | Input value                                              |
| Total Liabilities |  | Calculated | = *Total Current Liabilities + Long Term Debt*             |
| Common Stock |  | Input | Input value                                              |
| Retained Earnings |  | Input | Input value                                              |
| Total Stockholder's Equity |  | Calculated | = *Common Stock + Retained Earnings*                       |
| Total Liabilities & Equity |  | Calculated | = *Total Liabilities + Total Stockholder's Equity*         |

### Ratios

The ratio table is arranged in groups, each introduced by a heading row such as === LIQUIDITY ===. A ratio that cannot be defined because its denominator is zero (for example Interest Coverage for a company with no interest expense) shows **n/a**.

| Metric | Acronym | Value | Formula / Meaning |
|---|---:|---:|---|
| **=== PROFITABILITY ===** |  |  |  |
| Gross Margin |  | Percentage | = *Gross Profit / Sales* |
| EBITDA Margin |  | Percentage | = *EBITDA / Sales* |
| Operating Margin |  | Percentage | = *Earnings Before Interest and Taxes / Sales* |
| Net Margin |  | Percentage | = *Net Income / Sales* |
| SG&A % of Sales |  | Percentage | = *SG&A / Sales* |
| **=== RETURNS ===** |  |  |  |
| Return on Assets | ROA | Percentage | = *Net Income / Total Assets* |
| Return on Equity | ROE | Percentage | = *Net Income / Total Equity* |
| Net Operating Profit After Tax | NOPAT | Currency | = *Earnings Before Interest and Taxes × (1 - Tax Rate)* |
| Invested Capital = Interest Bearing Debt + Equity |  | Currency | = *Long Term Debt + Total Equity* |
| Return on Invested Capital | ROIC | Percentage | = *Net Operating Profit After Tax / Invested Capital* |
| Return on Net Operating Assets | RONA | Percentage | = *Net Operating Profit After Tax / Net Operating Assets* |
| **=== EFFICIENCY & WORKING CAPITAL ===** |  |  |  |
| Asset Turnover |  | Multiple | = *Sales / Total Assets* |
| Fixed Asset Turnover |  | Multiple | = *Sales / Net Property/Plant/Equipment* |
| Inventory Turnover |  | Multiple | = *Cost of Goods Sold / Inventories* |
| Accounts Receivable Turnover |  | Multiple | = *Sales / Accounts Receivable* |
| Accounts Payable Turnover |  | Multiple | = *Cost of Goods Sold / Accounts Payable* |
| Days Sales Outstanding | DSO | Days | = *Accounts Receivable / Sales × Period Days* |
| Days Inventory Outstanding | DIO | Days | = *Inventories / Cost of Goods Sold × Period Days* |
| Days Payables Outstanding | DPO | Days | = *Accounts Payable / Cost of Goods Sold × Period Days* |
| Cash Conversion Cycle | CCC | Days | = *DIO + DSO - DPO* |
| **=== LIQUIDITY ===** |  |  |  |
| Current Ratio |  | Multiple | = *Total Current Assets / Total Current Liabilities* |
| Quick Ratio |  | Multiple | = *(Cash & Equivalents + Accounts Receivable) / Total Current Liabilities* |
| Net Working Capital | NWC | Currency | = *Total Current Assets - Total Current Liabilities* |
| **=== LEVERAGE & SOLVENCY ===** |  |  |  |
| Debt-to-Equity | D/E | Multiple | = *Long Term Debt / Total Equity* |
| Liabilities-to-Assets |  | Multiple | = *Total Liabilities / Total Assets* |
| Equity Multiplier |  | Multiple | = *Total Assets / Total Equity* |
| Interest Coverage |  | Multiple | = *Earnings Before Interest and Taxes / Interest Expense* |
| Net Debt |  | Currency | = *Long Term Debt - Cash & Equivalents* |
| Net Debt / EBITDA |  | Multiple | = *Net Debt / EBITDA* (n/a when EBITDA is not positive) |
| **=== PER SHARE ===** |  |  |  |
| Earnings Per Share | EPS | Currency per share | = *Net Income / Shares Outstanding* |
| Book Value Per Share | BVPS | Currency per share | = *Total Equity / Shares Outstanding* |

## Why the Ratios Matter

### Profitability

- **Gross Margin**: how much of each sales unit remains after direct production cost. Higher usually means stronger pricing power or lower production cost.
- **EBITDA Margin**: operating profit before depreciation and amortization, useful for comparing businesses with different asset ages and depreciation policies.
- **Operating Margin**: operating profit kept after core operating expenses; a strong indicator of operating efficiency.
- **Net Margin**: how much of sales becomes bottom-line profit after interest and taxes; the clearest all-in profit measure.
- **SG&A % of Sales**: overhead burden. A rising share can signal weakening cost control.

### Returns

- **Return on Assets (ROA)**: how effectively the asset base is turned into profit, comparable between asset-heavy and capital-light businesses.
- **Return on Equity (ROE)**: profit earned for each unit of equity invested; especially relevant to shareholders. ROE = Net Margin × Asset Turnover × Equity Multiplier.
- **Net Operating Profit After Tax (NOPAT)**: operating profit after tax but before financing effects, for comparing companies with different capital structures.
- **Invested Capital**: long-term capital deployed in the business.
- **Return on Invested Capital (ROIC)**: operating profit generated from invested capital. Higher generally means more value created from the money tied up.
- **Return on Net Operating Assets (RONA)**: operating profit relative to the net operating asset base, after working-capital and fixed-asset investment.

### Efficiency & Working Capital

- **Asset Turnover** and **Fixed Asset Turnover**: sales generated per unit of total assets or of property/plant/equipment. Higher means better utilization.
- **Inventory Turnover**: how quickly inventory is sold and replaced. Higher generally means less cash tied up.
- **Accounts Receivable Turnover**: how quickly customers pay. Higher usually means faster collections.
- **Accounts Payable Turnover**: how quickly suppliers are paid. Lower can mean supplier credit is used for longer.
- **Days Sales Outstanding (DSO)**: approximate days sales remain uncollected. Lower usually means faster collections.
- **Days Inventory Outstanding (DIO)**: approximate days inventory is held before sale. Lower generally means leaner inventory.
- **Days Payables Outstanding (DPO)**: approximate days taken to pay suppliers. Higher often means supplier credit is used for longer.
- **Cash Conversion Cycle (CCC)**: approximate days cash is tied up between paying suppliers and collecting from customers (DIO + DSO - DPO). Lower generally means less cash locked in working capital; negative means suppliers effectively finance operations. Compare only between similar businesses.

### Liquidity

- **Current Ratio**: current assets per unit of current liabilities. Above 1 means short-term obligations are covered by short-term assets.
- **Quick Ratio**: like the current ratio but excluding inventory, a stricter test of near-term payment ability.
- **Net Working Capital (NWC)**: the absolute short-term cushion in currency.

### Leverage & Solvency

- **Debt-to-Equity** and **Liabilities-to-Assets**: how much of the business is financed by lenders rather than owners. Higher means more financial risk.
- **Equity Multiplier**: assets per unit of equity, the leverage component of ROE.
- **Interest Coverage**: how many times operating profit covers interest. Low coverage signals difficulty servicing debt.
- **Net Debt**: debt remaining after using cash. Negative means the company holds more cash than debt.
- **Net Debt / EBITDA**: roughly how many periods of EBITDA it would take to repay net debt.

### Per Share

- **Earnings Per Share (EPS)**: profit available per share; a familiar measure for equity valuation and comparison.
- **Book Value Per Share (BVPS)**: accounting equity per share.
## Notes on Interpretation

- Percentage ratios in the output are displayed as percentages with two decimal places.
- DSO, DIO, DPO, and CCC are only meaningful because the calculator includes a period length in months and converts it into an approximate number of days.
- EBITDA, EBIT, and EBT are accounting profitability stages rather than percentages.
- NOPAT, invested capital, net working capital, net debt, EPS, and BVPS are shown as value measures, not percentages.
- The calculator gives a compact financial summary; it does not replace a full audited financial model.

## Example

Using the default-style values in the calculator, the report can be read as follows:

- Sales are the starting revenue line.
- Cost of goods sold is subtracted to arrive at gross profit.
- SG&A, depreciation and amortization, and other operating items lead to EBITDA and EBIT.
- Interest expense takes EBIT to EBT.
- Taxes take EBT to net income.
- The balance sheet shows how the operating base is financed.
- The ratio table summarizes profitability, returns, efficiency and cash conversion, liquidity, leverage, and per-share measures.

This makes it easy to answer questions such as:

- Is the company generating enough operating profit?
- How much cash is tied up in receivables, inventory, and payables?
- Is the capital base producing an acceptable return?
- Are margins improving or weakening over the selected period?
