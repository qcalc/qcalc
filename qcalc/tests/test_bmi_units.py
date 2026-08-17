# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import sys
from pathlib import Path
# import qsett
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calculators.all.health.cal_bmi import bmi
# from calc import mod_mfunc

def test_bmi_works_with_si_units():
    result = bmi('70 kg', '1.75 m')
    assert result['BMI'].val > 0


# def test_sqlite_for_user_code_uses_direct_path():
#     assert mod_mfunc._should_run_direct(
#         user_code=True,
#         exec_mode='0',
#         timeout=30,
#         system_name='Windows',
#         db_engine='django.db.backends.sqlite3',
#     ) is True
#
#
# def test_sqlite_for_non_user_code_uses_direct_path_on_linux():
#     assert mod_mfunc._should_run_direct(
#         user_code=False,
#         exec_mode='0',
#         timeout=30,
#         system_name='Linux',
#         db_engine='django.db.backends.sqlite3',
#     ) is True
