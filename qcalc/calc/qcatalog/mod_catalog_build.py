# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import importlib.util
import inspect
import logging
import os
import re
import traceback
from importlib import import_module
from pathlib import Path

import qconst
from django.conf import settings
from qcore import registered
from qutil import TreeNode, joinx, names2fid
from qvars import qfunc_categ_info
from ..mod_sandbox import CalcSandbox

logger = logging.getLogger(__name__)

# | ids of the folders a user names in a calculator's __info() 'folder'; the prefix keeps them apart from
# | calculator ids and the created / shared / favorites branches
FOLDER_ID_PREFIX = 'd:'
FOLDER_DEPTH_MAX = 4
FOLDER_NAME_MAX = 30


class CatalogBuilder:
    """Scans calculator sources into function dictionaries and grows calculator catalog trees."""

    @staticmethod
    def build_func_dict(func_addr_list, catalog_name, package_name, func_dict, c_dict=None):
        for fname, faddr in func_addr_list:
            if fname.endswith('__info'):
                cal_name = fname.split('__info')[0]
                cal_id = names2fid(catalog_name, cal_name)
                func_dict[f'{cal_id}__info'] = faddr
                if c_dict is not None:
                    c_dict[cal_id] = package_name
            elif '__' in fname:
                splits = fname.split('__')
                cal_id = names2fid(catalog_name, splits[0])
                func_dict[f'{cal_id}__{splits[1]}'] = faddr
            else:
                func_dict[names2fid(catalog_name, fname)] = faddr

    @classmethod
    def scan_package(cls, package_name, catalog_name, func_dict, c_dict, ctg_dict):
        host_package_name = package_name

        def searchpath(package_name):
            ctg_dict[package_name] = package_name.replace(host_package_name, catalog_name)

            spec = importlib.util.find_spec(package_name)
            if spec is None:
                return
            with os.scandir(Path(spec.origin).parent) as entries:
                for entry in entries:
                    if entry.name.startswith('__'):
                        continue
                    current_pkg = '.'.join((package_name, entry.name.partition('.')[0]))
                    if entry.is_dir():
                        searchpath(current_pkg)
                    elif entry.is_file() and entry.name.endswith('.py'):
                        module = import_module(current_pkg)
                        func_address_list = inspect.getmembers(module, inspect.isfunction)
                        func_address_list += registered(vars(module), vars(module)).items()
                        cls.build_func_dict(func_address_list, catalog_name, package_name, func_dict, c_dict)

        searchpath(package_name)

    @classmethod
    def scan_cals(cls, sources, scope, label, func_dict, c_dict, ctg_dict):
        """Run user calculator code from MyStuff records and collect its functions.

        sources yields (package_name, catalog_name, record); record may be None when the code is missing.
        """
        for package_name, catalog_name, record in sources:
            ctg_dict.setdefault(package_name, catalog_name)
            if record is None:
                continue
            try:
                local_dict = CalcSandbox.exec_with_context(
                    record.item,
                    scope=scope,
                    username=record.user.username,
                    item_id=record.item_id,
                )
            except Exception as e:
                logger.error(
                    "%s calculator scan skipped | user=%s item_id=%s error=%s",
                    label,
                    record.user.username,
                    record.item_id,
                    str(e),
                )
                if getattr(settings, 'DEBUG', False):
                    traceback.print_exc()
                continue
            cls.build_func_dict(local_dict.items(), catalog_name, package_name, func_dict, c_dict)

    @staticmethod
    def add_categories(node, ctg, uname=None, id_prefix=''):
        cats = ctg.split('.')  # sub categories
        cur_node = node
        par_id = node.id
        cur_path = ""
        for cur_node_name in cats:
            cur_path = joinx((cur_path, cur_node_name), qconst.name_separator)
            cur_node_id = id_prefix + cur_path
            cur_node = cur_node.add_category_node(par_id, cur_node_id, cur_node_name, cur_node_name, uname)
            cur_node_path_dot = cur_path.replace(qconst.name_separator, '.')
            # | a user's own folder has no description, unlike the standard categories
            cur_node.desc = '' if id_prefix else (
                qfunc_categ_info.get(cur_path, {}).get('desc')
                or qfunc_categ_info.get(cur_node_path_dot, {}).get('desc')
                or qfunc_categ_info.get(cur_node_name, {}).get('desc')
                or cur_node.title
            )
            par_id = cur_node_id
        return cur_node  # last sub category added

    @staticmethod
    def normalize_folder(folder):
        """A user's folder path as dot separated lowercase segments, e.g. 'My Jobs/Steel' => 'my_jobs.steel'.

        Segments keep only letters, digits, spaces and underscores; empty ones are dropped.
        """
        if not isinstance(folder, str):
            return ''
        segments = (re.sub(r'[^\w ]', '', seg).strip() for seg in re.split(r'[./]', folder))
        segments = (re.sub(r'\s+', '_', seg).lower()[:FOLDER_NAME_MAX] for seg in segments if seg)
        return '.'.join(list(segments)[:FOLDER_DEPTH_MAX])

    @classmethod
    def add_folder(cls, root, folder, uname=None):
        """The node of the user's folder path under root, created as needed; root itself for no folder."""
        return cls.add_categories(root, folder, uname, FOLDER_ID_PREFIX) if folder else root

    @staticmethod
    def prune_folders(folder):
        """Remove the user folder, and the user folders above it, while they are empty."""
        while folder is not None and folder.id.startswith(FOLDER_ID_PREFIX) and not folder.children:
            parent = folder.parent
            folder.delete_tree()
            folder = parent

    @classmethod
    def remove_leaf(cls, node):
        """Remove the calculator leaf and the user folders it leaves empty."""
        parent = node.parent
        node.delete_tree()
        cls.prune_folders(parent)

    @classmethod
    def upsert_leaf(cls, root, func_id, title_fn, scope, uname='', sub_type=''):
        """Add the calculator leaf under root (or its folder), or refresh its title, desc and tags if it exists.

        title_fn(func_id, scope=) returns (title, desc, tags) plus, optionally, the normalized user folder path.
        An existing leaf is moved when its folder changed. Raises whatever title_fn raises, so the caller decides how
        to log it.
        """
        title, desc, tags, *folder = title_fn(func_id, scope=scope)
        parent = cls.add_folder(root, folder[0] if folder else '', uname)
        func_node = root.get_node_by_id(func_id)
        old_parent = None
        if func_node is not None and func_node.parent is not parent:
            old_parent = func_node.parent
            func_node.delete_tree()
            func_node = None
        if func_node is None:
            func_node = TreeNode(nid=func_id, name=func_id, title=title, desc=desc, tags=tags,
                                 is_leaf=True, node_type='c', sub_type=sub_type)
            func_node.uname = uname
            parent.add_child(func_node)
        else:
            func_node.title = title
            func_node.desc = desc
            func_node.tags = tags
        cls.prune_folders(old_parent)  # | after the new parent is linked, which may be an ancestor of the old one
        return func_node

    @classmethod
    def populate(cls, root, ctg_dict, c_dict, title_fn, scope, uname=None, sub_type='', flat_ctg=None, on_leaf=None):
        """Add category and calculator leaf nodes under root.

        title_fn(func_id, scope=) returns (title, desc, tags) plus, optionally, the normalized user folder path to
        place the calculator in under its category; a calculator for which it raises is left out.
        Calculators of the category flat_ctg are added directly under root. on_leaf(func_node) is called per leaf.
        """
        func_ids_by_pkg = {}
        for func_id, pkg in c_dict.items():
            func_ids_by_pkg.setdefault(pkg, []).append(func_id)

        for pkg, ctg in ctg_dict.items():
            cur_node = root if ctg == flat_ctg else cls.add_categories(root, ctg, uname)
            for func_id in func_ids_by_pkg.get(pkg, ()):
                try:
                    title, desc, tags, *folder = title_fn(func_id, scope=scope)
                    parent = cls.add_folder(cur_node, folder[0], uname) if folder else cur_node
                    func_node = TreeNode(nid=func_id, name=func_id, title=title, desc=desc, tags=tags,
                                         is_leaf=True, node_type='c', sub_type=sub_type)
                    func_node.uname = uname or ''
                    parent.add_child(func_node)
                    if on_leaf:
                        on_leaf(func_node)
                except Exception:
                    # | title_fn raises if not in demo mode and the function has no __info()
                    pass
