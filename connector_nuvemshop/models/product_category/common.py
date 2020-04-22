# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, models, fields
from ...unit.backend_adapter import GenericAdapter
from ...backend import nuvemshop

_logger = logging.getLogger(__name__)

class ProductCategory(models.Model):
    _inherit = 'product.category'

    nuvemshop_bind_ids = fields.One2many(
        comodel_name='nuvemshop.product.category',
        inverse_name='openerp_id',
        string="Nuvemshop Bindings",
    )

class NuvemshopProductCategory(models.Model):
    _name = 'nuvemshop.product.category'
    _inherit = ['nuvemshop.binding', 'nuvemshop.handle.abstract']
    _inherits = {'product.category': 'openerp_id'}
    _description = 'nuvemshop product category'
    _rec_name = 'name'

    openerp_id = fields.Many2one(comodel_name='product.category',
                                 string='category',
                                 required=True,
                                 ondelete='cascade')

    nuvemshop_parent_id = fields.Many2one(
        comodel_name='nuvemshop.product.category',
        string='Nuvemshop Parent Category',
        ondelete='cascade',)

    description = fields.Char('Description', translate=True)
    seo_title = fields.Char('SEO Title', translate=True)
    seo_description = fields.Char('SEO Description', translate=True)

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.handle = self._handle_name(self.name)


@nuvemshop
class CategoryAdapter(GenericAdapter):
    _model_name = 'nuvemshop.product.category'
    _nuvemshop_model = 'categories'

