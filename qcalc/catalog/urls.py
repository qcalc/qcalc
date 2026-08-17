# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.urls import path
from catalog import views
from qutil import not_found
from qsite.views import show_docs

urlpatterns = [
    path('', views.calc_tree, name='catalog-index'),

    path('calc/', views.calc_tree, name='calc-tree'),
    path('calc/<str:category>/', views.calc_dir, name='calc-dir'),  # should be after 'tree'
    path('user/', views.ucalc_tree, name='user-tree'),
    path('user/<str:category>/', views.ucalc_dir, name='user-dir'),
    path('pcalc/', views.pcalc_tree, name='pcalc-tree'),
    path('pcalc/<str:category>/', views.pcalc_dir, name='pcalc-dir'),

    path('qty/', views.qty_tree, name='qty-tree'),
    path('qty/<str:category>/', views.qty_dir, name='qty-dir'),

    path('ulist/', views.qty_ulist, name='qty-ulist'),
    path('help/', show_docs, name='show-docs'),
    path('search/', views.search_catalog, name='catalog-search'),  # ?q=body
    path('search_func/', views.search_func, name='catalog-search-func'),  # ?qf=bmi, not used
    path('search_pfunc/', views.search_func, name='catalog-search-pfunc'),  # ?qf=bmi, not used
    path('search_unit/', views.search_unit, name='catalog-search-unit'),  # ?qu=ft
    path('search_tag/', views.search_tag, name='catalog-search-tag'),  # ?qf=bmi
    path('page/<str:pname>/', views.show_page, name='show-page'),
    path('toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('toggle_share/', views.toggle_share, name='toggle_share'),

    path('<str:pname>/', not_found, name='not_found'),  # should be last item
]
