# -*- coding: utf-8 -*-
# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import ExportSynchronizer
from openerp.addons.connector.unit.mapper import (
    mapping,
    ExportMapper
)

from ...backend import nuvemshop
from ...connector import get_environment
from ...unit.backend_adapter import GenericAdapter
from ...unit.mapper import NuvemshopExportMapper
from ...unit.exporter import (
    NuvemshopExporter,
    delay_export_all_bindings,
    delay_export,
    export_record
)

VARIANT_EXPORT_FIELDS = [
    'nuvemshop_image_id',
    'position',
    'list_price',
    'promotional_price',
    'stock_management',
    'weight',
    'width',
    'height',
    'depth',
    'default_code',
    'ean13',
    # 'name',
    'attribute_value_ids',
]

# TODO: - Corrigir exportaçao de value (atributo da variante)
#       - Sincronizaçao ao criar novo atributo ou nova variante no odoo


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
        delay_export_all_bindings(session, model_name, record_id)


@on_record_write(model_names='nuvemshop.product.product')
def nuvemshop_product_product_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(VARIANT_EXPORT_FIELDS):
        delay_export(session, model_name, record_id)

    model = session.env[model_name]
    record = model.browse(record_id)
    if not record.is_product_variant:
        return
    NO_UPDATE_FIELDS = [
        'created_at',
        'updated_at',
        'stock',
    ]
    if fields and not any([field in fields for field in NO_UPDATE_FIELDS]):
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
                    session, 'nuvemshop.product.template', binding.id
                )


@nuvemshop
class ProductProductExporter(NuvemshopExporter):
    _model_name = ['nuvemshop.product.product']

    def _create(self, data):
        """ Create the Nuvemshop record """
        nuvemshop_record = self.backend_adapter.create(data)
        return nuvemshop_record

    def _update(self, data):
        """ Update an Nuvemshop record """
        assert self.nuvemshop_id
        return self.backend_adapter.write(self.nuvemshop_id, data)


@nuvemshop
class ProductProductExportMapper(NuvemshopExportMapper):
    _model_name = 'nuvemshop.product.product'
    direct = [
        ('position', 'position'),
        ('list_price', 'price'),
        ('promotional_price', 'promotional_price'),
        ('weight', 'weight'),
        ('width', 'width'),
        ('height', 'height'),
        ('depth', 'depth'),
        ('default_code', 'sku'),
        ('ean13', 'barcode'),
    ]

    @mapping
    def image_id(self, record):
        if record.nuvemshop_image_id:
            return {
                'image_id': record.nuvemshop_image_id.nuvemshop_id
            }

    @mapping
    def stock_management(self, record):
        if record['stock_management']:
            return {
                'stock_management': record['stock_management']
            }

    @mapping
    def product_id(self, record):
        if record['main_template_id']:
            return {
                'product_id': record.main_template_id.nuvemshop_id
            }

    @mapping
    def values(self, record):
        if record['attribute_value_ids']:
            return {
                'values': [
                    dict(pt=val.name) for val in record['attribute_value_ids']
                ]
            }


@nuvemshop
class ProductInventoryExporter(ExportSynchronizer):
    _model_name = ['nuvemshop.product.product']

    def run(self, binding_id, fields):
        """ Export the product inventory to Nuvemshop """
        variant = self.env[self.model._name].browse(binding_id)
        adapter = self.unit_for(GenericAdapter, 'nuvemshop.product.product')
        binder = self.binder_for()
        nuvemshop_id = binder.to_backend(variant.id)
        template_id = variant.main_template_id.nuvemshop_id
        adapter.export_quantity(template_id, nuvemshop_id, variant.stock)


@job(default_channel='root.nuvemshop')
def export_inventory(session, model_name, record_id, fields=None):
    """ Export the inventory configuration and quantity of a product. """
    product = session.env[model_name].browse(record_id)
    backend_id = product.backend_id.id
    env = get_environment(session, model_name, backend_id)
    inventory_exporter = env.get_connector_unit(ProductInventoryExporter)
    return inventory_exporter.run(record_id, fields)


@job(default_channel='root.nuvemshop')
def export_product_quantities(session, ids):
    model_obj = session.env['nuvemshop.product.product']
    model_obj.search([
        ('backend_id', 'in', [ids]),
    ]).recompute_nuvemshop_qty()
