# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

from datetime import date

from calculators.all.science.astronomy.cal_earth_rotation import moonphase


def test_moonphase_reference_dates():
    assert moonphase(date(2000, 1, 6))['Moon Phase'] == 'New'
    assert moonphase(date(2000, 1, 14))['Moon Phase'] == 'First Qtr'
    assert moonphase(date(2000, 1, 21))['Moon Phase'] == 'Full'
    assert moonphase(date(2000, 1, 28))['Moon Phase'] == 'Third Qtr'
