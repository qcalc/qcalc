# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json

from qutil import user_name, is_loggedin

# | posted keys that are transport details, not calculator fields
_TRANSPORT_KEYS = frozenset({'csrfmiddlewaretoken', 'extra', 'qcalc_structural_cmd', 'cid', 'input_id'})


class HookContext:
    """Read-only request level data passed as the first argument of the per-request hooks
    (__input, __schema, __modify, __command).

    It holds no reference to the request or session, so it is safe to give to frontend calculators.
    Hook specific data (arg_name, arg_value, action, func_kwargs) is still passed as separate arguments.
    """
    __slots__ = ('func_id', 'cid', 'user', 'is_loggedin', 'is_post', 'recall', 'cmd',
                 '_var_url_kwargs', '_posted', '_remembered', '_extra')

    def __init__(self, func_id='', cid='', var_url_kwargs=None, posted=None, remembered=None,
                 cmd='', extra=None, is_post=False, recall=False, user='', is_loggedin=False):
        self.func_id = func_id
        self.cid = cid
        self.user = user
        self.is_loggedin = bool(is_loggedin)
        self.is_post = bool(is_post)
        self.recall = bool(recall)
        self.cmd = str(cmd or '').lower()
        self._var_url_kwargs = dict(var_url_kwargs or {})
        self._posted = {name: tuple(values) for name, values in (posted or {}).items()}
        self._remembered = dict(remembered or {})
        self._extra = json.loads(json.dumps(extra or {}))

    @classmethod
    def from_request(cls, request, func_id, cid, var_url_kwargs, remembered=None):
        is_post = request.method == 'POST'
        data = request.POST if is_post else request.GET
        cmd, extra = cls._command_of(request, data)
        posted = {}
        if is_post:
            posted = {name: data.getlist(name) for name in data if name not in _TRANSPORT_KEYS}
        # | the fields a 'reload' trigger resets take their default values, not the remembered ones
        reset = extra.get('reset') or []
        remembered = {k: v for k, v in (remembered or {}).items() if k not in reset}
        return cls(func_id=func_id, cid=cid, var_url_kwargs=var_url_kwargs, posted=posted,
                   remembered=remembered, cmd=cmd, extra=extra, is_post=is_post,
                   recall=getattr(request, 'recall', False),
                   user=user_name(request), is_loggedin=is_loggedin(request))

    @staticmethod
    def _command_of(request, data):
        # | same rule as q11421_get_extra_form_data_posted(), which runs later and blanks POST['extra']:
        # | 'extra' in the request decides the command, otherwise the command already set on the request is used
        if 'extra' not in data:
            return getattr(request, 'cmd', ''), {}
        try:
            extra = json.loads(data.get('extra') or '{}')
        except ValueError:
            extra = {}
        if not isinstance(extra, dict) or not extra:
            return '', {}
        return str(extra.get('cmd', '')), extra

    # | field values come from three sources. For each source, name(field, default) returns one value
    # | and name_kwargs returns a new dict of all fields (a copy, so the context cannot be changed)

    @property
    def var_url_kwargs(self):
        """Values of a saved variant, example or shared input, overlaid by the values given in the url.
        Empty on a posted form. Values are not always text (e.g. DataFrame)."""
        return dict(self._var_url_kwargs)

    def var_url(self, name, default=None):
        """One value of var_url_kwargs."""
        return self._var_url_kwargs.get(name, default)

    @property
    def remembered_kwargs(self):
        """Input of the user's previous run of this calculator. Empty unless memory is being recalled."""
        return dict(self._remembered)

    def remembered(self, name, default=None):
        """One value of remembered_kwargs, as it was stored (not always text)."""
        return self._remembered.get(name, default)

    @property
    def posted_kwargs(self):
        """Posted values of all fields as received (text, never converted). The last one for a repeated field."""
        return {name: values[-1] for name, values in self._posted.items() if values}

    def posted(self, name, default=None):
        """Posted value of a field as received (text, never converted). The last one for a repeated field."""
        values = self._posted.get(name)
        return values[-1] if values else default

    def posted_list(self, name):
        """All posted values of a field as received (text), e.g. a multiple select."""
        return list(self._posted.get(name, ()))

    @property
    def extra(self):
        """Data sent by a callback button: {cmd, args, kwargs}. kwargs maps field name to action."""
        return json.loads(json.dumps(self._extra))
