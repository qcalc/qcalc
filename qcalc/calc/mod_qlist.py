# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import sys
from qcore import add_measurement_units, add_quantities
from qvars import qfunc_info, qty_info, unit_info
from qutil import load_json
from .mod_currency import CurrencyLoader
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

gender_choice = {
    'type': 'choice',
    'initial': 'F',
    'choices': {'M': 'Male', 'F': 'Female'}
}

show_choice = {
    'type': 'radio',
    'initial': 'both',
    'choices': {'table': 'Table', 'chart': 'Chart', 'both': 'Both'}
}


def list2options(lst, **kwargs):
    for key, value in kwargs.items():
        lst[key] = value
    return lst


class StdList:
    initialized = False
    autofill1_list = {}
    autofill1data_list = {}
    autofill2_list = {}
    autofill2data_list = {}
    related1_list = {}
    related1data_list = {}
    text_list = {}
    theme_list = {}
    timezone_list = {}

    @classmethod
    def w1_prepare_lists_once_per_worker(cls):
        cls.autofill1_list = load_json("autofill1.json")
        cls.autofill1data_list = load_json("autofill1data.json")
        cls.autofill2_list = load_json("autofill2.json")
        cls.autofill2data_list = load_json("autofill2data.json")
        cls.related1_list = load_json("related1.json")
        cls.related1data_list = load_json("related1data.json")
        cls.text_list = load_json("texts.json")
        cls.theme_list = load_json("themes.json")
        cls.timezone_list = load_json("timezones.json")

        add_measurement_units()
        logger.info('*** Units added')
        add_quantities()
        logger.info('*** Qtys added')
        msg = cur_loader.update_currency()
        logger.info(f'*** {msg}')
        qfunc_info.update(load_json("qfunc_info.json"))
        logger.info('*** Func info updated')
        qty_info.update(load_json("qty_info.json"))
        logger.info('*** Qty info updated')
        unit_info.update(load_json("unit_info.json"))
        logger.info('*** Unit info updated')
        cls.initialized = True
        logger.info("*** STAGE W.1: w1_prepare_lists_once_per_worker() completed")


class QList:
    dict_of_list: dict = {}
    dict_of_stat: dict = {}

    @classmethod
    def get(cls, key):
        if key in cls.dict_of_stat:
            cls.dict_of_stat[key]["hit"] += 1
        else:
            cls.dict_of_list[key] = load_json(f"{key}.json")
            cls.dict_of_stat[key] = {
                "hit": 0,
                'length': len(cls.dict_of_list[key]),
                'size': sys.getsizeof(cls.dict_of_list[key])
            }
        return cls.dict_of_list[key]

    @classmethod
    def getx(cls, key, **kwargs):
        lst = cls.get(key)
        for key, value in kwargs.items():
            lst[key] = value
        return lst
