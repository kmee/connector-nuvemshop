# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, models, fields
from ...unit.backend_adapter import GenericAdapter
from openerp.addons.connector.session import ConnectorSession
from ...backend import nuvemshop
from ...unit.importer import import_batch_delayed
from ..product_template.exporter import export_inventory



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
        for record in self:
            for bind in record.nuvemshop_bind_ids:
                import_batch_delayed(
                    session,
                    'nuvemshop.product.image',
                    bind.backend_id.id,
                    {'product_id': bind.nuvemshop_id}
                )

    @api.multi
    def import_variant_nuvemshop(self):
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
        for record in self:
            for bind in record.nuvemshop_bind_ids:
                import_batch_delayed(
                    session,
                    'nuvemshop.product.product',
                    bind.backend_id.id,
                    {'product_id': bind.nuvemshop_id}
                )

    # @api.multi
    # def import_attribute_nuvemshop(self):
    #     session = ConnectorSession(self.env.cr, self.env.uid,
    #                                context=self.env.context)
    #     for record in self:
    #         for bind in record.nuvemshop_bind_ids:
    #             import_batch_delayed(
    #                 session,
    #                 'nuvemshop.product.attribute',
    #                 bind.backend_id.id,
    #                 {'product_id': bind.nuvemshop_id}
    #             )
    #

    @api.multi
    def update_nuvemshop_quantities(self):
        for template in self:
            # Recompute product template Nuvemshop qty
            template.mapped('nuvemshop_bind_ids').recompute_nuvemshop_qty()
            # Recompute variant Nuvemshop qty
            template.mapped(
                'product_variant_ids.nuvemshop_bind_ids'
            ).recompute_nuvemshop_qty()
        return True

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

    # nuvemshop_parent_id = fields.Many2one(
    #     comodel_name='nuvemshop.product.category',
    #     string='Nuvemshop Parent Category',
    #     ondelete='cascade',)
    #
    handle = fields.Char('Handle', translate=True)
    published = fields.Boolean('Published')
    free_shipping = fields.Boolean('Free Shipping')
    canonical_url = fields.Char('Canonical URL')
    brand = fields.Char('Brand')
    description_html = fields.Html('HTML Description', translate=True)
    seo_title = fields.Char('SEO Title', translate=True)
    seo_description = fields.Char('SEO Description', translate=True)
    published = fields.Boolean('Remote available', default=True)
    stock = fields.Float(string='Quantidade em estoque na nuvemshop')

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.handle = self._handle_name(self.name)

    @api.multi
    def force_export_stock(self):
        session = ConnectorSession.from_env(self.env)
        for template in self:
            if template.product_variant_count > 1:
                for binding in template.mapped(
                        'product_variant_ids.nuvemshop_bind_ids'):
                    export_inventory.delay(
                        session,
                        'nuvemshop.product.product',
                        binding.id,
                        fields=['stock'],
                        priority=20
                    )
            else:
                for binding in template.nuvemshop_bind_ids:
                    export_inventory.delay(
                        session,
                        'nuvemshop.product.template',
                        binding.id,
                        fields=['stock'],
                        priority=20
                    )

    def _nuvemshop_qty(self):
        locations = self.backend_id.get_stock_locations()
        qty_available = self.with_context(location=locations.ids).qty_available
        return qty_available - self.outgoing_qty

    @api.multi
    def recompute_nuvemshop_qty(self):
        for product_binding in self:
            new_qty = product_binding._nuvemshop_qty()
            if product_binding.stock != new_qty:
                product_binding.stock = new_qty if new_qty >= 0.0 else 0.0
            # Recompute variants if is needed
            if product_binding.product_variant_count > 1:
                for variant in product_binding.mapped(
                        'product_variant_ids.nuvemshop_bind_ids'):
                    variant.recompute_nuvemshop_qty()
        return True

@nuvemshop
class TemplateAdapter(GenericAdapter):
    _model_name = 'nuvemshop.product.template'
    _nuvemshop_model = 'products'
