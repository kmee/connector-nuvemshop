# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api, fields, _
from openerp.exceptions import Warning
from openerp.addons.connector.session import ConnectorSession
from datetime import datetime

from tiendanube.client import NubeClient

from ..unit.importer import import_batch_delayed

LANG_NUVEMSHOP_ODOO = {
    'en': 'en_US',
    'pt': 'pt_BR',
    'es': 'es_ES',
}

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
    backend_url = fields.Char(readonly=True)
    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
        help="If a default language is selected, the records "
             "will be imported in the translation of this language.\n"
             "Note that a similar configuration exists "
             "for each storeview.",
    )
    language_ids = fields.Many2many(
        comodel_name='res.lang',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        index=True,
        string='Company',
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        help='Warehouse used to compute the stock quantities.'
    )
    stock_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Stock Location',
        help='Location used to import stock quantities.'
    )
    import_categories_since = fields.Datetime()
    import_partners_since = fields.Datetime()
    import_templates_since = fields.Datetime()
    import_orders_since = fields.Datetime()

    @api.multi
    def test_connection(self):
        client = NubeClient(self.access_token)
        store = client.get_store(self.store_id)
        try:
            store_info = store.get_info()
            self.backend_url = store_info.url_with_protocol
            self.store_info = store_info

            for lang in store_info.languages.keys():
                if store_info.languages[lang].active:
                    self.language_ids |= self.language_ids.search(
                        [('code', '=', LANG_NUVEMSHOP_ODOO[lang])], limit=1
                    )

        except Exception as e:
            raise Warning(_('Error!!! \n {}'.format(e.message)))

    @api.multi
    def import_category(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        import_start_time = datetime.now()
        backend_id = self.id
        from_date = None
        import_batch_delayed.delay(
            session, 'nuvemshop.product.category', backend_id,
            {'updated_at_min': from_date,
             'updated_at_max': import_start_time}, priority=1)
        return True

    @api.multi
    def import_categories(self):
        """ Import Product categories """
        for backend in self:
            backend.import_category()
        return True

    @api.multi
    def import_partner(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        import_start_time = datetime.now()
        backend_id = self.id
        from_date = None
        import_batch_delayed.delay(
            session, 'nuvemshop.res.partner', backend_id,
            {'updated_at_min': from_date,
             'updated_at_max': import_start_time}, priority=1)
        return True

    @api.multi
    def import_partners(self):
        """ Import Partners """
        for backend in self:
            backend.import_partner()
        return True

    @api.multi
    def import_order(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        import_start_time = datetime.now()
        backend_id = self.id
        from_date = None
        import_batch_delayed.delay(
            session, 'nuvemshop.sale.order', backend_id,
            {'updated_at_min': from_date,
             'updated_at_max': import_start_time}, priority=1)
        return True

    @api.multi
    def import_orders(self):
        """ Import Partners """
        for backend in self:
            backend.import_order()
        return True

    @api.multi
    def import_template(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        import_start_time = datetime.now()
        backend_id = self.id
        from_date = None
        import_batch_delayed.delay(
            session, 'nuvemshop.product.template', backend_id,
            {'updated_at_min': from_date,
             'updated_at_max': import_start_time}, priority=1)
        return True

    @api.multi
    def import_templates(self):
        """ Import Templates """
        for backend in self:
            backend.import_template()
        return True

    @api.multi
    def import_image(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        import_start_time = datetime.now()
        backend_id = self.id
        from_date = None
        import_batch_delayed.delay(
            session, 'nuvemshop.product.image', backend_id,
            {'updated_at_min': from_date,
             'updated_at_max': import_start_time}, priority=1)
        return True

    @api.multi
    def import_images(self):
        """ Import Images """
        for backend in self:
            products = self.env['nuvemshop.product.template'].search(
                [('backend_id', '=', backend.id)]
            ).mapped('openerp_id')
            for product_id in products:
                backend.import_image(product_id)
        return True

