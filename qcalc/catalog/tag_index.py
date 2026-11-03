# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from collections import Counter

from calc import QCals


def normalize_tag_list(values):
    tags = []
    seen = set()
    for value in values:
        tag = value.strip().lower()
        if not tag or tag in seen:
            continue
        tags.append(tag)
        seen.add(tag)
    return tags


def _node_tags(node):
    return frozenset(tag.strip().lower() for tag in node.tag_list if tag.strip())


def _tag_items(counter):
    return [
        {'name': tag, 'count': count}
        for tag, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def _sort_nodes(nodes):
    return sorted(nodes, key=lambda nd: (nd.title.lower(), nd.name.lower()))


class TagIndex:
    """
    Tag lookup over the standard calculator catalog, built once per catalog build.
    Unrestricted leaves (visible to everyone) are pre-indexed; the few admin/demo/personal
    leaves are checked against the request's visibility at lookup time.
    """

    def __init__(self, root):
        self.root = root
        self.open_nodes = {}  # tag -> [nodes visible to everyone]
        self.restricted = []  # [(node, tags)] leaves with admin/demo/personal flags
        open_counter = Counter()
        for node in root.depth_first():
            if not (node.is_leaf and node.is_active):
                continue
            tags = _node_tags(node)
            if node.flags:
                self.restricted.append((node, tags))
                continue
            for tag in tags:
                open_counter[tag] += 1
                self.open_nodes.setdefault(tag, []).append(node)
        self.open_counter = open_counter
        self.open_tag_items = _tag_items(open_counter)

    def view(self, request):
        return TagView(self, [(node, tags) for node, tags in self.restricted if node.is_visible(request)])


class TagView:
    """Tag lookups as seen by one request."""

    def __init__(self, index, restricted):
        self._index = index
        self._restricted = restricted

    @property
    def tag_items(self):
        if not self._restricted:
            return self._index.open_tag_items
        counter = Counter(self._index.open_counter)
        for _node, tags in self._restricted:
            counter.update(tags)
        return _tag_items(counter)

    def nodes_by_tags(self, selected_tags, mode='or'):
        if not selected_tags:
            return []

        selected = set(selected_tags)
        open_nodes = self._index.open_nodes
        if mode == 'or':
            found = {}
            for tag in selected:
                for node in open_nodes.get(tag, ()):
                    found[node.id] = node
            result = list(found.values())
            result += [node for node, tags in self._restricted if tags & selected]
        else:  # mode == 'and'
            per_tag = [open_nodes.get(tag, ()) for tag in selected]
            if all(per_tag):
                per_tag.sort(key=len)
                common = {node.id for node in per_tag[0]}
                for nodes in per_tag[1:]:
                    common.intersection_update(node.id for node in nodes)
                result = [node for node in per_tag[0] if node.id in common]
            else:
                result = []
            result += [node for node, tags in self._restricted if selected <= tags]
        return _sort_nodes(result)


_index = None


def get_tag_view(request):
    global _index
    index = _index
    if index is None or index.root is not QCals.calc_root:  # catalog was rebuilt
        index = _index = TagIndex(QCals.calc_root)
    return index.view(request)
