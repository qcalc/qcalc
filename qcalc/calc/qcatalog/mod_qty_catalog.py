# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

import logging

import qconst
from qcore import UnitRegistry, QtyRegistry, _base_categories, _base_categ_d2s, lmt_desc, dim_to_bname, _base_names
from qutil import TreeNode
from qvars import qty_categ_info, unit_info
from .mod_qcals import QCals

logger = logging.getLogger(__name__)


def _group_node(nid, title, desc, node_type):
    return TreeNode(nid=nid, name=nid, title=title, desc=desc, is_leaf=False, node_type=node_type)


class QtyCatalog:
    """Catalog tree of units of measurement and quantities of typical objects."""

    root: TreeNode

    @classmethod
    def build(cls):
        TreeNode.setup(qconst.admin_name, qconst.demo_name, qconst.personal_name)
        root = _group_node('units', 'UoMs for Quantitites',
                           'Units of measurement for various physical quantities', 'u')
        root._index_node()

        node_base = _group_node('bases', 'Base Quantity UoMs',
                                'Units of measurement for 7 SI base quantities, 2 derived quantities and currency', 'u')
        node_comp = _group_node('composites', 'Composite Quantity UoMs',
                                'Units of measurement for physical quantities that are combinations of base quantities',
                                'u')
        node_obj = _group_node('objects', 'Quantities of Typical Objects',
                               'Magnitudes of the physical quantities of representative physical objects', 'q')
        for node in (node_base, node_comp, node_obj):
            root.add_child(node)

        cls._add_units(root, node_base, node_comp)
        cls._add_objects(root, node_obj)

        root.update_all_descendant_leafs_count()
        root.sort_by()
        cls.root = root
        QCals.bump_catalog_version()

    @staticmethod
    def _add_units(root, node_base, node_comp):
        for dim, categ in _base_categories.items():
            slug = _base_categ_d2s[dim]
            child = TreeNode(nid=slug, name=slug, title=categ, desc=qty_categ_info.get(slug, {}).get('desc', ''),
                             is_leaf=False, node_type='u')
            if dim == 'C':
                root.add_child(child)
            elif len(dim) == 1:
                node_base.add_child(child)
            else:
                node_comp.add_child(child)

            for uname in UnitRegistry.tree.get(dim, ()):
                cur_node, flag = root.add_node_if_not_found(parent_id=slug, nid=uname, name=uname)
                if not cur_node:
                    logger.error(f'>>> CCQ: Error processing {uname}')
                if flag == 0:  # newly added node
                    cur_node.title = UnitRegistry.info[uname]['long_name']
                    # | short_desc ends with a semicolon
                    cur_node.desc = UnitRegistry.short_desc(uname) + ' ' + unit_info.get(uname, {}).get('desc', '')
                    cur_node.is_leaf = True
                    cur_node.node_type = 'u'

            if len(dim) > 1:
                name = dim_to_bname(dim, _base_names)
                child.add_child(TreeNode(nid=name, name=name,
                                         title=f'({slug} base)'.replace('-', ' '),
                                         desc=qty_categ_info.get(slug, {}).get('desc', ''),
                                         is_leaf=True, node_type='u'))

    @staticmethod
    def _add_objects(root, node_obj):
        for dim in QtyRegistry.tree:
            slug = _base_categ_d2s[dim]
            title = lmt_desc(dim)
            name = f"{slug}_objects"
            node_obj.add_child(TreeNode(nid=name, name=name, title=title,
                                        desc=f"Magnitude of the \"{title}\" of representative physical objects",
                                        is_leaf=False, node_type='q'))

            for qname in QtyRegistry.tree[dim]:
                cur_node, flag = root.add_node_if_not_found(parent_id=name, nid=qname, name=qname)
                if not cur_node:
                    logger.error(f'>>> CCQ: Error processing {qname}')
                if flag == 0:  # newly added node
                    cur_node.title = QtyRegistry.info[qname]['description']
                    cur_node.desc = ''
                    cur_node.is_leaf = True
                    cur_node.node_type = 'q'
                    cur_node.data = dim
