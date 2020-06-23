# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ...unit.exporter import delay_export, delay_export_all_bindings
from openerp.addons.connector.event import on_record_create, on_record_write

from openerp.addons.connector.unit.mapper import (
    mapping,
    ExportMapper
)

from ...unit.mapper import TranslationNuvemshopExportMapper
from ...unit.exporter import TranslationNuvemshopExporter
from ...backend import nuvemshop


CATEGORY_EXPORT_FIELDS = [
    'name',
    'parent_id',
    'description',
    'handle',
    'seo_title',
    'seo_description',
]

@on_record_create(model_names='nuvemshop.product.category')
def nuvemshop_product_template_create(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    delay_export(session, model_name, record_id, priority=20)


@on_record_write(model_names='product.category')
def product_category_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(CATEGORY_EXPORT_FIELDS):
        delay_export_all_bindings(session, model_name, record_id)


@on_record_write(model_names='nuvemshop.product.category')
def nuvemshop_product_category_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(CATEGORY_EXPORT_FIELDS):
        delay_export(session, model_name, record_id, fields)


@nuvemshop
class ProductCategoryExporter(TranslationNuvemshopExporter):
    _model_name = ['nuvemshop.product.category']

@nuvemshop
class ProductCategoryExportMapper(TranslationNuvemshopExportMapper):
    _model_name = 'nuvemshop.product.category'
    direct = [
        ('name', 'name'),
        ('description', 'description'),
        ('handle', 'handle'),
        ('seo_title', 'seo_title'),
        ('seo_description', 'seo_description'),
    ]

    _translatable_fields = {
        'nuvemshop.product.category': [
            'name',
            'description',
            'handle',
            'seo_title',
            'seo_description',
        ],
    }

    @mapping
    def translatable_fields(self, record):
        trans = TranslationNuvemshopExporter(self.environment)
        return self.convert_languages(
            trans.get_record_by_lang(record.id), self._translatable_fields[self._model_name])
