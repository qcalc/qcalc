# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import environ
import json
import os

qfunc_dict_template = {  # dict of function name and template version
    'default': 'v4.27',
}
qfunc_info = {}
qty_info = {}
unit_info = {}


# also change in gpref.json  # pref-00


def load_root_json(json_file_name):
    path = (environ.Path(__file__) - 1)
    filepath = os.path.join(path, json_file_name)

    try:
        json_data = open(filepath)
        j_list = json.load(json_data)
        json_data.close()
    except FileNotFoundError:
        j_list = {}
    return j_list


qc_gpref = {  # pref-01
    # user settings
    'theme': 'default',
    'ignore_decimal_format': False,
    'decimal': 8,  # 2-16
    'qty_decimal': 5,  # 2-16
    'currency_decimal': 2,  # 2-16
    'thousands_separator': True,
    'exponent_threshold_min': 1.0e-6,
    'exponent_threshold_max': 1.0e9,
    # 'number_format': '{:,.8f}',  # precision 2-16
    'defa_currency': 'USD',
    'memory': 10,  # 10
    'fuzzy_search': False,
    'semantic_search': False,
    'chart_color_scheme': 'tab20',
    'chart_width': 620,
    'chart_height': 620,
    # 'page_font_size': 82,
    'chart_legend': 'lower center',
    'strict_assign': False,
    'execution_timeout': 60,  # 60
    # global settings
    'range_limit': 1000,  # 10-2000
    'demo_mode': True,  # allows arbitrary function to addfunc
    'schema_cache': True,  # True
    'uom_v2': True,
}
qc_gpref.update(load_root_json("gpref.json"))
shared_session = {}
last_dump = {}
super_user = None
stop_redis_listener = False
