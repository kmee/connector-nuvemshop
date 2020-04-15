# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api, fields, _


class NuvemShopBackend(models.Model):

    _name = 'nuvemshop.backend'
    _inherit = 'connector.backend'
    _description = 'NuvemShop Backend Configuration'
    _backend_type = 'nuvemshop'

    name = fields.Char(string='name')

    store_id = fields.Char(
        string="Store ID"
    )
    access_token = fields.Char(
        string="Acess Token"
    )

    version = fields.Selection(
        selection=[
            ('v1', 'V1')],
        string='Version'
    )

    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
        help="If a default language is selected, the records "
             "will be imported in the translation of this language.\n"
             "Note that a similar configuration exists "
             "for each storeview.",
    )
