# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty

def buy_rent__info():
    return {
        'title': 'Buy vs Rent',
        'desc': (
            'Compare the present-value cost of buying an asset with renting '
            'it over the same period, including ownership costs, rent '
            'escalation, residual value and opportunity cost.'
        ),
        'schema': {
            'purchase_price': {
                'label': 'Purchase Price'
            },
            'use_period_years': {
                'label': 'Use Period'
            },
            'residual_value': {
                'label': 'Residual / Salvage Value'
            },
            'annual_ownership_cost': {
                'label': 'Annual Ownership Cost'
            },
            'monthly_rent': {
                'label': 'Monthly Rent'
            },
            'rent_escalation': {
                'label': 'Annual Rent Escalation'
            },
            'opportunity_return': {
                'label': 'Opportunity Return'
            },
        }
    }


def buy_rent(
    purchase_price='50000 USD',
    use_period_years=5,
    residual_value='10000 USD',
    annual_ownership_cost='1500 USD/yr',
    monthly_rent='1000 USD/mo',
    rent_escalation='3 pct/yr',
    opportunity_return='8 pct/yr',
):
    # ------------------------------------------------------------
    # Normalize inputs
    # ------------------------------------------------------------
    q_purchase = Qty(purchase_price).to('USD')
    q_residual = Qty(residual_value).to('USD')
    q_ownership = Qty(annual_ownership_cost).to('USD/yr')
    q_rent = Qty(monthly_rent).to('USD/mo')
    q_escalation = Qty(rent_escalation).to('pct/yr')
    q_return = Qty(opportunity_return).to('pct/yr')

    purchase = q_purchase.val
    residual = q_residual.val
    annual_ownership = q_ownership.val
    monthly_rent_val = q_rent.val

    years = int(use_period_years)

    rent_escalation_rate = q_escalation.val / 100.0
    opportunity_rate = q_return.val / 100.0

    # ------------------------------------------------------------
    # Monthly discount rate
    #
    # Convert effective annual opportunity return to an equivalent
    # monthly rate.
    # ------------------------------------------------------------
    monthly_discount = (
        (1.0 + opportunity_rate) ** (1.0 / 12.0) - 1.0
    )

    # ------------------------------------------------------------
    # Present value of annual ownership costs
    #
    # Ownership costs are assumed to occur at the end of each year.
    # ------------------------------------------------------------
    pv_ownership = 0.0

    for year in range(1, years + 1):
        pv_ownership += (
            annual_ownership
            / (1.0 + opportunity_rate) ** year
        )

    # ------------------------------------------------------------
    # Present value of residual value
    #
    # Residual value is received at the end of the use period.
    # ------------------------------------------------------------
    pv_residual = (
        residual
        / (1.0 + opportunity_rate) ** years
    )

    # ------------------------------------------------------------
    # Buy economic cost
    # ------------------------------------------------------------
    pv_buy_cost = (
        purchase
        + pv_ownership
        - pv_residual
    )

    # ------------------------------------------------------------
    # Present value of rent
    #
    # Rent is paid monthly at the end of each month.
    # Rent increases once per year.
    # ------------------------------------------------------------
    pv_rent = 0.0
    months = years * 12

    for month in range(1, months + 1):
        year_index = (month - 1) // 12

        rent = (
            monthly_rent_val
            * (1.0 + rent_escalation_rate) ** year_index
        )

        pv_rent += (
            rent
            / (1.0 + monthly_discount) ** month
        )

    # ------------------------------------------------------------
    # Buy vs rent difference
    #
    # Positive means renting costs more.
    # Negative means buying costs more.
    # ------------------------------------------------------------
    buy_advantage = pv_rent - pv_buy_cost

    # ------------------------------------------------------------
    # Break-even monthly rent
    #
    # Find the starting monthly rent whose PV equals the
    # economic cost of buying.
    #
    # Because rent escalation is independent of the initial rent,
    # the relationship is linear:
    #
    #     PV(rent) = initial_rent * rent_pv_factor
    # ------------------------------------------------------------
    rent_pv_factor = 0.0

    for month in range(1, months + 1):
        year_index = (month - 1) // 12

        escalation_factor = (
            (1.0 + rent_escalation_rate) ** year_index
        )

        rent_pv_factor += (
            escalation_factor
            / (1.0 + monthly_discount) ** month
        )

    break_even_monthly_rent = (
        pv_buy_cost / rent_pv_factor
        if rent_pv_factor > 0
        else 0.0
    )

    # ------------------------------------------------------------
    # Return results
    # ------------------------------------------------------------
    return {
        'Buy vs Rent': {
            'data': [
                [
                    'Initial Cost',
                    Qty(purchase, 'USD'),
                    Qty(0, 'USD'),
                    Qty(purchase, 'USD'),
                ],
                [
                    'PV of Ongoing Costs',
                    Qty(pv_ownership, 'USD'),
                    Qty(pv_rent, 'USD'),
                    Qty(pv_rent - pv_ownership, 'USD'),
                ],
                [
                    'PV of Residual Value',
                    Qty(-pv_residual, 'USD'),
                    Qty(0, 'USD'),
                    Qty(pv_residual, 'USD'),
                ],
                [
                    'Economic Cost (PV)',
                    Qty(pv_buy_cost, 'USD'),
                    Qty(pv_rent, 'USD'),
                    Qty(pv_rent - pv_buy_cost, 'USD'),
                ],
            ],
            'columns': ['Metric', 'Buy', 'Rent', 'Rent − Buy'],
        },

        'break_even_monthly_rent': Qty(
            break_even_monthly_rent, 'USD/mo'
        ),

        'buy_advantage': Qty(
            buy_advantage, 'USD'
        ),
    }
