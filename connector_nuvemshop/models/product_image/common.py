# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, models, fields
from ...unit.backend_adapter import (
    GenericAdapter, NuvemShopWebServiceImage)
from ...backend import nuvemshop

_logger = logging.getLogger(__name__)

class ProductImage(models.Model):
    _inherit = 'base_multi_image.image'

    nuvemshop_bind_ids = fields.One2many(
        comodel_name='nuvemshop.product.image',
        inverse_name='openerp_id',
        string="Nuvemshop Bindings",
    )


class NuvemshopProductImage(models.Model):
    _name = 'nuvemshop.product.image'
    _inherit = ['nuvemshop.binding', 'nuvemshop.handle.abstract']
    _inherits = {'base_multi_image.image': 'openerp_id'}
    _description = 'nuvemshop product image'

    openerp_id = fields.Many2one(comodel_name='base_multi_image.image',
                                 string='image',
                                 required=True,
                                 ondelete='cascade')

    nuvemshop_product_id = fields.Many2one(
        comodel_name='nuvemshop.product.template',
        string='Product',
        required=True,
        ondelete='cascade',
    )


@nuvemshop
class ImageAdapter(GenericAdapter):
    _model_name = 'nuvemshop.product.image'
    _nuvemshop_model = 'products'

    def search(self, filters):
        if filters.get('product_id'):
            images = self.store[self._nuvemshop_model].images.list(
                filters.get('product_id'), fields='id,product_id')
            return [img.toDict() for img in images]
        raise NotImplementedError

    def read(self, data, attributes=None):
        """ Returns the information of a record """
        return self.store[self._nuvemshop_model].images.get(
            resource_id=data['product_id'], id=data['id']
        )

    def write(self, id, data):
        """ Update records on the external system """
        data['id'] = id
        return self.store[self._nuvemshop_model].images.update(
            data['product_id'], data)

    def create(self, data):
        """ Create a record on the external system """
        return self.store[self._nuvemshop_model].images.add(
            data['product_id'], data)
