# -*- coding: utf-8 -*-
# Copyright (C) 2020  Daniel Sadamo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, models, fields
from ..product_product.exporter import export_inventory
from openerp.addons.connector.session import ConnectorSession

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

    def do_transfer(self):
        # The key in the context avoid the event to be fired in
        # StockMove.action_done(). Allow to handle the partial pickings
        self_context = self.with_context(__no_adjust_stock=True)
        result = super(StockPicking, self_context).do_transfer()
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        for picking in self:
            if not picking.location_dest_id.nuvemshop_synchronized:
                continue

            products = picking.mapped(
                'move_lines.product_id')
            for prod in products:
                for binding in prod.nuvemshop_variants_bind_ids:
                    export_inventory.delay(
                        session,
                        'nuvemshop.product.product',
                        binding.id,
                        fields=['stock'],
                        priority=20
                    )

        return result
