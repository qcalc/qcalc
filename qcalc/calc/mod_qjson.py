# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import sys
from qcore import add_measurement_units, add_quantities
from qvars import qfunc_info, qty_categ_info, unit_info, qfunc_categ_info
from qutil import load_json
from .mod_currency import CurrencyLoader
from .mod_cred_quota import load_provider_quotas
import logging

logger = logging.getLogger(__name__)

cur_loader = CurrencyLoader()

activity_choice = {
    'type': 'choice',
    'initial': 1.2,
    'choices':
        {
            1.0: 'Basal Metabolic Rate (BMR)',
            1.2: 'Sedentary: little or no exercise',
            1.375: 'Light: exercise 1-3 times/week',
            1.465: 'Moderate: exercise 4-5 times/week',
            1.55: 'Active: daily exercise or intense exercise 3-4 times/week',
            1.725: 'Very Active: intense exercise 6-7 times/week',
            1.90: 'Extra Active: very intense exercise daily, or physical job',
        }
}

calorie_formula_choice = {
    'type': 'radio',
    'initial': 'M',
    'choices':
        {
            'M': 'Miffin St Jeor',
            'H': 'Revised Harris-Benedict',
            'K': 'Katch McArdle'
        },
}


def dict2options(lst, **kwargs):
    for key, value in kwargs.items():
        lst[key] = value
    return lst


class StdJson:
    initialized = False
    autofill1 = {}  # demo json
    autofill1data = {}  # demo json
    autofill2 = {}  # demo json
    autofill2data = {}  # demo json
    related1 = {}  # demo json
    related1data = {}  # demo json
    texts = {}  # qCalc title, desc
    themes = {}  # qCalc themes
    timezones = {}  # not used

    @classmethod
    def w1_load_json_once_per_worker(cls):
        cls.autofill1 = load_json("autofill1.json")
        cls.autofill1data = load_json("autofill1data.json")
        cls.autofill2 = load_json("autofill2.json")
        cls.autofill2data = load_json("autofill2data.json")
        cls.related1 = load_json("related1.json")
        cls.related1data = load_json("related1data.json")
        cls.texts = load_json("texts.json")
        cls.themes = load_json("themes.json")
        cls.timezones = load_json("timezones.json")
        load_provider_quotas()

        add_measurement_units()
        logger.info('*** Units added')
        add_quantities()
        logger.info('*** Quantities added')
        msg = cur_loader.update_currency()
        logger.info(f'*** {msg}')
        qfunc_info.update(load_json("qfunc_info.json"))
        logger.info('*** Calculators info updated')
        qty_categ_info.update(load_json("qty_categ_info.json"))
        logger.info('*** Qty/Unit categories info updated')
        unit_info.update(load_json("unit_info.json"))
        logger.info('*** Units info updated')
        qfunc_categ_info.update(load_json("qfunc_categ_info.json"))
        logger.info('*** Calculator categories info updated')
        cls.initialized = True
        logger.info("*** STAGE W.1: w1_load_json_once_per_worker() completed")


class QJson:
    json_cache: dict = {}
    json_cache_stat: dict = {}

    @classmethod
    def get(cls, key):
        if key in cls.json_cache_stat:
            cls.json_cache_stat[key]["hit"] += 1
        else:
            cls.json_cache[key] = load_json(f"{key}.json")
            cls.json_cache_stat[key] = {
                "hit": 0,
                'length': len(cls.json_cache[key]),
                'size': sys.getsizeof(cls.json_cache[key])
            }
        return cls.json_cache[key]

    @classmethod
    def getx(cls, key, **kwargs):
        lst = cls.get(key)
        for key, value in kwargs.items():
            lst[key] = value
        return lst
