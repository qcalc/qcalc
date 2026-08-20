# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from .mod_cache import QMeta, QMyCal, QFav, QMem
from .mod_qcals import QCals
from qutil.mod_tree import dict_to_tree
from qutil import TreeNode, create_category_node, user_name, get_functions, \
    extract_common_prefix, names2fid, fid2owner
import copy
import logging

logger = logging.getLogger(__name__)


def get_uc_list():
    return QMeta.getp1('uc_list', [])


class UCals:
    TreeNode.setup()

    # calc_root: TreeNode('personal', 'personal', 'Personal')

    def __init__(self):
        self.sc_tree = None
        self.sc_list = None
        self.sctg_dict = None
        self.sc_dict = None
        self.sfunc_dict = None

        self.uc_tree = None
        self.uc_list = None
        self.uctg_dict = None
        self.uc_dict = None
        self.ufunc_dict = None

        # self.calc_root = TreeNode('personal', 'personal', 'Personal')
        # # noinspection PyProtectedMember
        # self.calc_root._index_node()
        self.calc_root = create_category_node('personal', 'personal', 'Personal')
        self.cal_owner = user_name()

    def get_code(self, cal_name):
        cal_id = names2fid(self.cal_owner, cal_name)
        code = QMyCal.getp1(cal_id, '')
        if code:
            return code
        else:
            return ''

    def del_tree(self, node_id="personal"):
        utree_node = self.calc_root.get_node_by_id(node_id)
        if utree_node:
            utree_node.delete_tree()
            del utree_node
            self.__init__()

    def ufavs_dict_to_tree(self, fav_dict: dict, parent: TreeNode, id_prefix=''):
        for func_id in fav_dict:
            child = QCals.calc_root.get_node_by_id(func_id)  # | qcalc
            if not child:
                child = QCals.pcalc_root.get_node_by_id(func_id)  # | public cal
                if not child:
                    child = self.calc_root.get_node_by_id(func_id)  # | owncal

            if child:
                child = copy.deepcopy(child)
                child.id = f'{id_prefix}{func_id}'
                child.uname = parent.uname
                parent.add_child(child)

    def get_tree(self):
        # create tree for the current user in the current worker process
        self.del_tree("created")  # id = func_id
        self.del_tree("shared")  # id = func_id+variant_info (vowner,varinat_id,token)
        self.del_tree("favorites")  # id = same as above

        uc_tree = QMeta.getp1('uc_tree', {})
        created_node = dict_to_tree(uc_tree)
        if created_node:
            created_node.uname = user_name()
            self.calc_root.add_tree(created_node)

        sc_tree = QMeta.getp1('sc_tree', {})
        shared_node = dict_to_tree(sc_tree)
        if shared_node:
            shared_node.uname = user_name()
            self.calc_root.add_tree(shared_node)  # , allowdups=True)

        ufavs_dict = QFav.getp({})
        if ufavs_dict:
            # favorites_node = TreeNode('favorites', 'favorites', 'My Favorites')
            # favorites_node.data["path"] = "Favorites"
            # favorites_node.uname = user_name()
            favorites_node = create_category_node('favorites', 'favorites',
                                                  'My Favorites', user_name())

            # | add standard calculators found in ufavs_dict to favorites node
            # | add user calculators found in ufavs_dict to favorites node
            self.ufavs_dict_to_tree(ufavs_dict, favorites_node, id_prefix='f:')
            # | add favorites subtree to the main tree
            self.calc_root.add_tree(favorites_node)

        self.calc_root.update_all_descendant_leafs_count()
        return self.calc_root

    def edit_cal(self, cal_name, code):  # , is_public: bool = False
        uc_list: list = QMeta.getp1('uc_list', [])
        uc_dict: dict = QMeta.getp1('uc_dict', {})
        uc_tree: dict = QMeta.getp1('uc_tree', {})

        utree = dict_to_tree(uc_tree)
        package_name = 'created'
        catalog_name = user_name()
        functions = get_functions(code)
        results = []

        added = False
        cal_name_determind = extract_common_prefix(functions)
        if cal_name_determind == '':
            raise Exception(
                f"Error (SUC): Meta __info() not found. You may click on [Format code] to create one automatically.")
        elif cal_name == '':
            cal_name = cal_name_determind
        elif cal_name != '' and cal_name_determind != cal_name:
            raise Exception(
                f"Error (SUC): Specified name '{cal_name}' mismatches with determind name '{cal_name_determind}'")

        cal_id = names2fid(catalog_name, cal_name)
        update = cal_id in uc_list
        _ = QCals.safe_exec(code)  # | validate and returns exception if invalid code

        for ufname in functions:
            # | ufaddr = locals.get(ufname, None)
            # | this dynamic address allocated from within the current worker process and
            # | hence not useful to store and use in future because
            # | successive request can be processed by a different worker process
            # | where this function address may not exist

            results.append(f'{ufname}() is defined')
            if ufname == cal_name:
                uc_dict[cal_id] = package_name
                if not update:
                    added = True
                    uc_list.append(cal_id)

        if added:
            uc_list.sort()
        results.append(f"Run the calculator using '{cal_name}'")
        QMeta.setp1('uc_list', uc_list)
        QMeta.setp1('uc_dict', uc_dict)
        QMyCal.setp1(cal_id, code)  # QCals.func_title_desc_tags needs it

        ctg_node_id = "created"
        if not utree:
            ctg_node = create_category_node(ctg_node_id, "created", "created", self.cal_owner)
        else:
            ctg_node = utree

        for ufname in functions:
            func_id = names2fid(catalog_name, ufname)
            if func_id not in uc_dict:
                continue
            update = func_id in uc_list
            try:
                title, desc, tags = QCals.func_title_desc_tags(func_id, scope='o')
                # func_id = ufname
                if not update:
                    # dead code? as line 145: uc_list.append(cal_id), so update is true
                    func_node = TreeNode(
                        nid=func_id, name=func_id, title=title, desc=desc,
                        tags=tags, is_leaf=True, node_type='c', sub_type='e')
                    func_node.uname = self.cal_owner
                    ctg_node.add_child(func_node)
                else:
                    func_node, flag = ctg_node.add_node_if_not_found(ctg_node_id, func_id, func_id)
                    func_node.title = title
                    func_node.desc = desc
                    func_node.tags = tags
                    func_node.is_leaf = True
                    func_node.node_type = 'c'
                    func_node.sub_type = 'e'
                    func_node.uname = self.cal_owner
            except Exception as e:
                logger.exception(f"Exception occurred: {e}")  # Example: Log the exception

        ctg_node.update_all_descendant_leafs_count()
        ctg_node.sort_by()
        uc_tree = ctg_node.tree_to_dict()
        QMeta.setp1('uc_tree', uc_tree)
        # | QMy.setp1(request, cal_id, code)
        ctg_node.delete_tree()
        del ctg_node
        QMem.clear(cal_id)
        return results

    def del_cal(self, cal_name):
        cal_id = names2fid(self.cal_owner, cal_name)
        uc_list = QMeta.getp1('uc_list', [])
        if cal_id not in uc_list:
            return f'{cal_name} not found'
        uc_dict = QMeta.getp1('uc_dict', {})
        uc_tree = QMeta.getp1('uc_tree', {})
        utree = dict_to_tree(uc_tree)

        try:
            uc_list.remove(cal_id)
            del uc_dict[cal_id]
            cur_node = utree.get_node_by_id(cal_id)
            cur_node.delete_tree()
            QMyCal.delp1(cal_id)
            QMeta.setp1('uc_list', uc_list)
            QMeta.setp1('uc_dict', uc_dict)
            uc_tree = utree.tree_to_dict()
            QMeta.setp1('uc_tree', uc_tree)
            result = f'{cal_name} deleted'
        except Exception as e:
            result = f'{cal_name} could not be deleted because {str(e)}'
            pass

        utree.delete_tree()
        del utree
        return result

    def package_contents_private(self, request):
        self.ufunc_dict = {}
        self.uc_dict = {}
        self.uctg_dict = {}
        self.uc_list = []

        from .models import MyStuff
        mystuffs = MyStuff.objects
        user = request.user
        prvcals = mystuffs.filter(user=user, object_id='mycal')  # , is_public=False)
        logger.info(f'Scanning: mycal')

        for record in prvcals:
            package_name = f"ucals.{record.user.username}"
            catalog_name = f"{record.user.username}"

            if package_name not in self.uctg_dict:
                self.uctg_dict[package_name] = catalog_name
            code = record.item
            local_dict = QCals.safe_exec(code)
            QCals.build_func_dict(local_dict.items(), catalog_name, package_name, self.ufunc_dict, self.uc_dict)

        self.uc_list[:] = self.uc_dict.keys()
        self.uc_list.sort()

        # QMeta.setp1('ufunc_dict', self.ufunc_dict)
        QMeta.setp1('uc_dict', self.uc_dict)
        # QMeta.setp1('uctg_dict', self.uctg_dict)
        QMeta.setp1('uc_list', self.uc_list)

    def create_catalog_calc_private(self, request):
        request.ufunc_dict = {}
        uname = user_name(request)
        created_node = create_category_node("created", "created", "Created by Me", uname)
        self.calc_root.add_child(created_node)
        for pkg, ctg in self.uctg_dict.items():
            if ctg != self.cal_owner:
                cur_node = QCals.add_catagories_to_node(created_node, ctg, uname)
                # cur_node.uname = uname
            else:
                cur_node = created_node

            func_ids = [func_id for func_id, categ in self.uc_dict.items() if categ == pkg]
            for func_id in func_ids:
                try:
                    title, desc, tags = QCals.func_title_desc_tags(func_id, scope='o')
                    func_node = TreeNode(nid=func_id, name=func_id, title=title, desc=desc, tags=tags,
                                         is_leaf=True, node_type='c', sub_type='e')
                    func_node.uname = uname
                    cur_node.add_child(func_node)
                except Exception as _e:
                    pass

        created_node.update_all_descendant_leafs_count()
        created_node.sort_by()
        self.uc_tree = created_node.tree_to_dict()
        QMeta.setp1('uc_tree', self.uc_tree)

    def package_contents_shared(self, request):
        self.sfunc_dict = {}
        self.sc_dict = {}
        self.sctg_dict = {}
        self.sc_list = []

        from .models import MyStuff
        mystuffs = MyStuff.objects
        user = request.user
        shrcals = mystuffs.filter(user=user, object_id='othcal')
        logger.info(f'Scanning: othcal')

        for record in shrcals:
            cal_id, cal_name, cal_owner = fid2owner(record.item_id)
            package_name = f"scals.{cal_owner}"
            catalog_name = f"{cal_owner}"
            if package_name not in self.sctg_dict:
                self.sctg_dict[package_name] = catalog_name
            try:
                oth_record = mystuffs.get(object_id='mycal', item_id=record.item_id)  # get 1 record
            except:
                continue

            code = oth_record.item
            local_dict = QCals.safe_exec(code)
            QCals.build_func_dict(local_dict.items(), catalog_name, package_name, self.sfunc_dict, self.sc_dict)

        self.sc_list[:] = self.sc_dict.keys()
        self.sc_list.sort()

        QMeta.setp1('sc_dict', self.sc_dict)
        QMeta.setp1('sc_list', self.sc_list)

    def create_catalog_calc_shared(self, request):
        if len(self.sctg_dict.items()) == 0: return
        request.ufunc_dict = {}
        request.token = ''
        uname = user_name(request)
        shared_node = create_category_node("shared", "shared", "Shared with Me", uname)
        self.calc_root.add_child(shared_node)
        for pkg, ctg in self.sctg_dict.items():
            if ctg != self.cal_owner:
                cur_node = QCals.add_catagories_to_node(shared_node, ctg, uname)
            else:
                cur_node = shared_node

            func_ids = [func_id for func_id, categ in self.sc_dict.items() if categ == pkg]
            for func_id in func_ids:
                try:
                    title, desc, tags = QCals.func_title_desc_tags(func_id, scope='s')
                    func_node = TreeNode(nid=func_id, name=func_id, title=title, desc=desc, tags=tags,
                                         is_leaf=True, node_type='c')
                    func_node.uname = uname
                    cur_node.add_child(func_node)
                except Exception as _e:
                    pass

        shared_node.update_all_descendant_leafs_count()
        shared_node.sort_by()
        self.sc_tree = shared_node.tree_to_dict()
        QMeta.setp1('sc_tree', self.sc_tree)


def register_shared_cal(func_id, token):
    cal_id, cal_name, owner = fid2owner(func_id)
    uname = user_name()
    sc_list: list = QMeta.getp1('sc_list', [])
    sc_dict: dict = QMeta.getp1('sc_dict', {})
    sc_tree: dict = QMeta.getp1('sc_tree', {})

    stree = dict_to_tree(sc_tree)
    package_name = 'shared'

    if cal_id not in sc_dict:
        sc_dict[cal_id] = package_name
        QMeta.setp1('sc_dict', sc_dict)

    if cal_id not in sc_list:
        sc_list.append(cal_id)
        sc_list.sort()
        QMeta.setp1('sc_list', sc_list)

    ctg_node_id = "shared"
    if not stree:
        ctg_node = create_category_node(ctg_node_id, "shared", "Shared with Me", uname)
    else:
        ctg_node = stree

    try:
        title, desc, tags = QCals.func_title_desc_tags(cal_id)
        func_node = TreeNode(
            nid=cal_id, name=cal_id, title=title, desc=desc,
            tags=tags, is_leaf=True, node_type='c')
        func_node.uname = uname
        ctg_node.add_child(func_node)
    except Exception as e:
        logger.exception(f"Exception occurred: {e}")  # Example: Log the exception

    ctg_node.update_all_descendant_leafs_count()
    ctg_node.sort_by()
    sc_tree = ctg_node.tree_to_dict()
    QMeta.setp1('sc_tree', sc_tree)
    ctg_node.delete_tree()
    del ctg_node


def unregister_shared_cal(func_id):  # review tree delete
    cal_id, cal_name, owner = fid2owner(func_id)
    sc_list = QMeta.getp1('sc_list', [])
    if cal_id not in sc_list:
        return f'{cal_name} not found'
    sc_dict = QMeta.getp1('sc_dict', {})
    sc_tree = QMeta.getp1('sc_tree', {})
    stree = dict_to_tree(sc_tree)

    try:
        sc_list.remove(cal_id)
        del sc_dict[cal_id]
        node = stree.get_node_by_id(cal_id)
        if node:
            node.delete_tree()
        QMeta.setp1('sc_list', sc_list)
        QMeta.setp1('sc_dict', sc_dict)
        uc_tree = stree.tree_to_dict()
        QMeta.setp1('sc_tree', uc_tree)
        result = f'{cal_name} deleted'
    except Exception as e:
        result = f'{cal_name} could not be deleted because {str(e)}'

    stree.delete_tree()
    del stree
    return result
