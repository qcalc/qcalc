# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty


def working_capital__info():
    return {
        'title': 'Working Capital & Cash Conversion Cycle',
        'desc': (
            'Calculate DSO, DIO, DPO, Cash Conversion Cycle and operating '
            'working capital, and estimate additional financing caused by '
            'changes in customer and supplier payment terms.'
        ),
        'schema': {
            'annual_sales': {
                'label': 'Annual Sales'
            },
            'annual_cogs': {
                'label': 'Annual COGS'
            },
            'average_inventory': {
                'label': 'Average Inventory'
            },
            'average_receivables': {
                'label': 'Average Receivables'
            },
            'average_payables': {
                'label': 'Average Payables'
            },
            'current_customer_terms': {
                'label': 'Current Customer Payment Terms'
            },
            'scenario_customer_terms': {
                'label': 'Scenario Customer Payment Terms'
            },
            'current_supplier_terms': {
                'label': 'Current Supplier Payment Terms'
            },
            'scenario_supplier_terms': {
                'label': 'Scenario Supplier Payment Terms'
            },
        }
    }


def working_capital(
    annual_sales='1000000 USD/yr',
    annual_cogs='600000 USD/yr',
    average_inventory='100000 USD',
    average_receivables='150000 USD',
    average_payables='80000 USD',
    current_customer_terms=45,
    scenario_customer_terms=60,
    current_supplier_terms=30,
    scenario_supplier_terms=45,
):
    # ------------------------------------------------------------
    # Normalize inputs
    # ------------------------------------------------------------
    q_sales = Qty(annual_sales).to('USD/yr')
    q_cogs = Qty(annual_cogs).to('USD/yr')
    q_inventory = Qty(average_inventory).to('USD')
    q_receivables = Qty(average_receivables).to('USD')
    q_payables = Qty(average_payables).to('USD')

    sales = q_sales.val
    cogs = q_cogs.val
    inventory = q_inventory.val
    receivables = q_receivables.val
    payables = q_payables.val

    current_customer_terms = float(current_customer_terms)
    scenario_customer_terms = float(scenario_customer_terms)
    current_supplier_terms = float(current_supplier_terms)
    scenario_supplier_terms = float(scenario_supplier_terms)

    # ------------------------------------------------------------
    # Actual historical operating metrics
    # ------------------------------------------------------------
    dso = receivables / sales * 365
    dio = inventory / cogs * 365
    dpo = payables / cogs * 365

    ccc = dso + dio - dpo

    # Actual operating working capital:
    # Receivables + Inventory - Payables
    current_wc = receivables + inventory - payables

    # ------------------------------------------------------------
    # Term-based working capital
    #
    # This isolates the effect of payment terms from the
    # actual balance-sheet DSO/DPO.
    # ------------------------------------------------------------
    daily_sales = sales / 365
    daily_cogs = cogs / 365

    current_term_receivables = (
        daily_sales * current_customer_terms
    )

    scenario_term_receivables = (
        daily_sales * scenario_customer_terms
    )

    current_term_payables = (
        daily_cogs * current_supplier_terms
    )

    scenario_term_payables = (
        daily_cogs * scenario_supplier_terms
    )

    current_term_wc = (
        current_term_receivables
        + inventory
        - current_term_payables
    )

    scenario_term_wc = (
        scenario_term_receivables
        + inventory
        - scenario_term_payables
    )

    # ------------------------------------------------------------
    # Financing impact caused by changing payment terms
    # ------------------------------------------------------------
    customer_financing_change = (
        scenario_term_receivables
        - current_term_receivables
    )

    supplier_financing_change = (
        current_term_payables
        - scenario_term_payables
    )

    additional_financing = (
        customer_financing_change
        + supplier_financing_change
    )

    # Equivalent direct formula:
    # + customer delay increases financing
    # - supplier delay decreases financing
    term_change_wc = (
        daily_sales
        * (scenario_customer_terms - current_customer_terms)
        - daily_cogs
        * (scenario_supplier_terms - current_supplier_terms)
    )

    # ------------------------------------------------------------
    # Scenario CCC
    # ------------------------------------------------------------
    scenario_dso = scenario_customer_terms
    scenario_dpo = scenario_supplier_terms

    scenario_ccc = (
        scenario_dso
        + dio
        - scenario_dpo
    )

    ccc_change = scenario_ccc - ccc

    # ------------------------------------------------------------
    # Return results
    # ------------------------------------------------------------
    return {
        'Actual vs Scenario': {
            'data': [
                ['DSO', Qty(dso, 'day'), Qty(scenario_dso, 'day'),
                 Qty(scenario_dso - dso, 'day')],

                ['DIO', Qty(dio, 'day'), Qty(dio, 'day'),
                 Qty(0, 'day')],

                ['DPO', Qty(dpo, 'day'), Qty(scenario_dpo, 'day'),
                 Qty(scenario_dpo - dpo, 'day')],

                ['Cash Conversion Cycle',
                 Qty(ccc, 'day'),
                 Qty(scenario_ccc, 'day'),
                 Qty(ccc_change, 'day')],

                ['Operating Working Capital Requirement',
                 Qty(current_wc, 'USD'),
                 Qty(scenario_term_wc, 'USD'),
                 Qty(term_change_wc, 'USD')],
            ],
            'columns': ['Metric', 'Actual', 'Scenario', 'Change'],
        },
        'Additional Financing Required': Qty(
            additional_financing, 'USD'
        )}
