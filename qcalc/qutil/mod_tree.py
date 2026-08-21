# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import json

from qutil import stop_words, match_any, css2strs, user_name, path_title
from qvars import qc_gpref as gs
from typing import Optional, List, Tuple
from qutil.mod_settings import is_debug
import logging

logger = logging.getLogger(__name__)


class TreeNode:
    admin_name: str = "admin"
    demo_name: str = "demo"
    personal_name: str = "personal"

    def __init__(self, nid, name, title='', desc='', tags='', is_leaf=False, node_type=None, is_active=True,
                 data=None, sub_type=''):
        self.id = nid  # | slug, unique, e.g. calculators-others-gold, ft, ext-others-gold
        self.name = name  # if name != '' else id  # | name or slug, may or may not be unique, e.g. gold, feet, gold
        self.title = title  # | proper title with multiple words e.g. Cals Gold, Feet, Ext Gold
        self.desc = desc  # | description
        self.tags = tags
        self.is_leaf = is_leaf
        self.node_type = node_type  # | c=calc, u=unit, q=qty
        self.sub_type = sub_type  # | e=editable user calc
        self.is_active = is_active
        self.data = {} if data is None else data

        self.flags = ''  # | A=admin, D=demo, P=personal, AD/DA=both, ''=All Users
        self.uname = ''  # | if 'P' in flags this will store session hash or user id if user is logged in
        self.depth = 0
        self.leafcount = 0  # | Property to store the total descendant leafs
        self.admincount = 0
        self.democount = 0
        self.children = []
        self.parent = None

        self.update_flags()
        self.tag_list = css2strs(self.tags) if self.tags else []

        # if not hasattr(self.__class__, "_nodes_index"):
        #     self.__class__._nodes_index = {}

        # | Indexing during add_child ensures that only fully initialized and linked nodes are indexed.
        # | hence removed indexing during initialization
        # | self._index_node()

        # Initialize the instance-level nodes index
        # self._nodes_index = nodes_index if nodes_index is not None else {}
        self._nodes_index = {}
        # self._index_node()  # Index the node upon initialization

    @classmethod
    def setup(cls, admin_name='admin', demo_name='demo', personal_name='personal'):
        cls.admin_name = admin_name
        cls.demo_name = demo_name
        cls.personal_name = personal_name

    def __iter__(self):
        return iter(self.children)

    def sort_by_title(self):
        for node in self.depth_first():
            node.children.sort(key=lambda nd: nd.title if nd.is_leaf else f"-{nd.title}")

    def sort_by_name(self):
        for node in self.depth_first():
            node.children.sort(key=lambda nd: nd.name if nd.is_leaf else f"-{nd.name}")

    def sort_by(self, key='name'):
        if key == 'name':
            self.sort_by_name()
        elif key == 'title':
            self.sort_by_title()

    def update_flags(self):
        cur_name = self.name.lower()
        self.flags = ''
        if cur_name == self.__class__.admin_name:
            self.flags += 'A'
        elif self.parent and ('A' in self.parent.flags):
            self.flags += 'A'

        if cur_name == self.__class__.demo_name:
            self.flags += 'D'
        elif self.parent and ('D' in self.parent.flags):
            self.flags += 'D'

        if cur_name == self.__class__.personal_name:
            self.flags += 'P'
        elif self.parent and ('P' in self.parent.flags):
            self.flags += 'P'

    def is_visible(self, request) -> bool:
        # | Check if node/function is visible to the user
        # | same logic in q1129_is_func_authorized
        # | Hide empty branch nodes
        if not self.is_leaf and not self.children:
            return False

        flags = self.flags
        # print('f', flags)
        if is_debug():  # to enable [mass] testing
            return True
        if 'D' in flags:  # Demo
            # return gs['demo_mode']
            return gs['demo_mode'] and request.user.is_active
        if 'P' in flags:  # Personal
            # return (self.uname == user_name(request)) or is_debug() or request.user.is_staff
            return (self.uname == user_name(request)) or request.user.is_staff
        if 'A' in flags:  # Admin
            # return is_debug() or request.user.is_staff
            return request.user.is_staff
        # '' All Users
        return True

    def depth_first(self):
        yield self
        for c in self:
            yield from c.depth_first()

    def get_tree(self):
        return list(self.depth_first())

    def get_ancestor_ids(self) -> list:
        """
        Generate a list of ancestors up to the root for the current node.
        """
        parents = []
        current_node = self
        while current_node.parent is not None:
            parents.append(current_node.parent.id)
            current_node = current_node.parent
        return parents[::-1]  # Reverse the list to start from the root

    def get_ancestor_ids_titles(self) -> List[Tuple[str, str]]:
        """
        Generate a list of ancestors up to the root for the current node.
        """
        parents = []
        current_node = self
        while current_node.parent is not None:
            parents.append((current_node.parent.id, current_node.parent.title))
            current_node = current_node.parent
        return parents[::-1]  # Reverse the list to start from the root

    def count_descendant_leafs(self):
        count = 0
        admincount = 0
        democount = 0
        for child in self.children:
            if child.is_leaf:
                count += 1
                admincount += 1 if 'A' in child.flags else 0
                democount += 1 if 'D' in child.flags else 0
            else:
                c, a, d = child.count_descendant_leafs()
                count += c
                admincount += a
                democount += d
        self.leafcount = count
        self.admincount = admincount
        self.democount = democount
        return count, admincount, democount

    def _index_node(self, allowdups=False):
        if not allowdups:
            if self.id not in self._nodes_index:
                self._nodes_index[self.id] = self
            else:
                raise Exception(f'Node id "{self.id}" already exists')
        else:
            if self.id not in self._nodes_index:
                self._nodes_index[self.id] = self

    def get_node_by_id(self, nid) -> Optional['TreeNode']:
        return self._nodes_index.get(nid, None)

    def add_child(self, child, allowdups=False):
        self.children.append(child)
        child.depth = self.depth + 1
        child.parent = self
        child.update_flags()

        # | Ensure the child shares the same index
        child._nodes_index = self._nodes_index
        # | Indexing during add_child ensures that only fully initialized and linked nodes are indexed.
        # noinspection PyProtectedMember
        child._index_node(allowdups)  # | Index the child node upon adding

    def add_tree(self, subtree, allowdups=False):
        # Step 1: Set the parent of the subtree to self
        subtree.parent = self

        # Step 2: Update the depth of the subtree and all its descendants
        def update_depth(node, new_depth):
            node.depth = new_depth
            for child in node.children:
                update_depth(child, new_depth + 1)

        update_depth(subtree, self.depth + 1)

        # Step 3: Add the subtree to self's children
        self.children.append(subtree)

        # Step 4: Ensure the subtree shares the same _nodes_index for node lookup
        subtree._nodes_index = self._nodes_index

        # Step 5: Index the subtree and all its descendants in the current tree's _nodes_index
        # noinspection PyProtectedMember
        subtree._index_node(allowdups)  # noqa: W0212
        for child in subtree.children:
            child._nodes_index = self._nodes_index
            # noinspection PyProtectedMember
            child._index_node(allowdups)

            # Step 6: Update flags for the subtree and all its descendants
        subtree.update_flags()
        for node in subtree.depth_first():
            node.update_flags()

    def add_node_if_not_found(self, parent_id, nid, name):
        # | Function to add a node if the id is not found
        parent_node = self.get_node_by_id(parent_id)
        if parent_node is None:
            return None, 0

        existing_node = parent_node.get_node_by_id(nid)
        if existing_node:
            return existing_node, 1  # Node already exists under specified parent

        new_node = TreeNode(nid, name)
        parent_node.add_child(new_node)
        return new_node, 0

    def tree_to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "desc": self.desc,
            "tags": self.tags,
            "is_leaf": self.is_leaf,
            "node_type": self.node_type,
            "sub_type": self.sub_type,
            "is_active": self.is_active,
            "data": self.data,

            "flags": self.flags,
            "uname": self.uname,
            "depth": self.depth,
            "leafcount": self.leafcount,
            "admincount": self.admincount,
            "democount": self.democount,
            "parent_id": self.parent.id if self.parent else '',
            "children": [child.tree_to_dict() for child in self.children]
        }

    def save_tree_to_json(self, filename):
        # | Function to save tree to a JSON file
        with open(filename, "w") as file:
            json.dump(self.tree_to_dict(), file, indent=2)

    def get_its_children(self) -> list:
        # | Function to get children of this node
        return self.children

    def get_children_by_id(self, nid) -> list:
        # | Function to get children of a node by id
        cnode = self.get_node_by_id(nid)
        nodes = cnode.children
        return nodes

    def search_nodes_by_tag(self, tag) -> list:
        # | Function to search for a node by tag
        results = []
        if tag in self.tag_list:
            results.append(self)

        for child in self.children:
            results += child.search_nodes_by_tag(tag)

        return results

    def search_related_nodes(self) -> list:
        # | Function to search all nodes having like tags
        results = []
        for tag in self.tag_list:
            results += self.search_nodes_by_tag(tag)

        return results

    def update_all_descendant_leafs_count(self):
        for node in self.depth_first():
            node.count_descendant_leafs()

    def filter(self, terms, request, is_leaf=None, is_active=None, fuzzy=False, semantic=False) -> list:
        nodes = []
        for child in self.children:
            if is_active is not None:
                if child.is_active != is_active:
                    continue

            check_this = True
            if is_leaf is not None:
                if child.is_leaf != is_leaf:
                    check_this = check_this and False
            check_this = check_this and child.is_visible(request)

            if check_this:
                text_to_search = child.name + ' ' + child.title + ' ' + child.tags + ' ' + child.desc
                text_to_search = text_to_search.lower()
                if match_any(terms, text_to_search, fuzzy=fuzzy, semantic=semantic):
                    nodes.append(child)
            if not child.is_leaf:
                nodes += child.filter(terms, request, is_leaf, is_active, fuzzy=fuzzy, semantic=semantic)
        return nodes

    def search_nodes(self, sterms, request, show_all=False,
                     fuzzy=False, semantic=False, exclude_stop_words=True) -> list:  # v2
        nodes = []
        # print("fuzzy", fuzzy)
        if len(sterms) > 1:
            terms = sterms.lower().split()
            terms = [term for term in terms if len(term) > 1]
            if exclude_stop_words:
                terms = [term for term in terms if term not in stop_words]
            terms = [term for term in terms if term not in
                     ['calculate', 'calculation', 'calculator']]
            # print('actually searching:', terms)
            if len(terms) > 0:
                # limit to first 100 serach results
                if not show_all:
                    nodes = self.filter(terms, request, True, fuzzy=fuzzy, semantic=semantic)[0:100]
                else:
                    nodes = self.filter(terms, request, fuzzy=fuzzy, semantic=semantic)[0:100]
        return nodes

    def get_depth(self):
        return self.depth

    def delete_tree(self):
        # Recursively delete all children
        for child in self.children[:]:  # Copy the list to avoid modification during iteration
            child.delete_tree()
        self.children.clear()  # Clear the list of children

        # If this node has a parent, remove this node from its parent's children list
        if self.parent:
            self.parent.children.remove(self)
            self.parent = None

        # Remove this node from the instance-level index
        if self.id in self._nodes_index:
            del self._nodes_index[self.id]

    def add_category_node(self, par_id, ctg_node_id, ctg_node_name, ctg_node_title, uname=None):
        ctg_node, flag = self.add_node_if_not_found(par_id, ctg_node_id, ctg_node_name)
        if not ctg_node:
            logger.error(f'>>> ACN: Error processing {ctg_node_id}')
        if flag == 0:  # newly added node
            # | ctg_node._index_node()
            ctg_node.title = path_title(ctg_node_title)
            ctg_node.data["path"] = ctg_node.title
            ctg_node.is_leaf = False
            ctg_node.node_type = 'c'
            ctg_node.uname = uname

        return ctg_node


def load_tree_from_json(filename):
    # | Function to load tree from a JSON file
    with open(filename, "r") as file:
        tree_dict = json.load(file)
    node = dict_to_tree(tree_dict)
    # | node.update_all_descendant_leafs_count()
    return node


def dict_to_tree(node_dict, id_prefix=''):
    if not node_dict:
        return None
    nid = f'{id_prefix}{node_dict["id"]}'
    name = node_dict["name"]
    node = TreeNode(nid, name)  # root
    # noinspection PyProtectedMember
    node._index_node()
    node.title = node_dict.get("title", '')
    node.desc = node_dict.get("desc", '')
    node.tags = node_dict.get("tags", '')
    node.is_leaf = node_dict.get("is_leaf", False)
    node.node_type = node_dict.get("node_type", '')
    node.sub_type = node_dict.get("sub_type", '')
    node.is_active = node_dict.get("is_active", True)
    node.data = node_dict.get("data", {})

    node.flags = node_dict.get("flags", '')
    node.uname = node_dict.get("uname", '')
    node.depth = node_dict.get("depth", 0)
    node.leafcount = 0  # | dynamic, not node_dict.get("numchild", 0)

    for child_dict in node_dict.get("children", []):
        child_node = dict_to_tree(child_dict)
        node.add_child(child_node)
    node.update_all_descendant_leafs_count()
    return node


def create_category_node(ctg_node_id, ctg_node_name, ctg_node_title, uname=None):
    ctg_node = TreeNode(ctg_node_id, ctg_node_name)
    # noinspection PyProtectedMember
    ctg_node._index_node()
    ctg_node.title = path_title(ctg_node_title)
    ctg_node.data["path"] = ctg_node.title
    ctg_node.is_leaf = False
    ctg_node.node_type = 'c'
    ctg_node.uname = uname
    return ctg_node


if __name__ == '__main__':
    # Function to build the tree
    def build_tree():
        TreeNode.setup()
        root = TreeNode("Root", "root")

        child1 = TreeNode("Child 1", "Child 1")
        child2 = TreeNode("Child 2", "Child 2")
        child3 = TreeNode("Child 3", "Child 3")

        root.add_child(child1)
        root.add_child(child2)
        root.add_child(child3)

        sub_child1_1 = TreeNode("Subchild 1.1", "Subchild 1.1", is_leaf=True)
        sub_child1_2 = TreeNode("Subchild 1.2", "Subchild 1.2", is_leaf=True)

        child1.add_child(sub_child1_1)
        child1.add_child(sub_child1_2)
        root.update_all_descendant_leafs_count()

        return root


    # Build the tree
    tree = build_tree()

    # Save the tree to a JSON file
    tree.save_tree_to_json("test_tree.json")

    print(f"Total descendant_leafs of '{tree.id}': {tree.leafcount}")

    tree.delete_tree()

    # Load the tree from the JSON file
    loaded_tree = load_tree_from_json("test_tree.json")

    # Search for a node by name in the loaded tree and print total descendants
    target_node_name = "Root"
    found_node = loaded_tree.get_node_by_id(target_node_name)

    if found_node:
        print(f"Node '{target_node_name}' found!")
        print(f"Total descendant_leafs of '{found_node.id}': {found_node.leafcount}")
    else:
        print(f"Node '{target_node_name}' not found.")

    # Update and save the tree after modification
    loaded_tree.save_tree_to_json("test_updated_tree.json")
