# -*- coding: utf-8 -*-
# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _


class WizardNuvemshopProductTemplate(models.TransientModel):

    _name = 'wizard.nuvemshop.product.template'

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
            nuvemshop_template_obj = self.env['nuvemshop.product.template']

            for template in self.env['product.template'].browse(
                    wizard.env.context['active_ids']):

                if not nuvemshop_template_obj.search_count([
                    ('openerp_id', '=', template.id),
                    ('backend_id', '=', self.backend_id.id),
                ]):
                    nuvemshop_template_obj.create({
                        'backend_id': self.backend_id.id,
                        'handle': nuvemshop_template_obj._handle_name(
                            template.name),
                        'openerp_id': template.id,
                        'published': True,
                    })
