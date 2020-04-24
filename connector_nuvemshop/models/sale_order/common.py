# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, models, fields
from ...unit.backend_adapter import GenericAdapter
from ...backend import nuvemshop

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    nuvemshop_bind_ids = fields.One2many(
        comodel_name='nuvemshop.sale.order',
        inverse_name='openerp_id',
        string="Nuvemshop Bindings",
    )


class NuvemshopSaleOrder(models.Model):
    _name = 'nuvemshop.sale.order'
    _inherit = ['nuvemshop.binding', 'nuvemshop.handle.abstract']
    _inherits = {'sale.order': 'openerp_id'}
    _description = 'nuvemshop sale order'
    _rec_name = 'name'

    openerp_id = fields.Many2one(comodel_name='sale.order',
                                 string='category',
                                 required=True,
                                 ondelete='cascade')
    token = fields.Char()
    store_id = fields.Char()
    shipping_min_days = fields.Integer()
    shipping_max_days = fields.Integer()
    shipping_cost_owner = fields.Float()
    discount_coupon = fields.Float()
    discount_gateway = fields.Float()


@nuvemshop
class CategoryAdapter(GenericAdapter):
    _model_name = 'nuvemshop.sale.order'
    _nuvemshop_model = 'orders'

