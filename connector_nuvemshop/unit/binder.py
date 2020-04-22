# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.addons.connector.connector import Binder
from ..backend import nuvemshop


class NuvemshopBinder(Binder):

    """ Generic Binder for NuvemshopCommerce """


@nuvemshop
class NuvemshopModelBinder(NuvemshopBinder):

    """
    Bindings are done directly on the binding model.nuvemshop.product.category

    Binding models are models called ``nuvemshop.{normal_model}``,
    like ``nuvemshop.res.partner`` or ``nuvemshop.product.product``.
    They are ``_inherits`` of the normal models and contains
    the Nuvemshop ID, the ID of the Nuvemshop Backend and the additional
    fields belonging to the Nuvemshop instance.
    """
    _external_field = 'nuvemshop_id'
    _backend_field = 'backend_id'
    _openerp_field = 'openerp_id'
    _sync_date_field = 'sync_date'

    _model_name = [
        'nuvemshop.product.category',
        'nuvemshop.res.partner',
    ]

