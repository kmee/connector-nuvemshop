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

    nuvemshop_order_line_ids = fields.One2many(
        comodel_name='nuvemshop.sale.order.line',
        inverse_name='nuvemshop_order_id',
        string='Nuvemshop Order Lines',
    )

    token = fields.Char()
    store_id = fields.Char()
    shipping_min_days = fields.Integer()
    shipping_max_days = fields.Integer()
    billing_name = fields.Char()
    billing_phone = fields.Char()
    billing_address = fields.Char()
    billing_number = fields.Char()
    billing_floor = fields.Char()
    billing_locality = fields.Char()
    billing_zipcode = fields.Char()
    billing_city = fields.Char()
    billing_province = fields.Char()
    billing_country = fields.Char()
    shipping_cost_owner = fields.Float()
    subtotal = fields.Float()
    discount = fields.Float()
    discount_coupon = fields.Float()
    discount_gateway = fields.Float()
    total = fields.Float()
    total_usd = fields.Float()
    weight = fields.Float()
    currency = fields.Char()
    language = fields.Char()
    gateway = fields.Char()
    gateway_id = fields.Char()
    shipping = fields.Char()
    shipping_option = fields.Char()
    shipping_option_code = fields.Char()
    shipping_option_reference = fields.Char()
    shipping_pickup_details = fields.Char()
    shipping_tracking_number = fields.Char()
    shipping_tracking_url = fields.Char()
    shipping_store_branch_name = fields.Char()
    shipping_pickup_type = fields.Char()
    storefront = fields.Char()
    note = fields.Char()
    next_action = fields.Char()
    cancel_reason = fields.Char()
    owner_note = fields.Char()
    cancelled_at = fields.Datetime()
    closed_at = fields.Datetime()
    read_at = fields.Datetime()
    status = fields.Selection(
        string="",
        selection=[
            ('open', 'Open'),
            ('closed', 'Closed'),
            ('canceled', 'Canceled'),
        ]
    )
    payment_status = fields.Selection(
        string="",
        selection=[
            ('authorized', 'Authorized'),
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('abandoned', 'Abandoned'),
            ('refunded', 'Refunded'),
            ('voided', 'Voided'),
        ]
    )
    shipping_status = fields.Selection(
        string="",
        selection=[
            ('unpacked', 'Unpacked'),
            ('shipped', 'Shipped'),
            ('unshipped', 'Unshipped'),
        ]
    )
    shipped_at = fields.Datetime()
    paid_at = fields.Datetime()
    landing_url = fields.Char()
    app_id = fields.Char()
    completed_at = fields.Datetime()
    payment_details_method = fields.Char()
    payment_details_credit_card_company = fields.Char()
    payment_details_installments = fields.Char()
    client_details_browser_ip = fields.Char()
    client_details_user_agent = fields.Char()


@nuvemshop
class SaleOrderAdapter(GenericAdapter):
    _model_name = 'nuvemshop.sale.order'
    _nuvemshop_model = 'orders'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    nuvemshop_bind_ids = fields.One2many(
        comodel_name='nuvemshop.sale.order.line',
        inverse_name='openerp_id',
        string="Nuvemshop Bindings",
    )


class NuvemshopSaleOrderLine(models.Model):
    _name = 'nuvemshop.sale.order.line'
    _inherit = ['nuvemshop.binding', 'nuvemshop.handle.abstract']
    _inherits = {'sale.order.line': 'openerp_id'}
    _description = 'nuvemshop sale order line'
    _rec_name = 'name'

    openerp_id = fields.Many2one(comodel_name='sale.order.line',
                                 string='Order line',
                                 required=True,
                                 ondelete='cascade')

    nuvemshop_order_id = fields.Many2one(
        comodel_name='nuvemshop.sale.order',
        string='Nuvemshop Order',
    )

    @api.model
    def create(self, vals):
        nuvemshop_sale_order = self.env['nuvemshop.sale.order'].search([
            ('id', '=', vals['nuvemshop_order_id'])
        ], limit=1)
        vals['order_id'] = nuvemshop_sale_order.openerp_id.id
        return super(NuvemshopSaleOrderLine, self).create(vals)

@nuvemshop
class SaleOrderLineAdapter(GenericAdapter):
    _model_name = 'nuvemshop.sale.order.line'
    _nuvemshop_model = 'orders'

    def read(self, data, attributes=None):
        """ Returns the information of a record """
        result = self.store[self._nuvemshop_model].get(
            id=data.get('nuvemshop_order_id')
        )

        lines = [
            line for line in result.get('products')
            if line.get('id') == data.get('id')
        ]

        lines[0].update({
            'nuvemshop_partner_id': result.get('customer').get('id'),
            'nuvemshop_order_id': result.get('id'),
        })

        return lines[0]
