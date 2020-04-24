# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class NuvemShopBinding(models.AbstractModel):
    """ Abstract Model for the Bindigs.

    All the models used as bindings between nuvemshop and OpenERP
    (``nuvemshop.res.partner``, ``nuvemshop.product.product``, ...) should
    ``_inherit`` it.
    """
    _name = 'nuvemshop.binding'
    _inherit = 'external.binding'
    _description = 'Nuvemshop Binding (abstract)'

    # openerp_id = openerp-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='nuvemshop.backend',
        string='Nuvemshop Backend',
        required=True,
        ondelete='restrict',
    )
    backend_url = fields.Char(related='backend_id.backend_url')
    nuvemshop_id = fields.Char(string='ID on NuvemShop')
    created_at = fields.Datetime()
    updated_at = fields.Datetime()

    _sql_constraints = [
        ('nuvemshop_uniq', 'unique(backend_id, nuvemshop_id)',
         'A binding already exists with the same Nuvem Shop ID.'),
    ]
