# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)

from ...unit.importer import NuvemshopImporter
from ...backend import nuvemshop
from ...connector import get_environment


@nuvemshop
class ProductImageImportMapper(ImportMapper):
    _model_name = 'nuvemshop.product.image'

    direct = [
        ('name', 'position'),
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
    ]

    @mapping
    def storage(self, record):
        return {'storage': 'url'}

    @mapping
    def owner_model(self, record):
        return {'owner_model': 'product.template'}

    @mapping
    def owner_id(self, record):
        if record['product_id']:
            product_id = self.binder_for(
                'nuvemshop.product.template').to_openerp(
                record['product_id'], unwrap=True).id
            return {'owner_id': product_id}

    @mapping
    def url(self, record):
        if record['src']:
            url = record['src'].replace('\\', '')
            return {'url': str(url)}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@nuvemshop
class ProductImageImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.product.image']

    # def _get_nuvemshop_data(self):
    #     """ Return the raw PrestaShop data for ``self.nuvemshop_id`` """
    #     return self.backend_adapter.read(self.template_id, self.image_id)

    # def run(self, product_tmpl_id):
    #     binder = self.binder_for('nuvemshop.product.template')
    #
    #     self.to_openerp(product_tmpl_id)
    #     # to_backend
    #     self.template_id = product_tmpl_id
    #     self.image_id = image_id
    #
    #     try:
    #         super(ProductImageImporter, self).run(image_id)
    #     except Exception, e:
    #         raise (e)

#
# @job(default_channel='root.nuvemshop')
# def import_product_image(session, model_name, backend_id, product_tmpl_id):
#     """Import a product image"""
#     env = get_environment(session, model_name, backend_id)
#     importer = env.get_connector_unit(ProductImageImporter)
#     importer.run(product_tmpl_id)
