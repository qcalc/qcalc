# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import os
import django
__cat_initialized = False

# Use this module to quickly setup development settings
# and optionally initialize catalog
# for testing purpose
# Do not import this module in production code

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
os.environ.setdefault("RUN_MAIN", "true")
django.setup()

def init():
    global __cat_initialized
    if __cat_initialized:
        return

    from calc import create_standard_cataog_from_packages, StdList
    create_standard_cataog_from_packages()
    StdList.prepare_lists()
    __cat_initialized = True

if __name__ == '__main__':
    # from calc.mod_cutil import _test
    # from qutil.mod_basic import _test
    # from qutil.mod_data import _test
    # from calc.mod_whoosh import _test
    # from qcore.mod_anno import _test
    # from calc.mod_mfunc import _test
    # from calc.mod_head import _test
    # from qcore.mod_qcutil import _test
    from qcore.qc_qty import _test

    _test()
