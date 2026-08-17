# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from qutil import HtmxHttpRequest, QThread, fid2owner, is_loggedin
# | from .models import MyInput
# | lazily imported within myobjects() to avoid application initialization issue
from typing import Optional, Any
from django.utils.functional import cached_property
from django.db.models import QuerySet
from qcore import prepare_for_json, reverse_prepare_for_json


class QDBTable:
    def __init__(self, prefix):
        self.prefix = prefix

    @cached_property
    def myinputs(self):
        # | lazily imported within myinputs() to avoid application initialization issue
        from .models import MyInput
        return MyInput.objects

    @cached_property
    def mystuffs(self):
        from .models import MyStuff
        return MyStuff.objects

    @classmethod
    def _get_authenticated_user(cls):
        request: HtmxHttpRequest = QThread.get_req()
        return request.user if is_loggedin(request) else None

    def clear(self, item_id):
        user = self._get_authenticated_user()
        if not user: raise PermissionError("Login required")
        self.myinputs.filter(user=user, object_id=self.prefix, item_id=item_id).delete()

    def set_variant(self, item_id: str, variant_id: int, data: dict):
        user = self._get_authenticated_user()
        if not user: raise PermissionError("Login required")
        if variant_id == 0:
            # Handle the case where variant_id is not provided
            last_variant = self.myinputs.filter(
                user=user, object_id=self.prefix, item_id=item_id
            ).order_by('-variant_id').first()

            if last_variant:
                variant_id = last_variant.variant_id + 1
            else:
                variant_id = 1
        desc = data.get('description', '')
        # if desc == '': desc = f'{'Variant' if user != qvars.app_user else 'Example'} {variant_id}'
        if desc == '': desc = f'Variant {variant_id}'
        # Now use the determined or provided variant_id
        self.myinputs.update_or_create(
            user=user,
            object_id=self.prefix,
            item_id=item_id,
            variant_id=variant_id,
            description=desc,
            defaults={'item': prepare_for_json(data)}
        )
        return variant_id

    def get_variant(self, item_id: str, variant_id: int, var_owner:str) -> Optional[Any]:
        try:
            record = self.myinputs.get(user__username=var_owner, object_id=self.prefix,
                                       item_id=item_id, variant_id=variant_id)
            user = self._get_authenticated_user()
            if not record.is_example and (not user or var_owner != user.username):
                raise PermissionError(f"Login required for variant owner {var_owner}")

            record.item = reverse_prepare_for_json(record.item)
            return record
        except self.myinputs.model.DoesNotExist:
            return None

    def get_var_info(self, input_id: int) -> Optional[Any]:
        if input_id == 0: return None
        try:
            var = self.myinputs.get(id=input_id)
            # user = self._get_authenticated_user()
            # if var.user.username != qvars.app_user.username and (not user or var.user.username != user.username):
            #     raise PermissionError(f"Login required for variant owner {var.user.username}")
            return var
        except self.myinputs.model.DoesNotExist:
            return None

    def is_shared_cal(self, func_id)->bool:
        user = self._get_authenticated_user()
        try:
            _ = self.mystuffs.get(user=user, object_id='othcal', item_id=func_id)
            return True
        except self.mystuffs.model.DoesNotExist:
            return False

    def save_shared_cal(self, func_id, token, check_only=True) -> str:
        # | return 2=saved, 1=exists, 0=does not exist, None=unknown
        result = None
        user = self._get_authenticated_user()
        # | if current user is not owner of the function
        cal_id, cal_name, cal_owner = fid2owner(func_id)
        if user and cal_owner != '' and cal_owner != user.username:
            try:
                # | if the shared function is registered for the user, othcal record will exist
                _ = self.mystuffs.get(user=user, object_id='othcal', item_id=func_id)
                result = "1"  # | exists
            except self.mystuffs.model.DoesNotExist:
                # | if the shared function is being executed first time by the user
                # | register the function for the user (one off)
                if not check_only:
                    self.mystuffs.update_or_create(user=user, object_id='othcal', item_id=func_id, item='')
                    from .mod_ucals import register_shared_cal  # | late reference
                    register_shared_cal(func_id, token)
                    result = "2"  # | saved
                else:
                    result = "0"  # | does not exist
        return result

    def delete_shared_cal(self, func_id):
        from .mod_ucals import unregister_shared_cal  # | late reference
        unregister_shared_cal(func_id)
        user = self._get_authenticated_user()
        # | if current user is not owner of the function
        cal_id, cal_name, cal_owner = fid2owner(func_id)
        if user and cal_owner != '' and cal_owner != user.username:
            try:
                # | if the shared function is registered for the user, othcal record will exist
                record = self.mystuffs.get(user=user, object_id='othcal', item_id=func_id)
                record.delete()
            except self.mystuffs.model.DoesNotExist:
                pass

    def get_variant_from_token(self, func_id, token) -> Optional[Any]:
        try:
            # | check if the token is found and the function is shared
            record = self.myinputs.get(access_token=token, is_shared=True)
            record.item = reverse_prepare_for_json(record.item)
            token_func_id = record.item.get('function', '')
            # | check if function name is matched with function name shared by the token
            if func_id == token_func_id:
                # self.save_shared_cal(func_id, token)
                return record
            else:
                return None
        except self.myinputs.model.DoesNotExist:
            return None

    def delete_variant(self, item_id: str, variant_id: int) -> bool:
        user = self._get_authenticated_user()
        if not user: raise PermissionError("Login required")
        count, _ = self.myinputs.filter(
            user=user, object_id=self.prefix,
            item_id=item_id, variant_id=variant_id).delete()
        return count > 0

    def get_variants(self, item_id: str) -> QuerySet:
        user = self._get_authenticated_user()
        if not user: raise PermissionError("Login required")
        return self.myinputs.filter(user=user, object_id=self.prefix, item_id=item_id)


QInput = QDBTable(prefix='input')  # User calculation input
# QExample = QDBTableX(prefix='input')  # Example calculation input
