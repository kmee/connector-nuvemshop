# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import logging
import hashlib

from openerp.addons.connector.unit.mapper import (
    mapping,
    ImportMapper
)

from ...backend import nuvemshop
from ...unit.backend_adapter import GenericAdapter
from ...unit.importer import NuvemshopImporter, normalize_datetime

_logger = logging.getLogger(__name__)


@nuvemshop
class ResPartnerImportMapper(ImportMapper):
    _model_name = 'nuvemshop.res.partner'

    direct = [
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
        (normalize_datetime('created_at'), 'created_at'),
        (normalize_datetime('updated_at'), 'updated_at'),
        ('active', 'active'),
        ('note', 'comment'),
    ]

    def _get_contacts(self, record):
        contacts = record.get('addresses')
        nuvemshop_parent_id = record.get('id')
        for contact in contacts:
            contact.update({
                'nuvemshop_parent_id': nuvemshop_parent_id,
            })
        return contacts

    children = [
        (
            _get_contacts,
            'nuvemshop_contact_ids',
            'nuvemshop.contact'
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
                nuvemshop_contact = self.env['nuvemshop.contact'].search(
                    [('nuvemshop_id', '=', items[0][2]['nuvemshop_id'])])
                if nuvemshop_contact:
                    nuvemshop_contact.write(items[0][2])
                    continue
            children.extend(items)
        return children

    @mapping
    def name(self, record):
        if record['name']:
            return {'name': record['name']}
        else:
            return {'name': record['billing_name']}

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
    def addresses_hash(self, record):
        return {'addresses_hash': hashlib.md5(
            str(record['addresses'])).digest()}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@nuvemshop
class ResPartnerImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.res.partner']

    def _is_uptodate(self, binding):
        """Return True if the import should be skipped because
        it is already up-to-date in OpenERP"""
        if super(ResPartnerImporter, self)._is_uptodate(binding):
            addresses_hash = hashlib.md5(
                str(self.nuvemshop_record['addresses'])).digest()
            if binding.addresses_hash == addresses_hash:
                return True
            binding.addresses_hash = addresses_hash
        return False


@nuvemshop
class ContactImportMapper(ImportMapper):
    _model_name = 'nuvemshop.contact'

    direct = [
        ('name', 'name'),
        ('address', 'street'),
        ('number', 'number'),
        ('floor', 'street2'),
        ('locality', 'district'),
        ('zipcode', 'zip'),
        ('phone', 'phone'),
        (normalize_datetime('created_at'), 'created_at'),
        (normalize_datetime('updated_at'), 'updated_at'),
    ]

    @mapping
    def country_id(self, record):
        if record['country']:
            country_id = self.env['res.country'].search(
                [('code', '=', record['country'])]
            )
            return {'country_id': country_id.id}

    def get_state(self, state):
        return self.env['res.country.state'].search(
            [('name', '=', state)]
        )

    @mapping
    def state_id(self, record):
        if record['province']:
            state_id = self.get_state(record['province'])
            return {'state_id': state_id.id}

    @mapping
    def l10n_br_city_id(self, record):
        if record['city']:
            state_id = self.get_state(record['province'])
            city_id = self.env['l10n_br_base.city'].search(
                [
                    ('name', '=', record['city']),
                    ('state_id', '=', state_id.id)
                 ], limit=1
            )
            return {'l10n_br_city_id': city_id.id}

    @mapping
    def type(self, record):
        return {'type': 'delivery'}

    @mapping
    def nuvemshop_line_id(self, record):
        if record.get('id'):
            return {'nuvemshop_id': record.get('id')}

    @mapping
    def nuvemshop_parent_id(self, record):
        if record.get('nuvemshop_parent_id'):
            nuvemshop_partner_binder = \
                self.binder_for('nuvemshop.res.partner')
            nuvemshop_partner = nuvemshop_partner_binder.to_openerp(
                record.get('nuvemshop_parent_id')
            )
            return {'nuvemshop_parent_id': nuvemshop_partner.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@nuvemshop
class ContactImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.contact']
