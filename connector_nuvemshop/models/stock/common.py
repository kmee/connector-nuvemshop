# -*- coding: utf-8 -*-
# Copyright (C) 2020  Daniel Sadamo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, models, fields
from ...unit.backend_adapter import GenericAdapter
from ...backend import nuvemshop

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shipping_tracking_url = fields.Char(
        string="Shipping Track URL"
    )
    nuvemshop_order_id = fields.Many2one(
        comodel_name='nuvemshop.sale.order',
        string='Nuvemshop Sale Order',
        ondelete='set null'
    )
