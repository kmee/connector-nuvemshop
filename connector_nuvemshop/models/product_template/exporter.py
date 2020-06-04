# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import timedelta

from ...unit.backend_adapter import GenericAdapter

from ...unit.exporter import delay_export, delay_export_all_bindings, export_record

from openerp.addons.connector.event import on_record_create, on_record_write

from openerp.addons.connector.unit.mapper import (
    mapping,
    ExportMapper,
)
from ..product_product.exporter import ProductProductExportMapper
from ...unit.mapper import TranslationNuvemshopExportMapper
from ...unit.exporter import TranslationNuvemshopExporter
from ...backend import nuvemshop
from ...connector import get_environment


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
    'brand',
    'attribute_line_ids',
    # 'created_at',
    # 'updated_at',
    'product_variant_ids',
    'tags',
    'image_ids',
    'categ_ids',
    'categ_id',
    'remote_available',
    # 'image_id',
    # 'position',
    'list_price',
    # 'promotional_price',
    # 'stock_management',
    'weight',
    # 'width',
    # 'height',
    # 'depth',
    'default_code',
    'ean13',
    # 'name',
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
    model = session.env[model_name]
    record = model.browse(record_id)
    for binding in record.nuvemshop_bind_ids:
        func = "openerp.addons.connector_nuvemshop.unit.exporter." \
               "export_record('nuvemshop.product.template', %s," \
               % binding.id
        jobs = session.env['queue.job'].sudo().search(
            [('func_string', 'like', "%s%%" % func),
             ('state', 'not in', ['done', 'failed'])]
        )
        if not jobs:
            export_record.delay(
                session, 'nuvemshop.product.template', binding.id, fields
            )



@on_record_write(model_names='nuvemshop.product.template')
def nuvemshop_product_template_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(TEMPLATE_EXPORT_FIELDS):
        delay_export(session, model_name, record_id, fields)


@nuvemshop
class ProductTemplateExporter(TranslationNuvemshopExporter):
    _model_name = ['nuvemshop.product.template']

    def _create(self, data):
        """ Create the Nuvemshop record """
        nuvemshop_record = self.backend_adapter.create(data)
        nuvemshop_variant_obj = self.env['nuvemshop.product.product']

        nuvemshop_variant_obj.with_context(connector_no_export=True).create({
            'backend_id': self.backend_record.id,
            'openerp_id': self.erp_record.product_variant_ids[0].id,
            'nuvemshop_id': nuvemshop_record.get('variants')[0].get('id'),
            'main_template_id': self.erp_record.id,
        })

        return nuvemshop_record.get('id', 0)

    def _update(self, data):
        """ Update an Nuvemshop record """
        assert self.nuvemshop_id
        return self.backend_adapter.write(self.nuvemshop_id, data)

    def _after_export(self):
        self.export_images()
        self.export_variants()

    def export_images(self):
        image_obj = self.session.env['nuvemshop.product.image']

        for index, product in enumerate(self.erp_record.image_ids):
            image_ext_id = image_obj.search([
                ('backend_id', '=', self.backend_record.id),
                ('openerp_id', '=', product.id),
            ])
            if not image_ext_id:
                image_ext_id = image_obj.with_context(
                    connector_no_export=True).create({
                    'backend_id': self.backend_record.id,
                    'openerp_id': product.id,
                    'nuvemshop_product_id': self.binding_id,
                })
            export_record.delay(
                self.session,
                'nuvemshop.product.image',
                image_ext_id.id, priority=50,
                eta=timedelta(seconds=10 + (index * 2))
            )

    def export_variants(self):
        variant_obj = self.session.env['nuvemshop.product.product']

        for index, product in enumerate(self.erp_record.product_variant_ids):
            variant_ext_id = variant_obj.search([
                ('backend_id', '=', self.backend_record.id),
                ('openerp_id', '=', product.id),
            ])
            if not variant_ext_id:
                variant_ext_id = variant_obj.with_context(
                    connector_no_export=True).create({
                    'backend_id': self.backend_record.id,
                    'openerp_id': product.id,
                    'main_template_id': self.binding_id,
                })
            export_record.delay(
                self.session,
                'nuvemshop.product.product',
                variant_ext_id.id, priority=70,
                eta=timedelta(seconds=10 + (index * 2))
            )


@nuvemshop
class ProductTemplateExportMapper(TranslationNuvemshopExportMapper):
    _model_name = 'nuvemshop.product.template'
    direct = [
        ('name', 'name'),
        # ('handle', 'handle'),
        ('published', 'published'),
        ('free_shipping', 'free_shipping'),
        # ('canonical_url', 'canonical_url'),
        ('seo_title', 'seo_title'),
        ('seo_description', 'seo_description'),
        ('brand', 'brand'),
        ('published', 'published'),
        # ('variants', 'variants'),
        # ('tags', 'tags'),
        # ('images', 'images'),
        # ('categories', 'categories'),
        #TODO campo tags
    ]

    @mapping
    def attributes(self, record):
        attributes = []
        if record.attribute_line_ids:
            for attribute in record.attribute_line_ids:
                attributes.append(
                    {
                        "pt": attribute.display_name
                    }
                )
            return {
                'attributes': attributes
            }

    @mapping
    def description(self, record):
        if record.description_html:
            return {'description': record.description_html}
        elif record.description:
            return{'description': record.description}
        else:
            return{'description': ' '}

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

    _translatable_fields = {
        'nuvemshop.product.template': [
            'name',
            'description',
            'handle',
            'seo_title',
            'seo_description',
            # 'attributes',
        ],
    }

    @mapping
    def translatable_fields(self, record):
        trans = TranslationNuvemshopExporter(self.environment)
        return self.convert_languages(
            trans.get_record_by_lang(record.id), self._translatable_fields[self._model_name])
