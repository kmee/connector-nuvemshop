# -*- coding: utf-8 -*-
# Copyright (C) 2020  Gabriel Cardoso de Faria - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

import datetime
from datetime import timedelta
from dateutil.parser.isoparser import isoparse

from openerp.addons.connector.exception import (
    RetryableJobError,
    FailedJobError,
    MappingError,
    NothingToDoJob
)
from openerp.addons.connector.connector import ConnectorUnit
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)

from openerp import fields
from openerp.addons.l10n_br_base.tools.misc import calc_price_ratio

from .exporter import export_state_change, ORDER_COMMAND_MAPPING
from ..res_partner.importer import ResPartnerImporter
from ..product_template.importer import ProductTemplateImporter
from ...unit.importer import NuvemshopImporter, normalize_datetime
from ...backend import nuvemshop
from ...connector import add_checkpoint
from ...unit.backend_adapter import GenericAdapter

_logger = logging.getLogger(__name__)

# TODO: - refatorar estados para poder cancelar e retornar estoque
#       - rateio do frete


@nuvemshop
class SaleImportRule(ConnectorUnit):
    _model_name = ['nuvemshop.sale.order']

    def _rule_always(self, record, method):
        """ Always import the order """
        return True

    def _rule_never(self, record, method):
        """ Never import the order """
        raise NothingToDoJob('Orders with payment method %s '
                             'are never imported.' %
                             record['gateway'])

    def _rule_authorized(self, record, method):
        """ Import the order only if payment has been authorized. """
        if record.get('gateway') != 'offline' and \
                record.get('payment_status') not in ['authorized', 'paid']:
            raise RetryableJobError(
                'The order has not been authorized.\n'
                'The import will be retried later.',
                seconds=60,
                ignore_retry=True
            )

    def _rule_paid(self, record, method):
        """ Import the order only if it has received a payment """
        if not record.get('payment_status') == 'paid':
            raise RetryableJobError(
                'The order has not been paid.\n'
                'The import will be retried later.',
                seconds=60,
                ignore_retry=True
            )

    _rules = {
        'always': _rule_always,
        'paid': _rule_paid,
        'authorized': _rule_authorized,
        'never': _rule_never,
    }

    # def _rule_global(self, record, method):
    #     """ Rule always executed, whichever is the selected rule """
    #     # the order has been canceled since the job has been created
    #     order_number = record['number']
    #     if record['status'] == 'cancelled':
    #         raise NothingToDoJob('Order %s canceled' % order_number)
    #     max_days = method.days_before_cancel
    #     if max_days:
    #         order_date = isoparse(
    #             record.get('created_at')).replace(tzinfo=None)
    #
    #         if order_date + timedelta(days=max_days) < datetime.datetime.now():
    #
    #             if record['payment_status'] not in ('paid', 'authorized') and\
    #                     record['shipping_status'] == 'unshipped':
    #
    #                 raise NothingToDoJob(
    #                     'Import of the order %s canceled because '
    #                     'it has not been paid since %d '
    #                     'days' % (order_number, max_days))

    def check(self, record):
        """ Check whether the current sale order should be imported
        or not. It will actually use the payment method configuration
        and see if the choosed rule is fullfilled.

        :returns: True if the sale order should be imported
        :rtype: boolean
        """
        payment_method = False
        if record.get('gateway'):
            method = record.get('payment_details').get('method')
            method_name = record['gateway']
            if method:
                method_name = method_name + '(' + method + ')'
            payment_method = self.env['payment.method'].search([
                ('name', 'ilike', method_name),
            ])
            if not payment_method:
                payment_method = self.env['payment.method'].search([
                    ('name', 'ilike', record['gateway']),
                ])

        if not payment_method:
            raise FailedJobError(
                "The configuration is missing for the Payment Method '%s'.\n\n"
                "Resolution:\n"
                "- Go to "
                "'Sales > Configuration > Sales > Customer Payment Method\n"
                "- Create a new Payment Method with name '%s'\n"
                "-Eventually  link the Payment Method to an existing Workflow "
                "Process or create a new one." % (method_name,
                                                  method_name))
        if len(payment_method) > 1:
            raise FailedJobError(
                "Found more than 1 payment method, maybe a misconfiguration?"
                "Try creating a method with name %s" %(method_name)
            )
        # self._rule_global(record, payment_method)
        self._rules[payment_method.import_rule](self, record, payment_method)


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
        (normalize_datetime('cancelled_at'), 'cancelled_at'),
        (normalize_datetime('closed_at'), 'closed_at'),
        (normalize_datetime('read_at'), 'read_at'),
        ('status', 'status'),
        ('payment_status', 'payment_status'),
        ('shipping_status', 'shipping_status'),
        (normalize_datetime('shipped_at'), 'shipped_at'),
        (normalize_datetime('paid_at'), 'paid_at'),
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
            if len(items) == 1:
                nuvemshop_sale_line = \
                    self.env['nuvemshop.sale.order.line'].search([
                        ('nuvemshop_id', '=', items[0][2]['nuvemshop_id'])
                    ]
                )
                if nuvemshop_sale_line:
                    nuvemshop_sale_line.write(items[0][2])
                    continue
            children.extend(items)
        return children

    @mapping
    def warehouse_id(self, record):
        return {'warehouse_id': self.backend_record.warehouse_id.id}

    @mapping
    def payment(self, record):
        if record.get('gateway') and record.get('payment_details'):
            method = record['payment_details']['method']
            payment_method = self.env['payment.method'].search([
                ('name', 'ilike', record['gateway'] + '(' + method + ')'),
            ])

            assert payment_method, ("Payment method '%s' has not been found ; "
                            "you should create it manually (in Sales->"
                            "Configuration->Sales->Payment Methods" %
                            record['gateway'])

            return {
                'payment_method_id': payment_method.id,
                'workflow_process_id': payment_method.workflow_process_id.id,
                'payment_term_id': payment_method.payment_term_id.id,
            }

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

            company = self.backend_record.company_id or\
                      self.env.user.company_id

            ctx = dict(self.env.context)
            ctx.update({
                'company_id': company.id,
                'fiscal_category_id': company.sale_fiscal_category_id.id,
            })

            val = self.env['sale.order'].with_context(ctx).onchange_partner_id(
                partner_id)['value']

            val.update({'partner_id': partner_id})
            return val

    @mapping
    def partner_shipping_id(self, record):
        shipping_address_id = record['shipping_address']['id']
        partner_shipping_id = self.env['nuvemshop.contact'].search([
            ('nuvemshop_id', '=', shipping_address_id)])
        if partner_shipping_id:
            return {'partner_shipping_id': partner_shipping_id.id}

    #TODO: REFATORAR PARA ESCOLHER CONDICAO DE PAGAMENTO CORRETAMENTE

    # @mapping
    # def account_payment_ids(self, record):
    #     if record['payment_details'].get('method'):
    #         if record['payment_details']['method'] == 'boleto':
    #             account_payment_ids = [(0, 0, {
    #                 'amount': record['total'],
    #                 'payment_term_id':
    #                     self.env['account.payment.term'].search([
    #                         ('forma_pagamento', '=', '15'),
    #                         ('name', '=', '15 Days'),
    #                     ], limit=1).id
    #             })]
    #             return {
    #                 'account_payment_ids': account_payment_ids
    #             }

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
    def amount_freight(self, record):
        if record.get('shipping_cost_customer'):
            return {
                'amount_freight': float(record.get('shipping_cost_customer')),
                'shipping_cost_customer': record.get('shipping_cost_customer')
            }

    @mapping
    def delivery_carrier(self, record):
        if record.get('shipping_option'):
            carrier = self.env['delivery.carrier'].search(
                [('name', 'ilike', record['shipping_option'])]
            )
            if carrier:
                return {
                    'carrier_id': carrier.id
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
            nuvemshop_id=record['customer']['id'],
            binding_model='nuvemshop.res.partner',
            importer_class=ResPartnerImporter,
            always=True
        )
        for line in record['products']:
            self._import_dependency(
                nuvemshop_id=line['product_id'],
                binding_model='nuvemshop.product.template',
                importer_class=ProductTemplateImporter,
            )

    def _before_import(self):
        rules = self.unit_for(SaleImportRule)
        rules.check(self.nuvemshop_record)

    def _set_freight(self, binding):
        if self.nuvemshop_record.get('shipping_cost_customer'):
            binding.amount_freight = self.nuvemshop_record[
                'shipping_cost_customer'
            ]


    def _check_shipping_data(self, binding):
        if binding.carrier_id.name != self.nuvemshop_record['shipping_option']:
            add_checkpoint(
                self.session,
                'sale.order',
                binding.openerp_id,
                binding.backend_id.id
            )

    def _check_to_cancel(self, binding):
        order_number = binding.name
        if binding.status == 'cancelled' and binding.state != 'cancel':
            binding.with_context(
                connector_no_export=True
            ).canceled_in_backend = True
            raise NothingToDoJob('Order %s canceled' % order_number)
        max_days = binding.payment_method_id.days_before_cancel
        if max_days:
            order_date = isoparse(binding.created_at).replace(tzinfo=None)

            if order_date + timedelta(days=max_days) < datetime.datetime.now():
                ctx = dict(self.env.context)
                ctx.update(dict(connector_no_export=True))
                session = ConnectorSession(self.env.cr, self.env.uid,
                                           context=ctx)
                if binding.payment_status not in ('paid', 'authorized') and \
                        binding.shipping_status == 'unpacked' and\
                        binding.status != 'cancelled':
                    export_state_change.delay(
                        session,
                        'nuvemshop.sale.order',
                        binding.id,
                        command='cancel',
                        data=dict(reason='other')
                    )
                else:
                    check = add_checkpoint(
                        session=session,
                        model_name='sale.order',
                        record_id=binding.openerp_id.id,
                        backend_id=binding.backend_id.id
                    )
        return

    def _after_import(self, binding):
        super(SaleOrderImporter, self)._after_import(binding)
        self._check_to_cancel(binding)
        self._set_freight(binding)
        self._check_shipping_data(binding)
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
            nuvemshop_sale_order_binder = self.binder_for(
                'nuvemshop.sale.order')
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
            product_product_binder = self.binder_for(
                'nuvemshop.product.product')
            product_product = product_product_binder.to_openerp(
                record.get('variant_id'), unwrap=True
            )
            if product_product:
                return {'product_id': product_product.id}
            else:
                raise RetryableJobError(
                    'The product was not imported yet. '
                    'The job will be retried later',
                    seconds=20,
                    ignore_retry=True
                )

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

@nuvemshop
class SaleOrderLineImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.sale.order.line']
