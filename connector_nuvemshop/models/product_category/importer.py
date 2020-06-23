# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)

from ...unit.importer import TranslatableRecordImporter, normalize_datetime
from ...backend import nuvemshop


@nuvemshop
class ProductCategoryImportMapper(ImportMapper):
    _model_name = 'nuvemshop.product.category'

    direct = [
        ('description', 'description'),
        ('handle', 'handle'),
        ('seo_title', 'seo_title'),
        ('seo_description', 'seo_description'),
        (normalize_datetime('created_at'), 'created_at'),
        (normalize_datetime('updated_at'), 'updated_at'),
    ]

    @mapping
    def name(self, record):
        if record['name']:
            return {'name': record['name']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def parent_id(self, record):
        if not record['parent']:
            return
        binder = self.binder_for()
        category_id = binder.to_openerp(record['parent'], unwrap=True)
        nuvemshop_cat_id = binder.to_openerp(record['parent'])
        if category_id is None:
            raise MappingError("The product category with "
                               "nuvemshop id %s is not imported." %
                               record['parent'])
        return {'parent_id': category_id.id, 'nuvemshop_parent_id': nuvemshop_cat_id.id}


@nuvemshop
class ProductCategoryImporter(TranslatableRecordImporter):
    _model_name = ['nuvemshop.product.category']
    _parent_field = 'parent' # não tenho certeza que precisa
    _translatable_fields = {
        'nuvemshop.product.category': [
            'name',
            'description',
            'handle',
            'seo_title',
            'seo_description',
        ],
    }


    def _is_uptodate(self, binding):
        """ NuvemShop Category do not update update and create dates =/ """
        return False
