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


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    nuvemshop_bind_ids = fields.One2many(
        comodel_name='nuvemshop.product.template',
        inverse_name='openerp_id',
        string="Nuvemshop Bindings",
    )

    @api.multi
    def import_image_nuvemshop(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        for record in self.with_context(connector_no_export=True):
            for bind in record.nuvemshop_bind_ids:
                import_batch_delayed(
                    session,
                    'nuvemshop.product.image',
                    bind.backend_id.id,
                    {
                        'product_id': bind.nuvemshop_id,
                    }
                )

    @api.multi
    def import_variant_nuvemshop(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        for record in self.with_context(connector_no_export=True):
            for bind in record.nuvemshop_bind_ids:
                import_batch_delayed(
                    session,
                    'nuvemshop.product.product',
                    bind.backend_id.id,
                    {
                        'product_id': bind.nuvemshop_id,
                    }
                )


class NuvemshopProductTemplate(models.Model):
    _name = 'nuvemshop.product.template'
    _inherit = ['nuvemshop.binding', 'nuvemshop.handle.abstract']
    _inherits = {'product.template': 'openerp_id'}
    _description = 'nuvemshop product template'
    _rec_name = 'name'

    openerp_id = fields.Many2one(comodel_name='product.template',
                                 string='template',
                                 required=True,
                                 ondelete='cascade')

    nuvemshop_variant_ids = fields.One2many(
        comodel_name='nuvemshop.product.product',
        inverse_name='main_template_id',
        string='Variants'
    )

    nuvemshop_image_ids = fields.One2many(
        comodel_name='nuvemshop.product.image',
        inverse_name='nuvemshop_product_id',
        string='Images'
    )

    handle = fields.Char('Handle', translate=True)
    published = fields.Boolean('Published')
    free_shipping = fields.Boolean('Free Shipping')
    canonical_url = fields.Char('Canonical URL')
    brand = fields.Char('Brand')
    description_html = fields.Html('HTML Description', translate=True)
    seo_title = fields.Char('SEO Title', translate=True)
    seo_description = fields.Char('SEO Description', translate=True)

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.handle = self._handle_name(self.name)


@nuvemshop
class TemplateAdapter(GenericAdapter):
    _model_name = 'nuvemshop.product.template'
    _nuvemshop_model = 'products'
