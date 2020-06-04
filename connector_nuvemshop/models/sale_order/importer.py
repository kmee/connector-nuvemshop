# -*- coding: utf-8 -*-
# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openerp.addons.connector.exception import (
    RetryableJobError,
    FailedJobError,
    MappingError
)

from openerp import fields
from openerp.addons.l10n_br_base.tools.misc import calc_price_ratio
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)

from ..res_partner.importer import ResPartnerImporter
from ..product_template.importer import ProductTemplateImporter
from ...unit.importer import NuvemshopImporter, normalize_datetime
from ...backend import nuvemshop
from ...unit.backend_adapter import GenericAdapter

_logger = logging.getLogger(__name__)


@nuvemshop
class SaleOrderImportMapper(ImportMapper):
    _model_name = 'nuvemshop.sale.order'

    direct = [
        ('token', 'token'),
        ('store_id', 'store_id'),
        ('shipping_min_days', 'shipping_min_days'),
        ('shipping_max_days', 'shipping_max_days'),
        ('billing_name', 'billing_name'),
        ('billing_phone', 'billing_phone'),
        ('billing_address', 'billing_address'),
        ('billing_number', 'billing_number'),
        ('billing_floor', 'billing_floor'),
        ('billing_locality', 'billing_locality'),
        ('billing_zipcode', 'billing_zipcode'),
        ('billing_city', 'billing_city'),
        ('billing_province', 'billing_province'),
        ('billing_country', 'billing_country'),
        ('shipping_cost_owner', 'shipping_cost_owner'),
        ('subtotal', 'subtotal'),
        ('discount', 'discount'),
        ('discount_coupon', 'discount_coupon'),
        ('discount_gateway', 'discount_gateway'),
        ('total', 'total'),
        ('total_usd', 'total_usd'),
        ('weight', 'weight'),
        ('currency', 'currency'),
        ('language', 'language'),
        ('gateway', 'gateway'),
        ('gateway_id', 'gateway_id'),
        ('shipping', 'shipping'),
        ('shipping_option', 'shipping_option'),
        ('shipping_option_code', 'shipping_option_code'),
        ('shipping_option_reference', 'shipping_option_reference'),
        ('shipping_pickup_details', 'shipping_pickup_details'),
        ('shipping_tracking_number', 'shipping_tracking_number'),
        ('shipping_tracking_url', 'shipping_tracking_url'),
        ('shipping_store_branch_name', 'shipping_store_branch_name'),
        ('shipping_pickup_type', 'shipping_pickup_type'),
        ('storefront', 'storefront'),
        ('note', 'note'),
        ('next_action', 'next_action'),
        ('number', 'client_order_ref'),
        ('cancel_reason', 'cancel_reason'),
        ('owner_note', 'owner_note'),
        ('cancelled_at', 'cancelled_at'),
        ('closed_at', 'closed_at'),
        ('read_at', 'read_at'),
        ('status', 'status'),
        ('payment_status', 'payment_status'),
        ('shipping_status', 'shipping_status'),
        ('shipped_at', 'shipped_at'),
        ('paid_at', 'paid_at'),
        ('landing_url', 'landing_url'),
        ('app_id', 'app_id'),
        (normalize_datetime('created_at'), 'created_at'),
        (normalize_datetime('updated_at'), 'updated_at'),
    ]

    def _get_sale_order_lines(self, record):
        order_lines = record.get('products')
        nuvemshop_order_id = record.get('id')
        nuvemshop_partner_id = record.get('customer').get('id')
        for line in order_lines:
            line.update({
                'nuvemshop_order_id': nuvemshop_order_id,
                'nuvemshop_partner_id': nuvemshop_partner_id,
            })
        return order_lines

    children = [
        (
            _get_sale_order_lines,
            'nuvemshop_order_line_ids',
            'nuvemshop.sale.order.line'
        ),
    ]

    def _map_child(self, map_record, from_attr, to_attr, model_name):
        source = map_record.source
        # TODO patch ImportMapper in connector to support callable
        if callable(from_attr):
            child_records = from_attr(self, source)
        else:
            child_records = source[from_attr]

        children = []
        for child_record in child_records:
            adapter = self.unit_for(GenericAdapter, model_name)
            detail_record = adapter.read(
                child_record
            )

            mapper = self._get_map_child_unit(model_name)
            items = mapper.get_items(
                [detail_record], map_record, to_attr, options=self.options
            )
            children.extend(items)
        return children

    @mapping
    def partner_id(self, record):
        if record['customer']:
            partner_id = self.binder_for(
                'nuvemshop.res.partner').to_openerp(
                record['customer']['id'], unwrap=True).id

            if not partner_id:
                raise RetryableJobError(
                    'Partner not imported yet. The job will be retried later',
                    seconds=10,
                    ignore_retry=True
                )

            company = self.backend_record.company_id or self.env.user.company_id

            ctx = dict(self.env.context)
            ctx.update({
                'company_id': company.id,
                'fiscal_category_id': company.sale_fiscal_category_id.id,
            })

            val = self.env['sale.order'].with_context(ctx).onchange_partner_id(
                partner_id)['value']

            val.update({'partner_id': partner_id})
            return val

    #TODO: REFATORAR PARA ESCOLHER CONDICAO DE PAGAMENTO CORRETAMENTE
    @mapping
    def account_payment_ids(self, record):
        if record['payment_details'].get('method'):
            if record['payment_details']['method'] == 'boleto':
                account_payment_ids = [(0, 0, {
                    'amount': record['total'],
                    'payment_term_id':
                        self.env['account.payment.term'].search([
                            ('forma_pagamento', '=', '15'),
                            ('name', '=', '15 Days'),
                        ], limit=1).id
                })]
                return {
                    'account_payment_ids': account_payment_ids
                }

    @mapping
    def date_order(self, record):
        if record['completed_at'].get('date'):
            order_date_datetime = fields.Datetime.from_string(
                record['completed_at']['date']
            )
            datetime_converted = fields.Datetime.context_timestamp(
                self.backend_record, order_date_datetime
            )
            converted_date_str = fields.Datetime.to_string(datetime_converted)

            return {'date_order': converted_date_str}

    @mapping
    def payment_details_method(self, record):
        if record['payment_details']:
            payment_details_method = record['payment_details']['method']
            payment_details_credit_card_company = \
                record['payment_details']['credit_card_company']
            payment_details_installments = \
                record['payment_details']['installments']
            return {
                'payment_details_method': payment_details_method,
                'payment_details_credit_card_company':
                    payment_details_credit_card_company,
                'payment_details_installments': payment_details_installments,
            }

    @mapping
    def client_details_browser_ip(self, record):
        if record['client_details']:
            client_details_browser_ip = record['client_details']['browser_ip']
            client_details_user_agent = record['client_details']['user_agent']
            return {
                'client_details_browser_ip': client_details_browser_ip,
                'client_details_user_agent': client_details_user_agent,
            }

    @mapping
    def discount_rate(self, record):
        if record['promotional_discount'].get('id'):
            return {
                'discount_rate': (
                    float(record['discount']) +
                    float(record['discount_coupon']) +
                    float(record['discount_gateway'])) / float(
                    record['subtotal']
                )}

    @mapping
    def ind_pres(self, record):
        return {'ind_pres': '2'}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@nuvemshop
class SaleOrderImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.sale.order']

    def _import_dependencies(self):
        record = self.nuvemshop_record
        self._import_dependency(
            record['customer']['id'],
            'nuvemshop.res.partner',
            ResPartnerImporter,
        )
        for line in record['products']:
            self._import_dependency(
                line['product_id'],
                'nuvemshop.product.template',
                ProductTemplateImporter,
            )

    def _after_import(self, binding):
        super(SaleOrderImporter, self)._after_import(binding)
        binding.openerp_id.onchange_fiscal()
        for line in binding.openerp_id.order_line:
            line.onchange_fiscal()


@nuvemshop
class SaleOrderLineImportMapper(ImportMapper):
    _model_name = 'nuvemshop.sale.order.line'


    direct = [
        ('name', 'name'),
        ('quantity', 'product_uom_qty'),
        ('price', 'price_unit'),
        (normalize_datetime('created_at'), 'created_at'),
        (normalize_datetime('updated_at'), 'updated_at'),
    ]

    @mapping
    def nuvemshop_line_id(self, record):
        if record.get('id'):
            return {'nuvemshop_id': record.get('id')}

    @mapping
    def nuvemshop_order_id(self, record):
        if record.get('nuvemshop_order_id'):
            nuvemshop_sale_order_binder = self.binder_for('nuvemshop.sale.order')
            nuvemshop_order = nuvemshop_sale_order_binder.to_openerp(
                record.get('nuvemshop_order_id')
            )
            return {'nuvemshop_order_id': nuvemshop_order.id}

    @mapping
    def company_fiscal_category(self, record):
        company = self.backend_record.company_id or self.env.user.company_id

        return{
            'company_id': company.id,
            'fiscal_category_id': company.sale_fiscal_category_id.id
        }

    @mapping
    def product_id(self, record):
        if record.get('variant_id'):
            product_product_binder = self.binder_for('nuvemshop.product.product')
            product_product = product_product_binder.to_openerp(
                record.get('variant_id'), unwrap=True
            )
            if product_product:
                return {'product_id': product_product.id}
            else:
                raise RetryableJobError(
                    'The product was not imported yet. The job will be retried later',
                    seconds=20,
                    ignore_retry=True
                )
    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

@nuvemshop
class SaleOrderLineImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.sale.order.line']
