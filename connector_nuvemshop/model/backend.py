# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api, fields, _
from openerp.exceptions import Warning
from openerp.addons.connector.session import ConnectorSession
from datetime import datetime

from tiendanube.client import NubeClient

from .product_category import category_import_batch


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
    store_info = fields.Text(readonly=True)
    url = fields.Char(readonly=True)
    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
        help="If a default language is selected, the records "
             "will be imported in the translation of this language.\n"
             "Note that a similar configuration exists "
             "for each storeview.",
    )

    @api.multi
    def test_connection(self):
        client = NubeClient(self.access_token)
        store = client.get_store(self.store_id)
        try:
            store_info = store.get_info()
            self.url = store_info.url_with_protocol
            self.store_info = store_info
        except Exception as e:
            raise Warning(_('Error!!! \n {}'.format(e.message)))

    @api.multi
    def import_category(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        import_start_time = datetime.now()
        backend_id = self.id
        from_date = None
        category_import_batch.delay(
            session, 'nuvemshop.product.category', backend_id,
            {'from_date': from_date,
             'to_date': import_start_time}, priority=1)
        return True
    @api.multi
    def import_categories(self):
        """ Import Product categories """
        for backend in self:
            backend.import_category()
        return True

