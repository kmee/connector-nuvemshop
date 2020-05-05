# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)
from openerp.addons.connector.unit.backend_adapter import BackendAdapter

from ...unit.importer import TranslatableRecordImporter, NuvemshopImporter
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
        # ('values', 'values'),
        ('barcode', 'ean13'),
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
    ]

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

    # def _import_dependencies(self):
    #     record = self.nuvemshop_record
    #     option_values = record.get('values')
    #     if not isinstance(option_values, list):
    #         option_values = [option_values]
    #     backend_adapter = self.unit_for(
    #         BackendAdapter, 'nuvemshop.product.attribute.value')
    #     for option_value in option_values:
    #         option_value = backend_adapter.read(option_value['id'])
    #         self._import_dependency(
    #             option_value['id_attribute_group'],
    #             'nuvemshop.product.attribute',
    #         )
    #         self._import_dependency(
    #             option_value['id'],
    #             'nuvemshop.product.attribute.value'
    #         )


    # def _is_uptodate(self, binding):
    #     """ NuvemShop Category do not update update and create dates =/ """
    #     return False


# @nuvemshop
# class ProductAttributeRecordImport(TranslatableRecordImporter):
#     _model_name = 'nuvemshop.product.attribute'
#
#     def _import_values(self):
#         record = self.nuvemshop_record
#         option_values = record.get('name')
#         if not isinstance(option_values, list):
#             option_values = [option_values]
#         for option_value in option_values:
#             self._import_dependency(
#                 option_value['id'],
#                 'nuvemshop.product.attribute.value'
#             )
#
#     def run(self, ext_id):
#         # looking for an product.attribute with the same name
#         self.nuvemshop_id = ext_id
#         self.nuvemshop_record = self._get_nuvemshop_data()
#         name = self.mapper.name(self.nuvemshop_record)['name']
#         attribute_ids = self.env['product.attribute'].search([
#             ('name', '=', name),
#         ])
#         if len(attribute_ids) == 0:
#             # if we don't find it, we create a nuvemshop_product_combination
#             super(ProductAttributeRecordImport, self).run(ext_id)
#         else:
#             # else, we create only a nuvemshop.product.attribute
#             data = {
#                 'openerp_id': attribute_ids.id,
#                 'backend_id': self.backend_record.id,
#             }
#             erp_id = self.model.with_context(
#                 connector_no_export=True).create(data)
#             self.binder.bind(self.nuvemshop_id, erp_id.id)
#         self._import_values()
#
#
# @nuvemshop
# class ProductAttributeMapper(ImportMapper):
#     _model_name = 'nuvemshop.product.attribute'
#
#     direct = []
#
#     @mapping
#     def backend_id(self, record):
#         return {'backend_id': self.backend_record.id}
#
#     @mapping
#     def name(self, record):
#         name = None
#         if 'language' in record['name']:
#             language_binder = self.binder_for('nuvemshop.res.lang')
#             languages = record['name']['language']
#             if not isinstance(languages, list):
#                 languages = [languages]
#             for lang in languages:
#                 erp_language = language_binder.to_odoo(lang['attrs']['id'])
#                 if not erp_language:
#                     continue
#                 if erp_language.code == 'en_US':
#                     name = lang['value']
#                     break
#             if name is None:
#                 name = languages[0]['value']
#         else:
#             name = record['name']
#         return {'name': name}
#
#
#
# @nuvemshop
# class ProductAttributeValueRecordImport(TranslatableRecordImporter):
#     _model_name = 'nuvemshop.product.attribute.value'
#
#     _translatable_fields = {
#         'nuvemshop.product.attribute.value': ['values'],
#     }
#
#
# @nuvemshop
# class ProductAttributeValueMapper(ImportMapper):
#     _model_name = 'nuvemshop.product.attribute.value'
#
#     direct = [
#         ('values', 'name'),
#     ]
#
#     @mapping
#     def attribute_id(self, record):
#         binder = self.binder_for('nuvemshop.product.attribute')
#         attribute = binder.to_odoo(record['id_attribute_group'], unwrap=True)
#         return {'attribute_id': attribute.id}
#
#     @mapping
#     def backend_id(self, record):
#         return {'backend_id': self.backend_record.id}
