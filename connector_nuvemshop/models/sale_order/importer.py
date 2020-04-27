# -*- coding: utf-8 -*-
# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.exception import MappingError
from openerp import fields
from openerp.addons.l10n_br_base.tools.misc import calc_price_ratio
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)

from ...unit.importer import NuvemshopImporter
from ...backend import nuvemshop


@nuvemshop
class SaleOrderImportMapper(ImportMapper):
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
            self.env.context = dict(self.env.context)
            fiscal_category_id = self.env['res.company'].browse(
                self.env.user.company_id.id).sale_fiscal_category_id
            self.env.context.update({
                'company_id': self.env.user.company_id.id,
                'fiscal_category_id': fiscal_category_id.id,
            })
            val = self.env['sale.order'].onchange_partner_id(
                partner_id)['value']
            val.update({'partner_id': partner_id})
            return val

    @mapping
    def order_line(self, record):
        lines = record.get('products', [])
        order_lines = []
        partner_id = self.binder_for(
            'nuvemshop.res.partner').to_openerp(
            record['customer']['id'], unwrap=True).id
        company = self.env['res.company'].browse(self.env.user.company_id.id)
        fiscal_category_id = company.sale_fiscal_category_id
        self.env.context = dict(self.env.context)
        self.env.context.update({
            'company_id': company.id,
            'fiscal_category_id': fiscal_category_id.id,
        })
        val = self.env['sale.order'].onchange_partner_id(
            partner_id)['value']
        self.env.context.update({
            'parent_fiscal_category_id': fiscal_category_id.id,
            'partner_invoice_id': val['partner_invoice_id'],
            'lang': 'pt_BR',
            'parent_fiscal_position': False,
            'tz': 'America/Sao_Paulo',
            'fiscal_position': val['fiscal_position'],
            'partner_id': partner_id,
        })
        result = {'value': {'fiscal_position': False}}
        kwargs = {
            'partner_id': partner_id,
            'partner_invoice_id': val['partner_invoice_id'],
            'fiscal_category_id': fiscal_category_id.id,
            'company_id': company.id,
            'context': self.env.context
        }
        result = self.env[
            'account.fiscal.position.rule'].apply_fiscal_mapping(
            result, **kwargs)
        fiscal_position = result['value'].get('fiscal_position')
        for line in lines:
            template_id = self.binder_for(
                'nuvemshop.product.template').to_openerp(
                line['product_id'], unwrap=True).id
            product_id = self.env['product.product'].search([
                ('product_tmpl_id', '=', template_id)
            ])
            res = self.env['sale.order.line'].product_id_change(
                pricelist=val['pricelist_id'],
                product=product_id.id,
                qty=float(line.get('quantity')),
                uom=False,
                qty_uos=False,
                uos=False,
                name=product_id.name,
                partner_id=partner_id,
                date_order=fields.Datetime.now(),
                fiscal_position=False,
                flag=False,
            )['value']
            res.update({
                'product_id': product_id.id,
                'qty': float(line.get('quantity')),
                'price_unit': float(line.get('price')),
                'freight_value': calc_price_ratio(
                    float(line.get('quantity')) * float(line.get('price')),
                    float(record['shipping_cost_owner']),
                    float(record['subtotal']),)
            })
            if res.get('tax_id'):
                res['tax_id'] = [(6, 0, res['tax_id'].ids)]

            order_lines += [(0, 0, res)]
        return {'order_line': order_lines,
                'fiscal_position': fiscal_position}

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
class SaleOrderImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.sale.order']
