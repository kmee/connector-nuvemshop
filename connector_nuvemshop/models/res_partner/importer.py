# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)

from ...unit.importer import NuvemshopImporter
from ...backend import nuvemshop


@nuvemshop
class ResPartnerImportMapper(ImportMapper):
    _model_name = 'nuvemshop.res.partner'

    direct = [
        ('billing_name', 'name'),
        ('name', 'legal_name'),
        ('email', 'email'),
        ('identification', 'cnpj_cpf'),
        ('billing_zipcode', 'zip'),
        ('phone', 'phone'),
        ('billing_address', 'street'),
        ('billing_number', 'number'),
        ('billing_floor', 'street2'),
        ('billing_locality', 'district'),
        ('total_spent', 'total_spent'),
        ('total_spent_currency', 'total_spent_currency'),
        ('last_order_id', 'last_order_id'),
        ('created_at', 'created_at'),
        ('updated_at', 'updated_at'),
        ('active', 'active'),
        ('note', 'comment'),
    ]

    @mapping
    def country_id(self, record):
        if record['billing_country']:
            country_id = self.env['res.country'].search(
                [('code', '=', record['billing_country'])]
            )
            return {'country_id': country_id.id}

    def get_state(self, state):
        return self.env['res.country.state'].search(
            [('name', '=', state)]
        )

    @mapping
    def state_id(self, record):
        if record['billing_province']:
            state_id = self.get_state(record['billing_province'])
            return {'state_id': state_id.id}

    @mapping
    def l10n_br_city_id(self, record):
        if record['billing_city']:
            state_id = self.get_state(record['billing_province'])
            city_id = self.env['l10n_br_base.city'].search(
                [
                    ('name', '=', record['billing_city']),
                    ('state_id', '=', state_id.id)
                 ], limit=1
            )
            return {'l10n_br_city_id': city_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@nuvemshop
class ResPartnerImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.res.partner']
