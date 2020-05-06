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
        ('position', 'position'),
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
    ]

    @mapping
    def nuvemshop_product_id(self, record):
        if record['product_id']:
            nuvemshop_product_id = self.binder_for(
                'nuvemshop.product.template').to_openerp(
                record['product_id'])
            return {
                'nuvemshop_product_id': nuvemshop_product_id.id
            }

    @mapping
    def storage(self, record):
        return {'storage': 'url'}

    @mapping
    def owner_model(self, record):
        return {'owner_model': 'product.template'}

    @mapping
    def sequence(self, record):
        return {'sequence': record.get('position')}

    @mapping
    def owner_id(self, record):
        if record['product_id']:
            product_id = self.binder_for(
                'nuvemshop.product.template').to_openerp(
                record['product_id'], unwrap=True)

            return {'owner_id': product_id.id}

    @mapping
    def name(self, record):
        if record['src']:
            url = record['src'].replace('\\', '')
            return {'name': str(url)}

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

    def _get_nuvemshop_data(self):
        """ Return the raw PrestaShop data for ``self.nuvemshop_id`` """
        return self.backend_adapter.read(dict(product_id=self.template_id,
                                              id=self.image_id))

    def run(self, nuvemshop_id, **kwargs):
        self.template_id = nuvemshop_id['product_id']
        self.image_id = nuvemshop_id['id']

        super(ProductImageImporter, self).run(self.image_id, **kwargs)
