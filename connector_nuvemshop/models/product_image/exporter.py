# -*- coding: utf-8 -*-
# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ...unit.exporter import delay_export, delay_export_all_bindings
from openerp.addons.connector.event import on_record_create, on_record_write

from openerp.addons.connector.unit.mapper import (
    mapping,
    ExportMapper
)

from ...unit.mapper import NuvemshopExportMapper
from ...unit.exporter import NuvemshopExporter
from ...backend import nuvemshop


IMAGE_EXPORT_FIELDS = [
    'sequence',
    'url',
    'owner_id',
    'name',
]

@on_record_create(model_names='nuvemshop.product.image')
def nuvemshop_product_image_create(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    delay_export(session, model_name, record_id, priority=20)


@on_record_write(model_names='base_multi_image.image')
def product_image_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(IMAGE_EXPORT_FIELDS):
        delay_export_all_bindings(session, model_name, record_id, fields)


@on_record_write(model_names='nuvemshop.product.image')
def nuvemshop_product_image_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if set(fields.keys()) <= set(IMAGE_EXPORT_FIELDS):
        delay_export(session, model_name, record_id, fields)


@nuvemshop
class ProductImageExporter(NuvemshopExporter):
    _model_name = ['nuvemshop.product.image']


@nuvemshop
class ProductImageExportMapper(NuvemshopExportMapper):
    _model_name = 'nuvemshop.product.image'
    direct = [
        ('url', 'src'),
        ('sequence', 'position'),
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
    ]

    @mapping
    def product_id(self, record):
        if record['owner_id']:
            product_id = self.binder_for(
                'nuvemshop.product.template').to_backend(
                record['owner_id'], wrap=True)
            return {'product_id': product_id}
