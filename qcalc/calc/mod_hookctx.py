# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json

from qconst import TOK_UOM, TOK_PART, TOK_PART_UOM, TOK_INDEX_SEP
from qcore import convert_to_type, qt, qt2, qtx, qtc, qtc2
from qutil import user_name, is_loggedin

# | posted keys that are transport details, not calculator fields
_TRANSPORT_KEYS = frozenset({'csrfmiddlewaretoken', 'extra', 'qcalc_structural_cmd', 'cid', 'input_id'})

# | quantity types are posted as value and unit inputs, not as one text
_QTY_TYPES = (qt, qt2, qtx, qtc, qtc2)


class HookContext:
    """Read-only request level data passed as the first argument of the per-request hooks
    (__input, __schema, __modify, __command).

    It holds no reference to the request or session, so it is safe to give to frontend calculators.
    Hook specific data (arg_name, arg_value, action, func_kwargs) is still passed as separate arguments.
    """
    __slots__ = ('func_id', 'cid', 'user', 'is_loggedin', 'is_post', 'recall', 'cmd',
                 '_var_url_kwargs', '_posted', '_resolved', '_extra')

    def __init__(self, func_id='', cid='', var_url_kwargs=None, posted=None, resolved=None,
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
        self._resolved = dict(resolved or {})
        self._extra = json.loads(json.dumps(extra or {}))

    @classmethod
    def from_request(cls, request, func_id, cid, var_url_kwargs):
        is_post = request.method == 'POST'
        data = request.POST if is_post else request.GET
        cmd, extra = cls._command_of(request, data)
        posted = {}
        if is_post:
            posted = {name: data.getlist(name) for name in data if name not in _TRANSPORT_KEYS}
        # | the fields a 'reload' trigger resets take their default values, not the posted ones
        reset = extra.get('reset') or []
        # | q11421 drops the same fields from POST, so the hooks must not see them either
        posted = {name: values for name, values in posted.items() if name not in reset}
        return cls(func_id=func_id, cid=cid, var_url_kwargs=var_url_kwargs, posted=posted,
                   cmd=cmd, extra=extra, is_post=is_post,
                   recall=getattr(request, 'recall', False),
                   user=user_name(request), is_loggedin=is_loggedin(request))

    def with_resolved(self, resolved):
        """A copy of this context holding the given resolved values. The context itself is never changed."""
        return HookContext(func_id=self.func_id, cid=self.cid, var_url_kwargs=self._var_url_kwargs,
                           posted=self._posted, resolved=resolved, cmd=self.cmd, extra=self._extra,
                           is_post=self.is_post, recall=self.recall, user=self.user, is_loggedin=self.is_loggedin)

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
        Empty on a posted form, except when a saved input file is opened. Values are not always text (e.g. DataFrame)."""
        return dict(self._var_url_kwargs)

    def var_url(self, name, default=None):
        """One value of var_url_kwargs."""
        return self._var_url_kwargs.get(name, default)

    @property
    def resolved_kwargs(self):
        """The value each field starts with in this request: function defaults, __info() and qfunc_info.json values,
        __input() values, remembered input, then the saved variant or url values, merged in that order (a url value
        of '-' keeps the lower layers, '--' empties the field). Posted values are not part of it.
        Keyed by the argument names of the calculator function. Values keep their own type, they are not always text.
        For __input() the values returned by __input() itself are not included yet.
        A post has no variant or url layer, except when a saved input file is opened."""
        return dict(self._resolved)

    def resolved(self, name, default=None):
        """One value of resolved_kwargs. The default is used only when the calculator has no such field."""
        return self._resolved.get(name, default)

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

    def posted_as(self, name, target_type, default=None):
        """Posted value of a field converted to target_type, a type of the calculator function (float, int, str,
        bool, qt ...). The default is returned when the field was not posted or its value cannot be converted,
        e.g. an empty or invalid number. A quantity (qt, qt2, qtx) is joined from its value and unit inputs."""
        text = self._posted_qty(name) if target_type in _QTY_TYPES else self.posted(name)
        if text is None:
            return default
        try:
            return convert_to_type(text, target_type, strict=True)
        except Exception:  # | converters raise different errors, e.g. a quantity with no unit is a SyntaxError
            return default

    def value(self, name, target_type, default=None):
        """The value a field has in this request, converted to target_type (see posted_as): the posted value when
        it converts, else the resolved value, else the default. A resolved value that is not text (a number, a
        quantity, a table) already has a type and is returned as it is."""
        missing = object()
        posted = self.posted_as(name, target_type, missing)
        if posted is not missing:
            return posted
        resolved = self._resolved.get(name)
        if resolved is None:
            return default
        if not isinstance(resolved, str):
            return resolved
        try:
            return convert_to_type(resolved, target_type, strict=True)
        except Exception:  # | e.g. an empty value, set by a url '--', is not a number
            return default

    def _posted_qty(self, name):
        # | the inputs of a quantity: name + name_uom, or name + name_part_uom for several parts, then
        # | name__2_part + name__2_part_uom and so on. An empty part makes the whole quantity unknown.
        value = self.posted(name)
        unit = self.posted(name + TOK_UOM)
        if unit is None:
            unit = self.posted(name + TOK_PART_UOM)
        parts, index = [], 1
        while unit is not None:
            if not value or not unit:
                return None
            parts.append(f'{value} {unit}')
            index += 1
            prefix = f'{name}{TOK_INDEX_SEP}{index}'
            value, unit = self.posted(prefix + TOK_PART), self.posted(prefix + TOK_PART_UOM)
        return ', '.join(parts) if parts else value  # | no unit input: the quantity was posted as one text

    @property
    def extra(self):
        """Data sent by a callback button: {cmd, args, kwargs}. kwargs maps field name to action."""
        return json.loads(json.dumps(self._extra))
