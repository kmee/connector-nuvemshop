# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from dateutil.parser.isoparser import isoparse

from openerp import fields
from openerp.addons.connector.exception import MappingError, RetryableJobError
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)

from ..product_category.importer import ProductCategoryImporter
from ...unit.importer import TranslatableRecordImporter, normalize_datetime
from ...backend import nuvemshop


@nuvemshop
class ProductTemplateImportMapper(ImportMapper):
    _model_name = 'nuvemshop.product.template'

    direct = [
        ('handle', 'handle'),
        ('published', 'published'),
        ('free_shipping', 'free_shipping'),
        ('canonical_url', 'canonical_url'),
        ('brand', 'brand'),
        ('seo_title', 'seo_title'),
        ('seo_description', 'seo_description'),
        (normalize_datetime('created_at'), 'created_at'),
        (normalize_datetime('updated_at'), 'updated_at'),
    ]

    @mapping
    def company_id(self, record):
        return {'company_id': False}

    @mapping
    def attributes(self, record):
        attributes = [(5, 0, 0)]
        prod_attrib = self.env['product.attribute']
        prod_attrib_v = self.env['product.attribute.value']
        if record.get('attributes') and record.get('variants'):
            for idx, attribute in enumerate(record.get('attributes')):
                record_line = {
                    "attribute_id": False,
                    "value_ids": [(6,0,[])]
                }
                attrib = prod_attrib.search([('name', '=', attribute.get('pt'))])
                if attrib:
                    record_line.update({'attribute_id': attrib.id})
                else:
                    new_attr = prod_attrib.create({'name': attribute.get('pt')})
                    record_line.update({'attribute_id': new_attr.id})

                for variant in record.get('variants'):
                    if not variant.get('values'):
                        continue
                    attrib = record_line.get('attribute_id')
                    value = prod_attrib_v.search([
                        ('name', '=', variant.get('values')[idx].get('pt')),
                        ('attribute_id', '=', attrib),
                    ])
                    if value:
                        record_line.get('value_ids')[0][2].append(value.id)
                    else:
                        new_value = prod_attrib_v.create({
                            'name': variant.get('values')[idx].get('pt'),
                            'attribute_id': record_line.get('attribute_id')
                        })
                        record_line.get('value_ids')[0][2].append(new_value.id)

                attributes.append((0,0, record_line))

            return {'attribute_line_ids': [(5, 0, 0)] + attributes}


    @mapping
    def product_type(self, record):
        return {'type': 'product'}

    @mapping
    def categ_ids(self, record):
        categories = record.get('categories', {})
        product_categories = []
        for category in categories:
            category_id = self.binder_for(
                'nuvemshop.product.category').to_openerp(
                category['id'], unwrap=True).id
            if not category_id:
                raise RetryableJobError(
                    'Product Category not imported yet. The job will be retried later',
                    seconds=15,
                    ignore_retry=False
                )
            product_categories.append(category_id)

        return {'categ_ids': [(6, 0, product_categories)]}

    @mapping
    def description_html(self, record):
        if record['description']:
            return {'description_html': record['description']}

    @mapping
    def name(self, record):
        if record['name']:
            return {'name': record['name']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def update_ctx(self, record):
        ctx = dict(self.env.context)
        ctx.update({'create_product_product': True})
        self.env.context = ctx

    # @mapping
    # def parent_id(self, record):
    #     if not record['parent']:
    #         return
    #     binder = self.binder_for()
    #     category_id = binder.to_openerp(record['parent'], unwrap=True)
    #     nuvemshop_cat_id = binder.to_openerp(record['parent'])
    #     if category_id is None:
    #         raise MappingError("The product category with "
    #                            "nuvemshop id %s is not imported." %
    #                            record['parent'])
    #     return {'parent_id': category_id.id, 'nuvemshop_parent_id': nuvemshop_cat_id.id}


@nuvemshop
class ProductTemplateImporter(TranslatableRecordImporter):
    _model_name = ['nuvemshop.product.template']
    _parent_field = 'parent' # não tenho certeza que precisa
    _translatable_fields = {
        'nuvemshop.product.template': [
            'name',
            'description',
            'handle',
            'seo_title',
            'seo_description',
            'attributes'
        ],
    }

    def _import_dependencies(self):
        record = self.nuvemshop_record
        for category in record.get('categories'):
            self._import_dependency(
                category.get('id'),
                'nuvemshop.product.category',
                ProductCategoryImporter,
            )


    def _after_import(self, binding):
        super(ProductTemplateImporter, self)._after_import(binding)
        binding.openerp_id.import_image_nuvemshop()
        binding.openerp_id.import_variant_nuvemshop()


    # def _is_uptodate(self, binding):
    #     """ NuvemShop Category do not update update and create dates =/ """
    #     return False
