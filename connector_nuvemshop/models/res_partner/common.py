# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, models, fields
from ...unit.backend_adapter import GenericAdapter
from ...backend import nuvemshop

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    nuvemshop_bind_ids = fields.One2many(
        comodel_name='nuvemshop.res.partner',
        inverse_name='openerp_id',
        string="Nuvemshop Bindings",
    )

    nuvemshop_contact_bind_ids = fields.One2many(
        comodel_name='nuvemshop.contact',
        inverse_name='openerp_id',
        string="Nuvemshop Contact Bindings"
    )

    @api.multi
    @api.constrains('cnpj_cpf', 'inscr_est')
    def _check_cnpj_inscr_est(self):
        if not any(self.mapped('is_company')):
            return
        return super(ResPartner, self)._check_cnpj_inscr_est()

class NuvemshopResPartner(models.Model):
    _name = 'nuvemshop.res.partner'
    _inherit = ['nuvemshop.binding', 'nuvemshop.handle.abstract']
    _inherits = {'res.partner': 'openerp_id'}
    _description = 'nuvemshop res partner'
    _rec_name = 'name'

    openerp_id = fields.Many2one(comodel_name='res.partner',
                                 string='category',
                                 required=True,
                                 ondelete='cascade')
    nuvemshop_contact_ids = fields.One2many(
        comodel_name='nuvemshop.contact',
        inverse_name='nuvemshop_parent_id',
        string='Nuvemshop Contacts',
    )

    addresses_hash = fields.Char()

    total_spent = fields.Float()
    total_spent_currency = fields.Char()
    last_order_id = fields.Char()


@nuvemshop
class CategoryAdapter(GenericAdapter):
    _model_name = 'nuvemshop.res.partner'
    _nuvemshop_model = 'customers'


class NuvemshopContact(models.Model):
    _name = 'nuvemshop.contact'
    _inherit = ['nuvemshop.binding', 'nuvemshop.handle.abstract']
    _inherits = {'res.partner': 'openerp_id'}
    _description = 'nuvemshop contact'
    _rec_name = 'name'

    openerp_id = fields.Many2one(comodel_name='res.partner',
                                 string='category',
                                 required=True,
                                 ondelete='cascade')

    nuvemshop_parent_id = fields.Many2one(
        comodel_name='nuvemshop.res.partner',
        string='Nuvemshop Parent',
    )

    @api.model
    def create(self, vals):
        nuvemshop_res_partner = self.env['nuvemshop.res.partner'].search([
            ('id', '=', vals['nuvemshop_parent_id'])
        ], limit=1)
        vals['parent_id'] = nuvemshop_res_partner.openerp_id.id
        return super(NuvemshopContact, self).create(vals)


@nuvemshop
class ContactAdapter(GenericAdapter):
    _model_name = 'nuvemshop.contact'
    _nuvemshop_model = 'customers'

    def read(self, data, attributes=None):
        """ Returns the information of a record """
        result = self.store[self._nuvemshop_model].get(
            id=data.get('nuvemshop_parent_id')
        )

        contacts = [
            contact for contact in result.get('addresses')
            if contact.get('id') == data.get('id')
        ]

        contacts[0].update({
            'nuvemshop_parent_id': result.get('id'),
        })

        return contacts[0]
