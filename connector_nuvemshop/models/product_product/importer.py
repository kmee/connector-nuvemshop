# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)

from ...unit.importer import TranslatableRecordImporter
from ...backend import nuvemshop


@nuvemshop
class ProductProductImportMapper(ImportMapper):
    _model_name = 'nuvemshop.product.product'

    direct = [
        ('image_id', 'image_id'),
        #('product_id', 'product_id'),
        ('position', 'position'),
        ('price', 'list_price'),
        ('promotional_price', 'promotional_price'),
        ('stock_management', 'stock_management'),
        ('weight', 'weight'),
        ('width', 'width'),
        ('height', 'height'),
        ('depth', 'depth'),
        ('sku', 'default_code'),
        ('values', 'values'),
        ('barcode', 'ean13'),
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
    ]

    @mapping
    def product_tmpl_id(self, record):
        if record['product_id']:
            product_id = self.binder_for(
                'nuvemshop.product.template').to_openerp(
                record['product_id'], unwrap=True).id
            return {'product_tmpl_id': product_id}

    @mapping
    def cost_method(self, record):
        return {
            'cost_method': self.env['product.template'].fields_get(
                allfields=['cost_method'])['cost_method']['selection'][0][0]
        }

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@nuvemshop
class ProductProductImporter(TranslatableRecordImporter):
    _model_name = ['nuvemshop.product.product']
    # _parent_field = 'parent' # não tenho certeza que precisa
    _translatable_fields = {
        'nuvemshop.product.product': [
            'values',
        ],
    }

    def _after_import(self, binding):
        super(ProductProductImporter, self)._after_import(binding)
        # binding.openerp_id.import_image_nuvemshop()


    # def _is_uptodate(self, binding):
    #     """ NuvemShop Category do not update update and create dates =/ """
    #     return False
