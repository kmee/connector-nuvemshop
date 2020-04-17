# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openerp.addons.connector.queue.job import job
from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper
                                                  )
from ...unit.import_synchronizer import (DelayedBatchImporter, NuvemshopImporter)
from ...connector import get_environment
from ...backend import nuvemshop

_logger = logging.getLogger(__name__)


@nuvemshop
class ProductCategoryImportMapper(ImportMapper):
    _model_name = 'nuvemshop.product.category'

    @mapping
    def name(self, record):
        if record['name']:
            return {'name': record['name']['pt']}

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
        return {'parent_id': category_id, 'nuvemshop_parent_id': nuvemshop_cat_id}


@nuvemshop
class CategoryBatchImporter(DelayedBatchImporter):

    _model_name = ['nuvemshop.product.category']

    def _import_record(self, nuvemshop_id, priority=None):
        """ Delay a job for the import """

        super(CategoryBatchImporter, self)._import_record(
            nuvemshop_id, priority=priority)

    def run(self, filters=None):
        """ Category do not receive date paramerters =/
         Then lets sync everything!"""
        record_ids = self.backend_adapter.search()
        _logger.info('search for nuvemshop Product Category %s returned %s',
                     filters, record_ids)
        for record_id in record_ids:
            self._import_record(record_id['id'])


@nuvemshop
class ProductCategoryImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.product.category']
    _parent_field = 'parent'


@job(default_channel='root.nuvemshop')
def category_import_batch(session, model_name, backend_id, filters=None):
    """ Prepare the import of category modified on NuvemshopCommerce """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(CategoryBatchImporter)
    importer.run(filters=filters)
