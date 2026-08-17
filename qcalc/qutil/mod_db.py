# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

def get_object(model_class, **filters):
    try:
        obj = model_class.objects.get(**filters)
        return obj
    except model_class.DoesNotExist:
        # print("Object not found.")
        return None
    except model_class.MultipleObjectsReturned:
        # print("Multiple objects found.")
        return None

# Usage example
# owner_user = get_object_with_handling(User, username=owner)
