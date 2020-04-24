# -*- coding: utf-8 -*-
# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)

from ...unit.importer import NuvemshopImporter
from ...backend import nuvemshop


@nuvemshop
class ProductCategoryImportMapper(ImportMapper):
    _model_name = 'nuvemshop.sale.order'

    direct = [
        ('token', 'token'),
        ('store_id', 'store_id'),
        ('shipping_min_days', 'shipping_min_days'),
        ('shipping_max_days', 'shipping_max_days'),
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
    ]

    @mapping
    def partner_id(self, record):
        if record['customer']:
            partner_id = self.binder_for(
                'nuvemshop.res.partner').to_openerp(
                record['customer']['id'], unwrap=True).id
            val = self.env['sale.order'].onchange_partner_id(
                partner_id)['value']
            val.update({'partner_id': partner_id})
            return val

    @mapping
    def partner_id(self, record):
        lines = record.get('order_line', [])
        order_lines = []
        for line in lines:
            product_id = self.binder_for(
                'nuvemshop.product.template').to_openerp(
                line['product_id'], unwrap=True).id
            order_lines += [(0, 0, {
                'product_id': product_id,
            })]
        return {'order_line': order_lines}


    @mapping
    def shipping_cost_owner(self, record):
        if record['shipping_cost_owner']:
            return {
                'shipping_cost_owner': float(record['shipping_cost_owner'])}

    @mapping
    def discount_coupon(self, record):
        if record['discount_coupon']:
            return {
                'discount_coupon': float(record['discount_coupon'])}

    @mapping
    def discount_gateway(self, record):
        if record['discount_gateway']:
            return {
                'discount_gateway': float(record['discount_gateway'])}

    @mapping
    def amount_freight(self, record):
        if record['shipping_cost_customer']:
            return {
                'amount_freight': float(record['shipping_cost_owner'])}

    @mapping
    def amount_untaxed(self, record):
        if record['subtotal']:
            return {
                'amount_untaxed': float(record['subtotal'])}

    @mapping
    def amount_discount(self, record):
        if record['discount']:
            return {
                'amount_discount': float(record['discount'])}

    @mapping
    def amount_total(self, record):
        if record['total']:
            return {
                'amount_total': float(record['total'])}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@nuvemshop
class ProductCategoryImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.sale.order']
