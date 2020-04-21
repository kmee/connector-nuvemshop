# -*- coding: utf-8 -*-
# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class WizardNuvemshopProductCategory(models.TransientModel):

    _name = 'wizard.nuvemshop.product.category'

    def _default_backend(self):
        return self.env['nuvemshop.backend'].search([], limit=1).id

    backend_id = fields.Many2one(
        comodel_name='nuvemshop.backend',
        default=_default_backend,
        string='Backend',
    )

    @api.multi
    def doit(self):
        self.ensure_one()
        for wizard in self:
            nuvemshop_category_obj = self.env['nuvemshop.product.category']

            for category in self.env['product.category'].browse(
                    wizard.env.context['active_ids']):

                if not nuvemshop_category_obj.search_count([
                    ('openerp_id', '=', category.id),
                    ('backend_id', '=', self.backend_id.id),
                ]):
                    nuvemshop_category_obj.create({
                        'backend_id': self.backend_id.id,
                        'handle': nuvemshop_category_obj._handle_name(
                            category.name),
                        'openerp_id': category.id,
                        'openerp_id': category.id,
                    })
