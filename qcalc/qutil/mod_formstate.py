# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json


class FormState:
    """Mutable state of the calculator form flow of one request. Created once as request.fs by q1139_request_init().

    cmd and extra come from the 'extra' json posted by a command button (or sent in the url).
    success turns False when the form is invalid or a command fails, and stays False.
    recall and remember tell if the input is read from / saved to the user's memory.
    cid, input_id, variant, var_owner and var_title tell which form and which saved input (variant) is opened.
    """
    __slots__ = ('cmd', 'extra', 'extra_posted', 'success', 'recall', 'remember',
                 'cid', 'input_id', 'variant', 'var_owner', 'var_title')

    def __init__(self, cmd='', extra=None, extra_posted=False, recall=False, remember=False,
                 cid='', input_id=0, variant=0, var_owner='', var_title=''):
        self.cmd = cmd
        self.extra = extra or {}
        self.extra_posted = extra_posted
        self.success = True
        self.recall = recall
        self.remember = remember
        self.cid = cid
        self.input_id = input_id
        self.variant = variant
        self.var_owner = var_owner
        self.var_title = var_title

    @classmethod
    def from_request(cls, request):
        data = request.POST if request.method == 'POST' else request.GET
        if 'extra' not in data:
            return cls()
        try:
            extra = json.loads(data.get('extra') or '{}')
        except ValueError:
            extra = {}
        if not isinstance(extra, dict):
            extra = {}
        return cls(cmd=str(extra.get('cmd', '')).lower(), extra=extra, extra_posted=True)

    def default_cmd(self, cmd):
        """Sets the command given by the url. A command in the posted 'extra' always wins."""
        if not self.extra_posted:
            self.cmd = cmd

    def mark_failed(self):
        self.success = False
