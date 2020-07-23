# -*- coding: utf-8 -*-
# Copyright (C) 2020  Daniel Sadamo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from openerp.addons.connector.event import on_record_unlink
from ...unit.deleter import delay_delete_record, delay_delete_all_bindings

from ...unit.deleter import NuvemshopDeleter
from ...backend import nuvemshop

@nuvemshop
class ProductProductDeleteExporter(NuvemshopDeleter):
    _model_name = ['nuvemshop.product.template']


@on_record_unlink(model_names='nuvemshop.product.template')
def nuvemshop_product_template_unlink(session, model_name, record_id):
    delay_delete_record(session, model_name, record_id, priority=20)


@on_record_unlink(model_names='product.template')
def product_template_unlink(session, model_name, record_id):
    delay_delete_all_bindings(session, model_name, record_id)
