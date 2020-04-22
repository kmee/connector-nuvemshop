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
        ('name', 'name'),
        ('email', 'email'),
        ('cnpj_cpf', 'identification'),
        ('phone', 'phone'),
        ('street', 'billing_address'),
        ('total_spent', 'total_spent'),
        ('total_spent_currency', 'total_spent_currency'),
        ('last_order_id', 'last_order_id'),
    ]

    @mapping
    def name(self, record):
        if record['name']:
            return {'name': record['name']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


@nuvemshop
class ResPartnerImporter(NuvemshopImporter):
    _model_name = ['nuvemshop.res.partner']
