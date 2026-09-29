# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import unittest
import sys
from pathlib import Path
from datetime import time as dt_time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from qutil.mod_data import time2float


class TestModData(unittest.TestCase):
    def test_time2float_seconds_milliseconds_microseconds(self):
        t = dt_time(1, 30, 15, 500000)
        self.assertEqual(time2float(t, 's'), 5415.5)
        self.assertEqual(time2float(t, 'ms'), 5415500)
        self.assertEqual(time2float(t, 'mics'), 5415500000)


if __name__ == '__main__':
    unittest.main()
