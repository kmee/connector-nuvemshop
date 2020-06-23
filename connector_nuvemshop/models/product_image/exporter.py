# -*- coding: utf-8 -*-
# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ...unit.exporter import delay_export, delay_export_all_bindings
from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.exception import MappingError, RetryableJobError

from openerp.addons.connector.unit.mapper import (
    mapping,
    changed_by,
    only_create,
    ExportMapper
)

from ...unit.backend_adapter import GenericAdapter
from ...unit.mapper import NuvemshopExportMapper
from ...unit.exporter import NuvemshopExporter
from ...backend import nuvemshop

IMAGE_EXPORT_FIELDS = [
    'sequence',
    'position',
    'url',
    'owner_id',
    'name',
    'product_id',
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

    def _create(self, data):
        """ Create the Nuvemshop record """
        nuvemshop_record = self.backend_adapter.create(data)
        return nuvemshop_record.get('id', 0)

    def _update(self, data):
        """ Update an Nuvemshop record """
        assert self.nuvemshop_id
        return self.backend_adapter.write(self.nuvemshop_id, data)

    def _link_image_to_url(self):
        """Change image storage to a url linked to product nuvemshop image"""
        try:
            data = {
                'product_id': self.erp_record.nuvemshop_product_id.nuvemshop_id,
                'id': self.nuvemshop_id
            }
            nuvemshop_record = self.backend_adapter.read(data)
            full_public_url = nuvemshop_record.get('src')
            if full_public_url and self.erp_record.url != full_public_url:
                self.erp_record.with_context(connector_no_export=True).write({
                    'url': full_public_url,
                    'file_db_store': False,
                    'storage': 'url',
                })
        except:
            raise

    def _after_export(self):
        self._link_image_to_url()


@nuvemshop
class ProductImageExportMapper(NuvemshopExportMapper):
    _model_name = 'nuvemshop.product.image'
    direct = []

    @only_create
    @mapping
    def src(self, record):
        if record.url:
            return {
                'src': record.url
            }

    @changed_by('url')
    @mapping
    def src(self, record):
        if record.url:
            return {
                'src': record.url
            }

    @mapping
    def position(self, record):
        if record.position:
            return {
                'position': record.position
            }

    @mapping
    def product_id(self, record):
        if record.nuvemshop_product_id:
            return {
                'product_id': record.nuvemshop_product_id.nuvemshop_id
            }
