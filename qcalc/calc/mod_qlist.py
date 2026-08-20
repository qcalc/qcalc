# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json
import os
import urllib.request
from qutil import makeid, check_setting, is_obsolete, timestamp_to_dt
from qcore import add_measurement_units, add_currencies, add_quantities
from .mod_redis import register_redis_action, publish_redis_action
import sys
from django.conf import settings
from qvars import qfunc_info, qty_info, unit_info
import logging

logger = logging.getLogger(__name__)

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


def load_json(json_file_name, path=None):
    if path is None:
        filepath = os.path.join(settings.JSON_FILES_DIR, json_file_name)
    else:
        filepath = os.path.join(path, json_file_name)

    try:
        json_data = open(filepath)
        j_list = json.load(json_data)
        json_data.close()
    except FileNotFoundError:
        logger.error(f'LDJ: File {filepath} does not exist')
        j_list = {}
    return j_list


def load_currency(update_now=False, backup=False):
    def check_curlist(j_list):
        notfound = False
        obsolete = False

        success = 'success' in j_list and j_list['success']
        if j_list == {}:
            notfound = True
        elif success:
            obsolete = is_obsolete(j_list["timestamp"], 36000)
        else:
            logger.error("LDC: " + j_list["error"]["info"])

        return notfound, obsolete, success

    latest_json_file = "latest.json"
    latest_filepath = os.path.join(settings.JSON_FILES_DIR, latest_json_file)
    default_json_file = "latest.json" if os.path.exists(latest_filepath) else "latest-default.json"
    notfound, obsolete, success = True, True, False
    j_list = None

    if not update_now:
        try:
            j_list = load_json(default_json_file)
            notfound, obsolete, success = check_curlist(j_list)
        except Exception as e:
            pass

    if notfound or obsolete or update_now or not success:
        try:
            fixer_api_key = check_setting(settings.FIXER_API_KEY, "FIXER_API_KEY", optional=True)
            if fixer_api_key == '':
                success = False
                logger.warning(f"LDC: Currency API key missing from settings.FIXER_API_KEY")
            else:
                fixer_api_url = check_setting(settings.FIXER_API_URL, "FIXER_API_URL")
                url = fixer_api_url + fixer_api_key
                with urllib.request.urlopen(url, timeout=15) as response:
                    jdata = json.loads(response.read())
                json_object = json.dumps(jdata)  # | simple JSON dumps
                if (not notfound) and success and backup:  # rename existing latest.json
                    os.rename(latest_filepath, os.path.join(
                        settings.JSON_FILES_DIR,
                        latest_json_file.replace('.json', f'-{j_list["date"]}-{makeid()}.json')))
                with open(latest_filepath, "w") as outfile:  # write current JSON dumps to latest.json
                    outfile.write(json_object)
                j_list = load_json(latest_json_file)
                notfound, obsolete, success = check_curlist(j_list)
        except Exception as e:
            logger.exception(f"Exception occurred: {e}")
            success = False

        if not success:
            try:
                j_list = load_json(default_json_file)
                logger.warning(f"LDC: Using Standard Currency rates from {default_json_file}")
            except Exception as e:
                raise logger.exception(f"Exception occurred: {e}")

    return j_list


def update_currency():
    cl = load_currency(update_now=True)
    StdList.currency_list.update(cl)  # update the global list
    add_currencies(StdList.currency_list, StdList.currency_desc)
    update_msg = "Currency updated as of: " + cur_as_of()
    publish_redis_action(
        channel="qcalc_channel",
        action="update_currency"
    )
    return update_msg

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
    currency_list: dict = {}
    currency_desc = {}
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
        cls.currency_list = load_currency()
        register_redis_action(update_currency)
        cls.currency_desc = load_json("currency.json")
        add_currencies(cls.currency_list, cls.currency_desc)

        logger.info('*** Currencies added')
        # qc_gpref.update(load_json("gpref.json", settings.ROOT_DIR))
        # lprint(qc_gpref)
        qfunc_info.update(load_json("qfunc_info.json"))
        logger.info('*** Func info updated')
        qty_info.update(load_json("qty_info.json"))
        logger.info('*** Qty info updated')
        unit_info.update(load_json("unit_info.json"))
        logger.info('*** Unit info updated')
        cls.initialized = True
        logger.info("--- STAGE W.1: w1_prepare_lists_once_per_worker() completed")


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


def cur_as_of():
    return timestamp_to_dt(StdList.currency_list['timestamp'])
