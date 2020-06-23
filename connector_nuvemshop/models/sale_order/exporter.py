# -*- coding: utf-8 -*-
# Copyright (C) 2020  Daniel Sadamo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from openerp import _
from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.queue.job import job

from ...backend import nuvemshop
from ...connector import get_environment
from ...unit.exporter import NuvemshopExporter

ORDER_COMMAND_MAPPING = {
    # 'draft': 'pending',
    # 'manual': 'processing',
    # 'progress': 'processing',
    # 'shipping_except': 'processing',
    # 'invoice_except': 'processing',
    # 'done': 'complete',
    'cancel': 'close',
    # 'waiting_date': 'holded'
}


@on_record_write(model_names='sale.order')
def sale_order_write(session, model_name, record_id, fields):
    if session.context.get('connector_no_export'):
        return
    if fields.get('state') and ORDER_COMMAND_MAPPING.get(fields.get('state')):
        model = session.env[model_name]
        record = model.browse(record_id)
        for binding in record.nuvemshop_bind_ids:
            export_state_change.delay(
                session,
                'nuvemshop.sale.order',
                binding.id,
                command=ORDER_COMMAND_MAPPING[fields.get('state')]
            )


@nuvemshop
class SaleStatusExporter(NuvemshopExporter):
    _model_name = ['nuvemshop.sale.order']

    def run(self, binding_id, command):
        self.backend_adapter.sale_order_command(binding_id, command)


@job(default_channel='root.nuvemshop')
def export_state_change(session, model_name, binding_id, command):
    """ Change state of a sales order on Nuvemshop """
    binding = session.env[model_name].browse(binding_id)
    backend_id = binding.backend_id.id
    env = get_environment(session, model_name, backend_id)
    exporter = env.get_connector_unit(SaleStatusExporter)
    return exporter.run(binding_id, command)
