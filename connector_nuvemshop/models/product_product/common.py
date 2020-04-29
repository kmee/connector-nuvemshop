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
        session = ConnectorSession(self.env.cr, self.env.uid,
                                   context=self.env.context)
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

    # @api.multi
    # def import_attributes_value_nuvemshop(self):
    #     session = ConnectorSession(self.env.cr, self.env.uid,
    #                                context=self.env.context)
    #     for record in self:
    #         for bind in record.nuvemshop_bind_ids:
    #             import_batch_delayed(
    #                 session,
    #                 'nuvemshop.product.attribute.value',
    #                 bind.backend_id.id,
    #                 {'product_id': bind.nuvemshop_id}
    #             )

    # nuvemshop_bind_ids = fields.One2many(
    #     comodel_name='nuvemshop.product.product',
    #     inverse_name='openerp_id',
    #     copy=False,
    #     string="Nuvemshop Bindings",
    # )


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

    image_id = fields.Integer(
        string="Image"
    )

    position = fields.Integer(
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

    # nuvemshop_parent_id = fields.Many2one(
    #     comodel_name='nuvemshop.product.template',
    #     string='Nuvemshop Parent Product Template',
    #     ondelete='cascade',)

    # handle = fields.Char('Handle', translate=True)
    # published = fields.Boolean('Published')
    # free_shipping = fields.Boolean('Free Shipping')
    # canonical_url = fields.Char('Canonical URL')
    # brand = fields.Char('Brand')
    # description_html = fields.Html('HTML Description', translate=True)
    # seo_title = fields.Char('SEO Title', translate=True)
    # seo_description = fields.Char('SEO Description', translate=True)

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

#
# class ProductAttribute(models.Model):
#     _inherit = 'product.attribute'
#
#     nuvemshop_bind_ids = fields.One2many(
#         comodel_name='nuvemshop.product.attribute',
#         inverse_name='openerp_id',
#         string='Nuvemshop Bindings (attribute)',
#     )
#
#
# class NuvemshopProductAttribute(models.Model):
#     _name = 'nuvemshop.product.attribute'
#     _inherit = ['nuvemshop.binding', 'nuvemshop.handle.abstract']
#     _inherits = {'product.attribute': 'openerp_id'}
#
#     openerp_id = fields.Many2one(
#         comodel_name='product.attribute',
#         string='Attribute',
#         required=True,
#         ondelete='cascade',
#     )
#
#
# @nuvemshop
# class ProductAttributeAdapter(GenericAdapter):
#     _model_name = 'nuvemshop.product.attribute'
#     _nuvemshop_model = 'products'
#
#     def search(self, filters):
#         if filters.get('product_id'):
#             attributes = self.store[self._nuvemshop_model].list(
#                 fields=['attributes'], filters=filters)
#             return [attrib.toDict() for attrib in attributes]
#         raise NotImplementedError
#
#     def read(self, data, attributes=None):
#         """ Returns the information of a record """
#         return self.store[self._nuvemshop_model].get(
#             resource_id=data['product_id'], attribute=data['name']
#         )
#
#
# class ProductAttributeValue(models.Model):
#     _inherit = 'product.attribute.value'
#
#     nuvemshop_bind_ids = fields.One2many(
#         comodel_name='nuvemshop.product.attribute.value',
#         inverse_name='openerp_id',
#         string='Nuvemshop Bindings',
#     )
#
#
# class NuvemshopProductAttributeValue(models.Model):
#     _name = 'nuvemshop.product.attribute.value'
#     _inherit = ['nuvemshop.binding', 'nuvemshop.handle.abstract']
#     _inherits = {'product.attribute.value': 'openerp_id'}
#
#     openerp_id = fields.Many2one(
#         comodel_name='product.attribute.value',
#         string='Attribute',
#         required=True,
#         ondelete='cascade',
#     )
#
#     id_attribute_group = fields.Many2one(
#         comodel_name='nuvemshop.product.attribute')
#
#
# @nuvemshop
# class ProductAttributeValueAdapter(GenericAdapter):
#     _model_name = 'nuvemshop.product.attribute.value'
#     _nuvemshop_model = 'products'
