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


TEMPLATE_EXPORT_FIELDS = [
    'name',
    # 'parent_id',
    'description',
    'handle',
    'published',
    'free_shipping',
    'canonical_url',
    'seo_title',
    'seo_description',
    # 'created_at',
    # 'updated_at',
    'variants',
    'tags',
    'images',
    'categories',
]

@on_record_create(model_names='nuvemshop.product.template')
def nuvemshop_product_template_create(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    delay_export(session, model_name, record_id, priority=20)


@on_record_write(model_names='product.template')
def product_template_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(TEMPLATE_EXPORT_FIELDS):
        delay_export_all_bindings(session, model_name, record_id, fields)


@on_record_write(model_names='nuvemshop.product.template')
def nuvemshop_product_template_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(TEMPLATE_EXPORT_FIELDS):
        delay_export(session, model_name, record_id, fields)


@nuvemshop
class ProductTemplateExporter(TranslationNuvemshopExporter):
    _model_name = ['nuvemshop.product.template']

@nuvemshop
class ProductTemplateExportMapper(TranslationNuvemshopExportMapper):
    _model_name = 'nuvemshop.product.template'
    direct = [
        ('name', 'name'),
        ('handle', 'handle'),
        ('published', 'published'),
        ('free_shipping', 'free_shipping'),
        ('canonical_url', 'canonical_url'),
        ('seo_title', 'seo_title'),
        ('seo_description', 'seo_description'),
        ('brand', 'brand'),
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
        # ('variants', 'variants'),
        # ('tags', 'tags'),
        # ('images', 'images'),
        # ('categories', 'categories'),
        #TODO campo tags
    ]

    @mapping
    def description(self, record):
        if record.description_html:
            return {'description': record.description_html}
        else:
            return{'description': record.description}

    @mapping
    def images(self, record):
        images = []
        for image in record.image_ids:
            if image.url:
                images.append(
                    {
                        'src': image.url,
                        'name': image.name,
                        'position': image.sequence
                    }
                )
        return {'images': images}

    @mapping
    def categories(self, record):
        ext_categ_ids = []
        binder = self.binder_for('nuvemshop.product.category')
        categories = list(set(record.categ_ids + record.categ_id))
        for category in categories:
            binder_id = binder.to_backend(category.id, wrap=True)
            if binder_id:
                ext_categ_ids.append(int(binder_id))
            # TODO: exportar a categoria para ser vinculada

        return {'categories': ext_categ_ids}

    @mapping
    def variants(self, record):
        if record.product_variant_count == 1:
            return {
            "variants": [
                {
                    "price": str(record.lst_price),
                    "weight": str(record.weight),
                    "sku": record.default_code,
                    "barcode": record.ean13,
                    # TODO: Controle de estoque
                    # "stock_management": True,
                    # "stock": 12,
                }
            ]
        }
        #TODO: fazer importaçao para cada variant

    _translatable_fields = {
        'nuvemshop.product.template': [
            'name',
            'description',
            'handle',
            'seo_title',
            'seo_description',
            'attributes',
        ],
    }

    @mapping
    def translatable_fields(self, record):
        trans = TranslationNuvemshopExporter(self.environment)
        return self.convert_languages(
            trans.get_record_by_lang(record.id), self._translatable_fields[self._model_name])
