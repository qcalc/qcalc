# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.urls import path
from .views import *

urlpatterns = [
    path('<path:file_path>', edit_html_file, name='edit_html_file'), # file no end-slash
]
