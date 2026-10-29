# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha
# Tests generated with AI assistance. Reviewed and validated by the author.

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

from calc.mod_whoosh import IsolatedRamStorage


def test_ram_storage_uses_isolated_named_temp_directories():
    first_storage = IsolatedRamStorage()
    second_storage = IsolatedRamStorage()

    first_temp = first_storage.temp_storage("MAIN.tmp")
    repeated_first_temp = first_storage.temp_storage("MAIN.tmp")
    second_temp = second_storage.temp_storage("MAIN.tmp")

    try:
        assert first_temp.folder == repeated_first_temp.folder
        assert first_temp.folder != second_temp.folder
        assert os.path.basename(first_temp.folder).startswith("qcalc-whoosh-")
        assert os.path.basename(second_temp.folder).startswith("qcalc-whoosh-")
    finally:
        first_temp.destroy()
        second_temp.destroy()
