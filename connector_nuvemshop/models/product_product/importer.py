# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from dateutil.parser.isoparser import isoparse

from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)
from openerp import fields

from ...unit.importer import TranslatableRecordImporter, normalize_datetime
from ...backend import nuvemshop


@nuvemshop
class ProductProductImportMapper(ImportMapper):
    _model_name = 'nuvemshop.product.product'

    direct = [
        ('position', 'position'),
        ('price', 'list_price'),
        ('promotional_price', 'promotional_price'),
        ('stock_management', 'stock_management'),
        ('weight', 'weight'),
        ('width', 'width'),
        ('height', 'height'),
        ('depth', 'depth'),
        ('sku', 'default_code'),
        ('barcode', 'ean13'),
        (normalize_datetime('created_at'), 'created_at'),
        (normalize_datetime('updated_at'), 'updated_at'),
    ]

    @mapping
    def company_id(self, record):
        return {'company_id': False}

    @mapping
    def nuvemshop_image_id(self, record):
        if record['image_id']:
            image_binder = self.binder_for('nuvemshop.product.image')
            image_record = image_binder.to_openerp(record['image_id'])
            return {'nuvemshop_image_id': image_record.id}

    @mapping
    def product_type(self, record):
        return {'type': 'product'}

    @mapping
    def values(self, record):
        if record['values']:
            pav = self.env['product.attribute.value']
            values = []
            template = self.binder_for('nuvemshop.product.template').to_openerp(
                record['product_id'], unwrap=True)
            for idx, value in enumerate(record['values']):
                value_id = pav.search([
                    ('name', '=', value.get('pt')),
                    ('attribute_id', '=',
                     template.attribute_line_ids[idx].attribute_id.id
                     )
                ])
                values.append(value_id.id)
            return {'attribute_value_ids': [(6,0, values)]}

    @mapping
    def product_tmpl_id(self, record):
        if record['product_id']:
            product_id = self.binder_for(
                'nuvemshop.product.template').to_openerp(
                record['product_id'], unwrap=True).id
            return {'product_tmpl_id': product_id}

    @mapping
    def main_template_id(self, record):
        if record['product_id']:
            product_id = self.binder_for(
                'nuvemshop.product.template').to_openerp(
                record['product_id'])
            return {'main_template_id': product_id.id}

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
        binding.openerp_id.import_variant_image_nuvemshop()

    def _get_nuvemshop_data(self):
        """ Return the raw Nuvemshop data for ``self.nuvemshop_id`` """
        return self.backend_adapter.read(dict(product_id=self.template_id,
                                              id=self.variant_id))

    def run(self, nuvemshop_id, **kwargs):
        self.template_id = nuvemshop_id['product_id']
        self.variant_id = nuvemshop_id['id']

        super(ProductProductImporter, self).run(self.variant_id, **kwargs)
