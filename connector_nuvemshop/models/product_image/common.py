# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, models, fields
from ...unit.backend_adapter import GenericAdapter
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


@nuvemshop
class ImageAdapter(GenericAdapter):
    _model_name = 'nuvemshop.product.image'
    _nuvemshop_model = 'product_image'
