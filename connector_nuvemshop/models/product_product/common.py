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


class ProductProduct(models.Model):
    _inherit = 'product.product'

    nuvemshop_variants_bind_ids = fields.One2many(
        comodel_name='nuvemshop.product.product',
        inverse_name='openerp_id',
        string="Nuvemshop Variants Bindings",
    )

    @api.multi
    def import_variant_image_nuvemshop(self):
        # session = ConnectorSession(self.env.cr, self.env.uid,
        #                            context=self.env.context)
        for record in self:
            for bind in record.nuvemshop_variants_bind_ids:
                if bind.image_id:
                    image_record = record.nuvemshop_bind_ids.mapped(
                        'image_ids').mapped('nuvemshop_bind_ids').filtered(
                        lambda x: str(bind.image_id) in x.nuvemshop_id
                    )
                    image_record.product_variant_ids += record
                    image_record.sequence = 0
        return


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

    main_template_id = fields.Many2one(
        comodel_name='nuvemshop.product.template',
        string='Main Template',
        required=True,
        ondelete='cascade',
    )

    image_id = fields.Char(
        string="Image"
    )

    position = fields.Char(
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

    stock = fields.Char(
        string="Stock"
    )

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
            return [var.toDict() for var in variants]
        raise NotImplementedError

    def read(self, data, attributes=None):
        """ Returns the information of a record """
        return self.store[self._nuvemshop_model].variants.get(
            resource_id=data['product_id'], id=data['id']
        )

    def write(self, id, data):
        """ Update records on the external system """
        data['id'] = id
        return self.store[self._nuvemshop_model].variants.update(
            data['product_id'], data
        )

    def create(self, data):
        """ Create a record on the external system """
        return self.store[self._nuvemshop_model].variants.add(
            data['product_id'], data
        )
