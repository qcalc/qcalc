# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from math import ceil

from calc import QCost
from qcore import Qty
from qutil import cal_link, calurl, when_show

RATE_DOMAIN = 'apiculture'
# DEFAULT_SYRUP_RATE = '0.5 L/unit/day'
# DEFAULT_DRY_SUGAR_RATE = '0.5 kg/unit/day'
COST_SPEC = 'Sugar, Water, Feeding Labour'
COST_HELP = 'Price sugar, water and labour with your saved Schedule of Rates (illustrative rates are used until you save one).'
SHOW_RATES_BUTTON = cal_link(
    calurl('rates', f'rate_domain/{RATE_DOMAIN}'),
    f'Show Rates: {RATE_DOMAIN.title()}',
    'btn btn-info btncmd',
    button=True,
)


def _syrup_density_kg_per_litre(concentration_pct: float) -> float:
    # Sucrose solution fit near room temperature (20 C), C in % by weight.
    return 0.99823 + 0.003734 * concentration_pct + 0.00001789 * concentration_pct ** 2


def bee_feeding__info():
    return {
        'title': 'Bee Colony Feeding Requirement and Cost',
        'desc': (
            'Estimate syrup or dry sugar requirement for a colony count and feeding plan. '
            'For syrup, sugar concentration is weight-based and density can be entered or auto-estimated.'
        ),
        'rate_domain': RATE_DOMAIN,
        'schema': {
            'colonies': {
                'help_text': 'Colony count as a unit quantity, for example 50 unit.',
            },
            'feed_type': {'type': 'radio', 'choices': {'syrup': 'Sugar syrup', 'dry': 'Dry sugar'}, 'initial': 'syrup'},
            'sugar_concentration': {
                'help_text': 'Syrup only. Sugar share by weight.',
            },
            'syrup_density': {
                'help_text': 'Syrup only. Leave blank to estimate from concentration (kg/L).',
            },
            'include_cost': {'help_text': COST_HELP},
        },
        'showhide': {
            'feed_type': when_show({
                'syrup': ['syrup_rate_per_colony', 'sugar_concentration', 'syrup_density', 'batch_size'],
                'dry': 'dry_rate_per_colony',
            }),
        },
        'inserts': {'form_bottom': SHOW_RATES_BUTTON},
        'tags': 'beekeeping, apiculture, feeding, syrup, sugar, cost',
    }


def bee_feeding(
    colonies='50 unit',
    feeding_duration='10 day',
    feeding_interval='1 day',
    feed_type='syrup',
    syrup_rate_per_colony='0.5 L/unit/day',
    sugar_concentration='50 pct',
    syrup_density='',
    batch_size='100 L',
    dry_rate_per_colony='0.5 kg/unit/day',
    labour_productivity='250 unit/manday',
    other_expenses='0 pct',
    include_cost=False,
):
    colonies_unit = Qty(colonies, 'unit')
    duration_days = Qty(feeding_duration, 'day')
    interval_days = Qty(feeding_interval, 'day')
    if interval_days.val <= 0:
        raise Exception('feeding_interval must be greater than zero.')
    feedings = ceil(duration_days.val / interval_days.val)

    result = {
        'Total Feedings': Qty(feedings, 'unit'),
    }

    if str(feed_type).strip().lower() == 'dry':
        daily_rate = Qty(dry_rate_per_colony, 'kg/unit/day')
        daily_dry_sugar = colonies_unit.val * daily_rate.val
        total_dry_sugar = daily_dry_sugar * duration_days.val
        per_feeding = total_dry_sugar / feedings
        result.update({
            'Daily Feed Requirement': Qty(daily_dry_sugar, 'kg/day'),
            'Per Feeding Requirement': Qty(per_feeding, 'kg'),
            'Total Dry Sugar': Qty(total_dry_sugar, 'kg'),
            'Sugar': Qty(total_dry_sugar, 'kg'),
            'Water': Qty(0, 'L'),
            'Feed Type': 'Dry sugar',
        })
    else:
        daily_rate = Qty(syrup_rate_per_colony, 'L/unit/day')
        sugar_fraction = Qty(sugar_concentration, 'unit').val
        if sugar_fraction < 0 or sugar_fraction > 1:
            raise Exception('sugar_concentration must be between 0 pct and 100 pct.')
        density = Qty(syrup_density, 'kg/L').val if str(syrup_density).strip() else _syrup_density_kg_per_litre(
            sugar_fraction * 100)
        total_syrup = colonies_unit.val * daily_rate.val * duration_days.val
        syrup_mass = total_syrup * density
        sugar_mass = syrup_mass * sugar_fraction
        water_litre = syrup_mass - sugar_mass  # Approximation: 1 kg water ~= 1 L
        per_feeding = total_syrup / feedings
        batch_litre = Qty(batch_size, 'L').val
        if batch_litre <= 0:
            raise Exception('batch_size must be greater than zero.')
        result.update({
            'Daily Feed Requirement': Qty(colonies_unit.val * daily_rate.val, 'L/day'),
            'Per Feeding Requirement': Qty(per_feeding, 'L'),
            'Total Syrup': Qty(total_syrup, 'L'),
            'Syrup Density': Qty(density, 'kg/L'),
            'Syrup Mass': Qty(syrup_mass, 'kg'),
            'Sugar': Qty(sugar_mass, 'kg'),
            'Water': Qty(water_litre, 'L'),
            'Mixing Batches': Qty(ceil(total_syrup / batch_litre), 'unit'),
            'Feed Type': 'Sugar syrup',
        })

    colonies_per_manday = Qty(labour_productivity, 'unit/manday').val
    if colonies_per_manday <= 0:
        raise Exception('labour_productivity must be greater than zero.')
    labour_manday = colonies_unit.val * feedings / colonies_per_manday
    result['Feeding Labour'] = Qty(labour_manday, 'manday')

    if include_cost:
        cost = QCost.from_result(result, COST_SPEC, rate_domain=RATE_DOMAIN)
        cost.overhead('Other Expenses', other_expenses)
        result.update(cost.results(per=colonies_unit, per_label='Colony'))
    return result
