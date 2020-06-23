# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    nuvemshop_synchronized = fields.Boolean(
        string='Sync with Nuvemshop',
        help='Check this option to synchronize this location with Nuvemshop')

    @api.model
    def get_nuvemshop_stock_locations(self):
        nuvemshop_locations = self.search([
            ('nuvemshop_synchronized', '=', True),
            ('usage', '=', 'internal'),
        ])
        return nuvemshop_locations
