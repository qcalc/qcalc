# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

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
        logger.info(f'>>> LDJ: File {filepath} does not exist')
        j_list = {}
    return j_list
