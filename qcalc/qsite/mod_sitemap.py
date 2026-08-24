# SPDX-License-Identifier: MIT
# Copyright (c) 2024-2026 Debasish C Saha

from django.contrib.sitemaps import Sitemap
from calc import QCals
from qcore import _base_slugs
from datetime import date
from .mod_docs import build_docs_tree


class QSitemapPage(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    @classmethod
    def items(cls):
        return [
            '/calc/', '/help/',
            '/catalog/calc/calculators/', '/catalog/calc/tree/', '/catalog/qty/units/', '/catalog/qty/tree/',
            '/page/cal/', '/page/console/', '/page/about/', '/page/privacy-policy/',
            '/page/terms-conditions/', '/page/contact/',
        ]

    @classmethod
    def lastmod(cls, obj):
        return date(2024, 8, 3)

    @classmethod
    def location(cls, obj):
        return f'{obj}'


class QSitemapDocs(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    @classmethod
    def items(cls):
        root = build_docs_tree()
        return [node.name for node in root.depth_first() if node.is_leaf and node.name]

    @classmethod
    def lastmod(cls, obj):
        return date(2024, 8, 3)

    @classmethod
    def location(cls, obj):
        return f'/docs/{obj}'


class QSitemapCal(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    @classmethod
    def items(cls):
        return QCals.qc_user_list

    @classmethod
    def lastmod(cls, obj):
        return date(2024, 8, 3)

    @classmethod
    def location(cls, obj):
        return f'/calc/{obj}/'


class QSitemapCat(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    @classmethod
    def items(cls):
        nodes = QCals.calc_root.get_node_by_id('all')
        return [node.id for node in nodes if node.flags == '']

    @classmethod
    def lastmod(cls, obj):
        return date(2024, 8, 3)

    @classmethod
    def location(cls, obj):
        return f'/catalog/calc/{obj}/'


class QSitemapQty(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    @classmethod
    def items(cls):
        return _base_slugs

    @classmethod
    def lastmod(cls, obj):
        return date(2024, 8, 3)

    @classmethod
    def location(cls, obj):
        return f'/catalog/qty/{obj}/'
