# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import xmlrpclib
from urlparse import urljoin

from openerp import models, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.mapper import (mapping,
                                                  ImportMapper
                                                  )
from openerp.addons.connector.exception import IDMissingInBackend
from ..unit.backend_adapter import (GenericAdapter)
from ..unit.import_synchronizer import (DelayedBatchImporter, NuvemshopImporter)
from ..connector import get_environment
from ..backend import nuvemshop

_logger = logging.getLogger(__name__)


class NuvemshopProductCategory(models.Model):
    _name = 'nuvemshop.product.category'
    _inherit = 'nuvemshop.binding'
    _inherits = {'product.category': 'openerp_id'}
    _description = 'nuvemshop product category'

    _rec_name = 'name'

    openerp_id = fields.Many2one(comodel_name='product.category',
                                 string='category',
                                 required=True,
                                 ondelete='cascade')
    backend_id = fields.Many2one(
        comodel_name='nuvemshop.backend',
        string='Nuvemshop Backend',
        store=True,
        readonly=False,
    )

    slug = fields.Char('Slung Name')
    nuvemshop_parent_id = fields.Many2one(
        comodel_name='nuvemshop.product.category',
        string='Nuvemshop Parent Category',
        ondelete='cascade',)
    description = fields.Char('Description')
    count = fields.Integer('count')


@nuvemshop
class CategoryAdapter(GenericAdapter):
    _model_name = 'nuvemshop.product.category'
    _nuvemshop_model = 'categories'


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

    """ Import the NuvemshopCommerce Partners.

    For every partner in the list, a delayed job is created.
    """
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
