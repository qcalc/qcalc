# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qcore import Qty
from qutil import nzv


def applepie__info(): return {'title': 'Ingredients of Apple Pie Recipe'}


def applepie(servings=8):
    # https://www.allrecipes.com/recipe/12682/apple-pie-by-grandma-ople/
    ingredients = {
        'number of servings': 8,
        'apples': Qty('8 ea'),
        'unsalted_butter': Qty('0.5 cup'),
        'flour': Qty('3 tblsp'),
        'white sugar': Qty('0.5 cup'),
        'brown sugar': Qty('0.5 cup'),
        'water': Qty('0.25 cup'),
        '9 inch pie pastry': Qty('1 ea')
    }
    factor = servings / 8.0
    ingredients.update((key, value * factor) for key, value in ingredients.items())
    return ingredients


def gold__info():
    return {
        'title': 'Estimate Cost of Gold Jewelry',
        'desc': 'Estimate cost of gold jewelry',  # | can be replaced from qfunc_info.json
        'schema': {
            'vat_pct': {'label': 'VAT %'},
            'making_charge_pct': {'label': 'Making Charge %'}
        },
        'anyof': {"1": {'fields': ['gold_weight_intl', 'gold_weight_india']}},
        # 'outcol': ['chart__r']
    }


def gold(
    gold_weight_intl='10.0 g', gold_weight_india='@vori, @anna, @roti, @point',
    gold_price='150 USD', gold_price_per='g', vat_pct=5.0, making_charge_pct=6.0
):
    vat_pct = nzv(vat_pct)
    making_charge_pct = nzv(making_charge_pct)

    qgold_weight_intl = Qty(gold_weight_intl)
    qgold_weight_india = Qty(gold_weight_india)
    qgold_price = Qty(f'{gold_price}/{gold_price_per}')
    if qgold_weight_intl.val is not None:
        qgold_weight = qgold_weight_intl
    else:
        qgold_weight = qgold_weight_india
    qgold_value = qgold_price * qgold_weight
    to_cur = Qty(gold_price).uom
    qgold_value = qgold_value.to(to_cur)
    qvat_on_gold = qgold_value * (vat_pct / 100.0)
    qmaking_charge = qgold_value * (making_charge_pct / 100.0)
    qgrand_total = qgold_value + qvat_on_gold + qmaking_charge
    # qc = pie_chart(
    #     "Gold, VAT, Making",
    #     f"{qgold_value.val},{qvat_on_gold.val},{qmaking_charge.val}",
    #     "Gold's Percentage of the Total Cost",
    #     True
    # )
    return {
        "gold_weight": qgold_weight,
        "gold_value": qgold_value,
        "vat_on_gold": qvat_on_gold,
        "making_charge": qmaking_charge,
        "grand_total": qgrand_total,
        # "chart": qc['chart']
    }
