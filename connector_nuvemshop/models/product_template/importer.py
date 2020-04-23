# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)

from ..product_image.importer import import_product_image
from ...unit.importer import TranslatableRecordImporter
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
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
    ]

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

    def _after_import(self, binding):
        super(ProductTemplateImportMapper, self)._after_import(binding)
        self.import_images(binding)

    def import_images(self, binding):
        nuvemshop_record = self._get_nuvemshop_data()
        images = nuvemshop_record.get('images', {})
        for image in images:
            if image.get('id'):
                import_product_image.delay(
                    self.session,
                    'nuvemshop.product.image',
                    self.backend_record.id,
                    nuvemshop_record['id'],
                    image['id'],
                    priority=10,
                )

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
        ],
    }


    # def _is_uptodate(self, binding):
    #     """ NuvemShop Category do not update update and create dates =/ """
    #     return False
