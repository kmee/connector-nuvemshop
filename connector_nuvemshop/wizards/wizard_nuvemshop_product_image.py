# -*- coding: utf-8 -*-
# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class WizardNuvemshopProductImage(models.TransientModel):

    _name = 'wizard.nuvemshop.product.image'

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
            nuvemshop_image_obj = self.env['nuvemshop.product.image']

            for image in self.env['base_multi_image.image'].browse(
                    wizard.env.context['active_ids']):

                if not nuvemshop_image_obj.search_count([
                    ('openerp_id', '=', image.id),
                    ('backend_id', '=', self.backend_id.id),
                ]):
                    nuvemshop_product_id = self.env[
                        'nuvemshop.product.template'].search(
                        [
                            ('openerp_id', '=', image.owner_id)
                        ]
                    )
                    nuvemshop_image_obj.create({
                        'backend_id': self.backend_id.id,
                        'handle': nuvemshop_image_obj._handle_name(
                            image.name),
                        'openerp_id': image.id,
                        'nuvemshop_product_id': nuvemshop_product_id.id
                    })
