# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.urls import include, path
from django.views.generic import TemplateView
from . import views
from django.conf import settings
from qutil import not_found
from django.contrib.sitemaps import views as sm_views
from .mod_sitemap import *
from django.urls import re_path
from django.views.static import serve

from django.contrib import admin

admin.site.site_header = "qCalc Administration"
admin.site.site_title = "qCalc Admin"
admin.site.index_title = "Welcome to qCalc Administration"

urlpatterns = [
    path("robots.txt", views.serve_app_static_file("robots.txt", "text/plain")),
    path("favicon.ico", views.serve_app_static_file("favicon.png", "image/png")),
    path("", views.show_home, name="home"),
    path("api-auth/", include("rest_framework.urls")),
    path('page/console/execute/', views.execute_command, name='execute_command'),
    path('page/contact/', views.contact_view, name='contact-form'),
    path('thank_you/', TemplateView.as_view(template_name="contact_thank_you.html"), name='thank_you'),
    path('page/<str:pname>/', views.show_page, name='show-page'),
    path('page/help/<str:pname>/', views.q1_add_page_help, name='add-page-help'),
    path('cal/', views.show_cal, name='show_cal'),
    path('tour/', views.show_tour, name='show-tour'),
    path('help/', views.show_docs, name='show-docs'),
    path('docs/<path:pname>', views.q1_add_doc, name='add-page-doc'),  # pname, no end-slash
    # path('read/<path:rpname>', views.q1_add_doc, name='add-page-read'),  # rpname, no end-slash
    path('doc_create/<path:file>', views.q1_create_doc, name='create-doc'),  # file, no end-slash
]

urlpatterns += [
    path('<str:pname>/', not_found, name='not_found'),
]

sitemaps = {
    'pages': QSitemapPage,
    'docs': QSitemapDoc,
    'categories': QSitemapCat,
    'calculators': QSitemapCal,
    'help': QSitemapHelp,
    'quantities': QSitemapQty,
}

urlpatterns += [
    path("sitemap.xml", sm_views.index, {'sitemaps': sitemaps},
         name="django.contrib.sitemaps.views.index"),
    path("sitemap-<section>.xml", sm_views.sitemap, {'sitemaps': sitemaps},
         name="django.contrib.sitemaps.views.sitemap"),
]

if not settings.DEBUG:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT,
        }),
    ]
