# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, models, fields
from ...unit.backend_adapter import GenericAdapter
from ...backend import nuvemshop

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    nuvemshop_bind_ids = fields.One2many(
        comodel_name='nuvemshop.res.partner',
        inverse_name='openerp_id',
        string="Nuvemshop Bindings",
    )

class NuvemshopResPartner(models.Model):
    _name = 'nuvemshop.res.partner'
    _inherit = ['nuvemshop.binding', 'nuvemshop.handle.abstract']
    _inherits = {'res.partner': 'openerp_id'}
    _description = 'nuvemshop res partner'
    _rec_name = 'name'

    openerp_id = fields.Many2one(comodel_name='res.partner',
                                 string='category',
                                 required=True,
                                 ondelete='cascade')

    total_spent = fields.Float()
    total_spent_currency = fields.Char()
    last_order_id = fields.Char()


@nuvemshop
class CategoryAdapter(GenericAdapter):
    _model_name = 'nuvemshop.res.partner'
    _nuvemshop_model = 'customers'
