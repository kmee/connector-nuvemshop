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
            return {'url': record['src'].replace('\\', '')}


@nuvemshop
class ProductImageImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.product.image']

    def _get_nuvemshop_data(self):
        """ Return the raw PrestaShop data for ``self.nuvemshop_id`` """
        return self.backend_adapter.read(self.template_id, self.image_id)

    def run(self, template_id, image_id):
        self.template_id = template_id
        self.image_id = image_id

        try:
            super(ProductImageImporter, self).run(image_id)
        except Exception:
            pass


@job(default_channel='root.nuvemshop')
def import_product_image(session, model_name, backend_id, product_tmpl_id,
                         image_id):
    """Import a product image"""
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(NuvemshopImporter)
    importer.run(product_tmpl_id, image_id)
