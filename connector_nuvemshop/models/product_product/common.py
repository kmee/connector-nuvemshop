# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, models, fields
from ...unit.backend_adapter import GenericAdapter
from openerp.addons.connector.session import ConnectorSession
from ...backend import nuvemshop
from ...unit.importer import import_batch_delayed


_logger = logging.getLogger(__name__)

# TODO: Verificars se e necessario essa adiçao visto que ja e herdada do product.template
class ProductProduct(models.Model):
    _inherit = 'product.product'

    # nuvemshop_bind_ids = fields.One2many(
    #     comodel_name='nuvemshop.product.product',
    #     inverse_name='openerp_id',
    #     copy=False,
    #     string="Nuvemshop Bindings",
    # )
    nuvemshop_variants_bind_ids = fields.One2many(
        comodel_name='nuvemshop.product.product',
        inverse_name='openerp_id',
        string="Nuvemshop Variants Bindings",
    )

    image_id = fields.Integer(
        string="Image"
    )

    position = fields.Integer(
        string='Position'
    )

    promotional_price = fields.Float(
        string='Promotional Price'
    )

    stock_management = fields.Boolean(
        string="Stock Management"
    )

    width = fields.Float(
        string="Width"
    )

    height = fields.Float(
        string="Height"
    )

    depth = fields.Float(
        string="Depth"
    )

    values = fields.Char(
        string="Values"
    )


class NuvemshopProductProduct(models.Model):
    _name = 'nuvemshop.product.product'
    _inherit = ['nuvemshop.binding', 'nuvemshop.handle.abstract']
    _inherits = {'product.product': 'openerp_id'}
    _description = 'nuvemshop product product'
    _rec_name = 'name'

    openerp_id = fields.Many2one(comodel_name='product.product',
                                 string='product',
                                 required=True,
                                 ondelete='cascade')

    # nuvemshop_parent_id = fields.Many2one(
    #     comodel_name='nuvemshop.product.template',
    #     string='Nuvemshop Parent Product Template',
    #     ondelete='cascade',)

    # handle = fields.Char('Handle', translate=True)
    # published = fields.Boolean('Published')
    # free_shipping = fields.Boolean('Free Shipping')
    # canonical_url = fields.Char('Canonical URL')
    # brand = fields.Char('Brand')
    # description_html = fields.Html('HTML Description', translate=True)
    # seo_title = fields.Char('SEO Title', translate=True)
    # seo_description = fields.Char('SEO Description', translate=True)

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.handle = self._handle_name(self.name)


@nuvemshop
class ProductProductAdapter(GenericAdapter):
    _model_name = 'nuvemshop.product.product'
    _nuvemshop_model = 'products'

    def search(self, filters):
        if filters.get('product_id'):
            variants = self.store[self._nuvemshop_model].variants.list(
                filters.get('product_id'), fields='id,product_id')
            return [img.toDict() for img in variants]
        raise NotImplementedError

    def read(self, data, attributes=None):
        """ Returns the information of a record """
        return self.store[self._nuvemshop_model].variants.get(
            resource_id=data['product_id'], id=data['id']
        )
