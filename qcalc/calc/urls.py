# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.urls import path, re_path
from calc import views, views_tabulator
from qsite.views import show_docs

urlpatterns = [
    path('', views.clear_calcs, name='clear-calc'),
    path('core/<str:fname>/', views.q1_func_to_form_core, name='calc-core-func'),
    re_path(r'^core/(?P<path>([^/]+/)*)$', views.q1_func_to_form_core, name='calc-core-func-args'),

    path('run/<str:fname>/', views.q1_run_func, name='calc-run-func'),
    re_path(r'^run/(?P<path>([^/]+/)*)$', views.q1_run_func, name='calc-run-func-args'),
    path('add/', views.q1_add_func, name='calc-add-func'),
    path('step2/', views.q1_step2, name='calc-step2'),
    path('open/', views.q1_open_func, name='calc-open-func'),
    path('help/', show_docs, name='show-docs'),
    path('help/<str:fname>/', views.q1_add_func_help, name='calc-add-func-help'),
    path('dump/', views.dump, name='calc-dump'),
    path('io/', views.calc_io, name='calc-io'),
    path('mems/', views.mems, name='calc-mems'),
    path('lists/', views.lists, name='calc-lists'),
    path('cart/', views.add_to_cart, name='calc-cart'),
    path('save/', views.q11440b_get_saved_io, name='calc-save'),
]

urlpatterns += [
    path('fill_input_data/<str:scope>/<str:fname>/<str:varid>/', views.fill_input_data, name='fill_input_data'),
    path('scroll_input/<str:scope>/<str:item_id>/<str:cid>/', views_tabulator.scroll_input, name='scroll_input'),

    path('tabulate_input/<str:scope>/<str:item_id>/<str:cid>/', views_tabulator.tabulate_input, name='tabulate_input'),
    path('get_input_data/<str:scope>/<str:item_id>/', views_tabulator.get_input_data, name='get_input_data'),  # used
    path('update_input/<int:id>/', views_tabulator.update_input, name='update_input'),  # used in tabulator
    path('delete_input/<int:id>/', views_tabulator.delete_input, name='delete_input'),  # used in tabulator

    path('tabulate_stuff/<str:scope>/<str:item_id>/<str:cid>/', views_tabulator.tabulate_stuff, name='tabulate_stuff'),
    path('get_stuff_data/<str:scope>/<str:item_id>/', views_tabulator.get_stuff_data, name='get_stuff_data'),  # used
    path('update_stuff/<int:id>/', views_tabulator.update_stuff, name='update_stuff'),  # used in tabulator
    path('delete_stuff/<int:id>/', views_tabulator.delete_stuff, name='delete_stuff'),  # used in tabulator
]

urlpatterns += [
    # | follwoing must be the last
    path('<str:fname>/', views.q1999_func_to_form, name='calc-func'),
    re_path(r'^(?P<path>([^/]+/)*)$', views.q1999_func_to_form, name='calc-func-args'),
]
