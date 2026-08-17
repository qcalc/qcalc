# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin
from django.views import defaults as default_views

urlpatterns = ([
                   # Django Admin, use {% url 'admin:index' %}
                   path(settings.ADMIN_URL, admin.site.urls),
                   # User management
                   path("users/", include("qsite.users.urls", namespace="users")),
                   path("accounts/", include("allauth.urls")),
                   # Your stuff: custom urls includes go here
                   path('calc/', include('calc.urls')),
                   path('catalog/', include('catalog.urls')),
                   path('qedit/', include('qedit.urls')),
                   path("select2/", include("django_select2.urls")),
               ]
               + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]

    if "debug_toolbar" in settings.INSTALLED_APPS:
        # import debug_toolbar
        # urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
        urlpatterns = [path("__debug__/", include('debug_toolbar.urls', namespace='debug_toolbar'))] + urlpatterns
    if "silk" in settings.INSTALLED_APPS:
        urlpatterns = [path('silk/', include('silk.urls', namespace='silk'))] + urlpatterns

urlpatterns += [
    path('', include('qsite.urls')),
    # re_path(r'^(?P<path>([^/]+/)*)$', include('qsite.urls')),
]
