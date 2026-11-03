# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

"""
Rendered catalog fragments (category tables and trees) shared across requests.

A fragment depends only on the catalog node, the visibility class of the viewer and the catalog
version, so it is rendered once per (node, class) and reused. The one per-user part, the favorite
star of each calculator, is rendered in its empty state and swapped in afterwards.
"""

import threading
from functools import lru_cache

from django.template.loader import render_to_string

from calc import QCals
from qutil.mod_settings import is_debug
from qvars import qc_gpref as gs

_MAX_FRAGMENTS = 2000
_lock = threading.Lock()
_fragments = {}
_state = {'version': None, 'has_personal': {}}


def visibility_key(request):
    """
    Everything TreeNode.is_visible() and the uleafcount filter read from the request, for trees without
    personal nodes: two requests with the same key see the same nodes and the same leaf counts.
    """
    user = request.user
    return bool(is_debug()), bool(gs['demo_mode'] and user.is_active), bool(user.is_staff)


def _sync_version():
    version = QCals.catalog_version
    if _state['version'] != version:
        _fragments.clear()
        _state['has_personal'] = {}
        _state['version'] = version
    return version


def _is_shareable(root):
    # personal nodes are visible per owner, so such trees cannot be shared by visibility class
    cache = _state['has_personal']
    found = cache.get(id(root))
    if found is None:
        found = cache[id(root)] = not any('P' in node.flags for node in root.depth_first())
    return found


def cached_fragment(request, root, key, template, build_context):
    """
    Return the rendered fragment, building it with build_context() only on a miss.
    root is the catalog tree the fragment is drawn from; key identifies the fragment within it.
    """
    with _lock:
        version = _sync_version()
        shareable = _is_shareable(root)
        full_key = (key, visibility_key(request))
        html = _fragments.get(full_key) if shareable else None
    if html is not None:
        return html

    html = render_to_string(template, build_context(), request=request)
    if shareable:
        with _lock:
            if _state['version'] == version:  # skip if the catalog changed while rendering
                if len(_fragments) >= _MAX_FRAGMENTS:
                    _fragments.clear()
                _fragments[full_key] = html
    return html


@lru_cache(maxsize=4096)
def _fav_icon(func_id, fav_state):
    return render_to_string('favorite_icon.html', {'func_id': func_id, 'input_id': 0, 'fav_state': fav_state})


def apply_favorites(html, favorite_dict):
    """Turn the empty favorite stars of the user's favorite calculators into filled ones."""
    for func_id, input_ids in favorite_dict.items():
        if input_ids and 0 in input_ids:
            empty = _fav_icon(func_id, False)
            if empty in html:
                html = html.replace(empty, _fav_icon(func_id, True))
    return html
