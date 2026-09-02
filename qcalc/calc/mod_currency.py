# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import os
import json
import urllib.request
from django.conf import settings
from qutil import makeid, check_setting, is_obsolete, timestamp_to_date, timestamp_to_dt, load_json
from qcore import add_currencies
import logging

logger = logging.getLogger(__name__)


class CurrencyLoader:
    PROVIDERS = {
        "fixer": {
            "latest_file": "latest_fixer.json",
            "default_file": "latest_default_fixer.json",
            "key_setting": "FIXER_API_KEY",
            "url_setting": "FIXER_API_URL",
            "timestamp_key": "timestamp",
            "base_key": "base",
            "rates_key": "rates",
            "interval_secs": "14400",  # 4hr
        },
        "exrate": {
            "latest_file": "latest_exrate.json",
            "default_file": "latest_default_exrate.json",
            "key_setting": "EXRATE_API_KEY",
            "url_setting": "EXRATE_API_URL",
            "timestamp_key": "time_last_update_unix",
            "base_key": "base_code",
            "rates_key": "conversion_rates",
            "interval_secs": "36000",  # 10hr
        },
    }
    currency_desc = load_json("currency.json")
    currency_list: dict = {}  # global currency list

    def __init__(self):
        self.j_list = None  # local currency list being processed

        fixer_api_key = check_setting(
            settings.FIXER_API_KEY,
            "FIXER_API_KEY",
            optional=True,
        )

        self.provider = "fixer" if fixer_api_key else "exrate"
        self.config = self.PROVIDERS[self.provider]
        self.interval_secs = int(self.config["interval_secs"])

    def base(self):
        return self.currency_list[self.config["base_key"]]

    def rates(self):
        return self.currency_list[self.config["rates_key"]]

    def timestamp(self):
        return self.currency_list[self.config["timestamp_key"]]

    def load_currency(self, update_now=False, backup=False):
        latest_json_path = os.path.join(settings.JSON_FILES_DIR, self.config["latest_file"])
        default_json_path = os.path.join(settings.JSON_FILES_DIR, self.config["default_file"])
        key_setting = self.config["key_setting"]
        url_setting = self.config["url_setting"]

        # load_json_path = latest_json_path if os.path.exists(latest_json_path) else default_json_path

        notfound, obsolete, success = True, True, False
        self.j_list = None

        def load_existing():
            notfound, obsolete, success = True, True, False
            try:
                if os.path.exists(latest_json_path):
                    self.j_list = load_json(latest_json_path)
                    notfound, obsolete, success = self._check_response(self.j_list)

                if not success and os.path.exists(default_json_path):
                    self.j_list = load_json(default_json_path)
                    notfound, obsolete, success = self._check_response(self.j_list)

            except Exception as e:
                logger.warning(f"!!! LC: Cannot load from any existing currency file: {e}")

            return notfound, obsolete, success

        if not update_now:
            notfound, obsolete, success = load_existing()

        if notfound or obsolete or update_now or not success:
            try:
                api_key = check_setting(
                    getattr(settings, key_setting),
                    key_setting,
                    optional=True,
                )

                if not api_key:
                    success = False
                    logger.warning(f"!!! LC: Currency API key missing from settings.{key_setting}")
                else:
                    api_url = check_setting(
                        getattr(settings, url_setting),
                        url_setting,
                    )

                    if self.provider == "fixer":
                        url = api_url + api_key
                    else:
                        url = api_url.replace("{api_key}", api_key)

                    with urllib.request.urlopen(url, timeout=15) as response:
                        jdata = json.loads(response.read())

                    self.j_list = jdata
                    notfound, obsolete, success = self._check_response(self.j_list)

                    if success:
                        if backup and os.path.exists(latest_json_path):
                            try:
                                j_list_old = load_json(latest_json_path)
                                _, _, success_old = self._check_response(j_list_old)
                                if success_old:
                                    backup_date = timestamp_to_date(j_list_old[self.config["timestamp_key"]])
                                    backup_path = latest_json_path.replace(".json",
                                                                           f"-backup-{backup_date}-{makeid()}.json")
                                    os.rename(latest_json_path, backup_path)
                            except Exception as e:
                                logger.warning(f"!!! LC: Cannot backup currency file: {e}")

                        with open(latest_json_path, "w") as outfile:
                            json.dump(jdata, outfile)

            except Exception as e:
                logger.error(f">>> LC: {e}")
                success = False

            if not success:
                notfound, obsolete, success = load_existing()

        return self.j_list, success

    def _check_response(self, j_list):
        if j_list == {}:
            return True, False, False

        if self.provider == "fixer":
            success = j_list.get("success", False)

            if not success:
                logger.error(">>> CRF: " + j_list.get("error", {}).get("info", "Unknown error"))
            obsolete = (
                success
                and is_obsolete(j_list[self.config["timestamp_key"]], self.interval_secs)
            )

        else:
            success = j_list.get("result") == "success"

            if not success:
                logger.error(">>> CRE: " + j_list.get("error", {}).get("info", "Unknown error"))
            obsolete = (
                success
                and is_obsolete(j_list[self.config["timestamp_key"]], self.interval_secs)
            )

        return False, obsolete, success

    def update_currency(self, update_now=False):
        cl, success = self.load_currency(update_now=update_now)
        if success:
            self.currency_list.update(cl)  # update the global list
            add_currencies(self.rates(), self.base(), self.currency_desc)
            update_msg = f"Currency {"updated" if update_now else "loaded"} as of: {self.cur_as_of()}"
        else:
            update_msg = f">>> UC: Could not {"update" if update_now else "load"} currency"
            logger.error(update_msg)
        return update_msg

    def cur_as_of(self):
        return timestamp_to_dt(self.timestamp())
