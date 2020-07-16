# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import api, models, fields
from ...unit.backend_adapter import GenericAdapter
from ...backend import nuvemshop
from openerp.addons.connector.session import ConnectorSession
from ..product_product.exporter import export_inventory

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
        for record in self:
            for bind in record.nuvemshop_variants_bind_ids:
                if bind.nuvemshop_image_id:
                    image_record = bind.nuvemshop_image_id
                    image_record.product_variant_ids += record

    @api.multi
    def update_nuvemshop_qty(self):
        for variant_binding in self.nuvemshop_variants_bind_ids:
            variant_binding.recompute_nuvemshop_qty()

    @api.multi
    def update_nuvemshop_quantities(self):
        for variant_binding in \
                self.nuvemshop_variants_bind_ids:
            variant_binding.recompute_nuvemshop_qty()
        return True

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

    nuvemshop_image_id = fields.Many2one(
        comodel_name='nuvemshop.product.image',
        string='Image Record'
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

    stock = fields.Float(
        string="Stock"
    )

    @api.multi
    def force_export_stock(self):
        session = ConnectorSession.from_env(self.env)
        for binding in self.nuvemshop_variants_bind_ids:
            export_inventory.delay(
                session,
                'nuvemshop.product.product',
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
            locations = product_binding.backend_id.get_stock_locations()
            qty_available = product_binding.with_context(
                location=locations.ids).qty_available
            qty = qty_available - product_binding.outgoing_qty # - 3 # Security Quantity???
            if product_binding.stock != qty:
                product_binding.stock = qty if qty >= 0.0 else 0.0
        return True

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.handle = self._handle_name(self.name)


@nuvemshop
class ProductProductAdapter(GenericAdapter):
    _model_name = 'nuvemshop.product.product'
    _nuvemshop_model = 'products'

    def export_quantity(self, template_id, nuvemshop_id, quantity):
        # TODO: verificar estoque no nuvemshop antes de exportar
        # caso o numero esteja diferente, importar ordens antes
        self.write(nuvemshop_id, dict(product_id=template_id, stock=quantity))

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
