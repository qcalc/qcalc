# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

# from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.contrib import admin
from django.utils.crypto import get_random_string
from qutil import fid2owner
from .mod_redis import publish_redis_action
from .mod_ucals import UCals
import logging

logger = logging.getLogger(__name__)


class MyStuff(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mystuffs', db_index=True)
    object_id = models.CharField(max_length=10, db_index=True)  # Prefix or type of object, e.g. mycal, pref, fav
    item_id = models.CharField(max_length=50, db_index=True)  # Unique identifier for each item within the object type
    item = models.JSONField()  # Storing Python code snippets or serialized data
    is_public = models.BooleanField(default=False)
    added_on = models.DateTimeField(auto_now_add=True)
    changed_on = models.DateTimeField(auto_now=True)  # Automatically updated on every save

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'object_id', 'item_id'], name='unique_user_item')
        ]
        indexes = [
            models.Index(fields=['user', 'object_id', 'item_id']),  # Adding composite index for performance
        ]

    def __str__(self):
        return f"{self.user.username}: {self.object_id}-{self.item_id}"

    def save(self, *args, **kwargs):
        if self.object_id == 'mycal':
            from calc import QCals
            if self.is_public and self.item_id not in QCals.pc_list:
                code = self.item
                if code:
                    cal_id, cal_name, cal_owner = fid2owner(self.item_id)
                    updated = QCals.update_public_cal(self.item_id, cal_owner, code)
                    if updated: publish_redis_action(
                        channel="qcalc_channel",
                        action="update_public_cal",
                        cal_id=self.item_id,
                        cal_owner=cal_owner,
                        code=code
                    )
            elif not self.is_public and self.item_id in QCals.pc_list:
                deleted = QCals.delete_public_cal(self.item_id)
                if deleted:
                    publish_redis_action(
                        channel="qcalc_channel",
                        action="delete_public_cal",
                        cal_id=self.item_id
                    )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.object_id == 'mycal':
            from calc import QCals
            if self.is_public and self.item_id in QCals.pc_list:
                deleted = QCals.delete_public_cal(self.item_id)
                if deleted:
                    publish_redis_action(
                        channel="qcalc_channel",
                        action="delete_public_cal",
                        cal_id=self.item_id
                    )

            try:
                # Delete item_id from tree
                cal_id, cal_name, cal_owner = fid2owner(self.item_id)
                UCals().del_cal(cal_name)
                # Delete cal_id if it is also a public cal
                QCals.delete_public_cal(cal_id)
                # | Delete all user's variants for the item_id from MyInput if object_id is 'input'
                MyInput.objects.filter(object_id='input', item_id=self.item_id).delete()
                # | Delete all user's favorites for the item_id from MyStuff if object_id is 'fav'
                MyStuff.objects.filter(object_id='fav', item_id=self.item_id).delete()
            except Exception as e:
                logger.error(f'MSD: {str(e)}')

        super().delete(*args, **kwargs)  # Proceed with deletion


class MyInput(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='myinputs', db_index=True)
    object_id = models.CharField(max_length=10, db_index=True)  # Prefix or type of object, e.g. cal
    item_id = models.CharField(max_length=50,
                               db_index=True)  # Unique identifier for each item within the object type, e.g. bmi
    variant_id = models.IntegerField()  # 1, 2, 4, etc. there can be gaps because of deletion
    description = models.CharField(max_length=100)  # Description of the variant stored outside the item JSON
    item = models.JSONField()  # Storing serialized data
    is_shared = models.BooleanField(default=False)
    is_example = models.BooleanField(default=False)
    access_token = models.CharField(max_length=64, unique=True, blank=True, null=True)
    added_on = models.DateTimeField(auto_now_add=True)
    changed_on = models.DateTimeField(auto_now=True)  # Automatically updated on every save

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'object_id', 'item_id', 'variant_id'],
                                    name='unique_user_item_variant')
        ]
        indexes = [
            models.Index(fields=['user', 'object_id', 'item_id', 'variant_id']),  # Composite index for performance
        ]

    def __str__(self):
        return f"{self.user.username}: {self.object_id}-{self.item_id}-{self.variant_id}"

    def save(self, *args, **kwargs):
        # Check and convert the data before saving
        # self.data = normalize_json(self.data)

        # Automatically generate an access token if the variant is shared
        if self.is_shared and not self.access_token:
            self.access_token = get_random_string(length=16)
        elif not self.is_shared:
            self.access_token = None  # Clear token if unsharing
        super().save(*args, **kwargs)

    @classmethod
    def from_db_value(cls, value, expression, connection):
        # Handle deserialization if needed, for now, just return the value
        return value  # This can be modified based on your needs


# Admin Customization
@admin.register(MyStuff)
class MyStuffAdmin(admin.ModelAdmin):
    list_display = ('user', 'object_id', 'item_id', 'is_public', 'added_on', 'changed_on')
    search_fields = ('user__username', 'object_id', 'item_id')  # Enable search on specific fields
    list_filter = ('user', 'object_id', 'is_public', 'added_on')  # Filters for the admin interface


@admin.register(MyInput)
class MyInputAdmin(admin.ModelAdmin):
    list_display = ('user', 'object_id', 'item_id', 'variant_id', 'description',
                    'is_shared', 'is_example', 'access_token', 'added_on', 'changed_on')
    search_fields = ('user__username', 'object_id', 'item_id', 'description')  # Enable search on specific fields
    list_filter = ('user', 'object_id', 'item_id', 'added_on')  # Filters for the admin interface
