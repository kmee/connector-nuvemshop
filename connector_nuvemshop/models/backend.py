# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import pytz
from openerp import models, api, fields, _
from openerp.exceptions import Warning
from openerp.addons.connector.session import ConnectorSession
from datetime import datetime
from .product_product.exporter import export_product_quantities
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

    def _from_date_with_tz(self, import_since):
        if import_since:
            timezone = pytz.timezone(self.env.user.tz)
            from_date = fields.Datetime.from_string(import_since)
            from_date_tz = timezone.localize(from_date)
            from_date_dt = from_date_tz.replace(microsecond=0).isoformat()
            return str(from_date_dt)
        return None

    @api.multi
    def import_category(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        backend_id = self.id
        updated_at_min = self._from_date_with_tz(self.import_categories_since)
        import_start_time = datetime.now()
        self.import_categories_since = import_start_time
        import_batch_delayed.delay(
            session,
            'nuvemshop.product.category',
            backend_id,
            {'updated_at_min': updated_at_min},
            priority=1
        )
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
        backend_id = self.id
        updated_at_min = self._from_date_with_tz(self.import_partners_since)

        func = "openerp.addons.connector_nuvemshop.unit.importer." \
               "import_batch_delayed('nuvemshop.res.partner'"

        jobs = session.env['queue.job'].sudo().search(
            [('func_string', 'like', "%s%%" % func),
             ('state', '!=', 'done')]
        )
        if not jobs:
            import_start_time = datetime.now()
            self.import_partners_since = import_start_time

            import_batch_delayed.delay(
                session,
                'nuvemshop.res.partner',
                backend_id,
                {'updated_at_min': updated_at_min},
                priority=1
            )
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
        backend_id = self.id

        filter_data = {}

        updated_at_min = self._from_date_with_tz(self.import_orders_since)
        filter_data.update({'updated_at_min': updated_at_min})

        func = "openerp.addons.connector_nuvemshop.unit.importer." \
           "import_batch_delayed('nuvemshop.sale.order'"

        jobs = session.env['queue.job'].sudo().search(
            [('func_string', 'like', "%s%%" % func),
             ('state', '!=', 'done')]
        )
        if not jobs:
            self.import_orders_since = datetime.now()
            import_batch_delayed.delay(
                session,
                'nuvemshop.sale.order',
                backend_id,
                filter_data,
                priority=1
            )

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
        backend_id = self.id
        updated_at_min = self._from_date_with_tz(self.import_templates_since)
        import_start_time = datetime.now()
        self.import_templates_since = import_start_time
        import_batch_delayed.delay(
            session,
            'nuvemshop.product.template',
            backend_id,
            {'updated_at_min': updated_at_min},
            priority=1
        )
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
        backend_id = self.id
        updated_at_min = self._from_date_with_tz(self.import_images_since)
        import_start_time = datetime.now()
        self.import_images_since = import_start_time
        import_batch_delayed.delay(
            session,
            'nuvemshop.product.image',
            backend_id,
            {'updated_at_min': updated_at_min},
            priority=1
        )
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

    @api.multi
    def get_stock_locations(self):
        self.ensure_one()
        locations = self.env['stock.location'].search([
            ('id', 'child_of', self.stock_location_id.id or
             self.warehouse_id.lot_stock_id.id),
            ('nuvemshop_synchronized', '=', True),
            ('usage', '=', 'internal'),
        ])
        return locations

    @api.multi
    def update_product_stock_qty(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        for backend_record in self:
            export_product_quantities.delay(session, backend_record.id)
        return True

    @api.model
    def _scheduler_import_sale_orders(self, domain=None):
        backend = self.search(domain or [])
        backend.import_partners()
        backend.import_orders()
