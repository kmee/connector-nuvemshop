# -*- coding: utf-8 -*-
# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ...unit.exporter import delay_export, export_record
from openerp.addons.connector.event import on_record_create, on_record_write

from openerp.addons.connector.unit.mapper import (
    mapping,
    ExportMapper
)

from ...unit.mapper import NuvemshopExportMapper
from ...unit.exporter import (
    NuvemshopExporter,
    delay_export_all_bindings
)
from ...backend import nuvemshop


VARIANT_EXPORT_FIELDS = [
    'image_id',
    'position',
    'list_price',
    'promotional_price',
    'stock_management',
    'stock',
    'weight',
    'width',
    'height',
    'depth',
    'default_code',
    'ean13',
    # 'name',
    'attribute_value_ids',
]


# def delay_export_all_bindings(
#         session, model_name, record_id, fields=None, priority=20):
#     """ Delay a job which export all the bindings of a record.
#
#     In this case, it is called on records of normal models and will delay
#     the export for all the bindings.
#     """
#     if session.context.get('connector_no_export'):
#         return
#     model = session.env[model_name]
#     record = model.browse(record_id)
#     for binding in record.nuvemshop_variants_bind_ids:
#         export_record.delay(session, binding._model._name, binding.id,
#                             fields=fields, priority=priority)

@on_record_create(model_names='nuvemshop.product.product')
def nuvemshop_product_product_create(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    delay_export(session, model_name, record_id, priority=20)


@on_record_write(model_names='product.product')
def product_product_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(VARIANT_EXPORT_FIELDS):
        delay_export_all_bindings(session, model_name, record_id, fields)


@on_record_write(model_names='nuvemshop.product.product')
def nuvemshop_product_product_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(VARIANT_EXPORT_FIELDS):
        delay_export(session, model_name, record_id, fields)

    model = session.env[model_name]
    record = model.browse(record_id)
    if not record.is_product_variant:
        return

    if fields:
        # If user modify any variant we delay template export but before
        # check if the template have a queued job
        template = record.mapped('main_template_id')
        for binding in template.nuvemshop_bind_ids:
            # check if there is other queued job
            func = "openerp.addons.connector_nuvemshop.unit.exporter." \
                   "export_record('nuvemshop.product.template', %s," \
                   % binding.id
            jobs = session.env['queue.job'].sudo().search(
                [('func_string', 'like', "%s%%" % func),
                 ('state', '!=', 'done')]
            )
            if not jobs:
                export_record.delay(
                    session, 'nuvemshop.product.template', binding.id, fields
                )


@nuvemshop
class ProductProductExporter(NuvemshopExporter):
    _model_name = ['nuvemshop.product.product']


@nuvemshop
class ProductProductExportMapper(NuvemshopExportMapper):
    _model_name = 'nuvemshop.product.product'
    direct = [
        ('image_id', 'image_id'),
        ('position', 'position'),
        ('list_price', 'price'),
        ('promotional_price', 'promotional_price'),
        ('weight', 'weight'),
        ('width', 'width'),
        ('height', 'height'),
        ('depth', 'depth'),
        ('default_code', 'sku'),
        ('ean13', 'barcode'),
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
    ]

    @mapping
    def stock_management(self, record):
        if record['stock_management']:
            return {'stock_management': record['stock_management']}

    @mapping
    def product_id(self, record):
        if record['main_template_id']:
            return {'product_id': record.main_template_id.nuvemshop_id}

    @mapping
    def values(self, record):
        if record['attribute_value_ids']:
            return {'values': [
                dict(pt=val.name) for val in record['attribute_value_ids']]}
