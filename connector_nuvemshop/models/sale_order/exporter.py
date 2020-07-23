# -*- coding: utf-8 -*-
# Copyright (C) 2020  Daniel Sadamo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from openerp import _
from openerp.addons.connector.event import on_record_create, on_record_write
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.mapper import ImportMapper

from ...backend import nuvemshop
from ...connector import get_environment
from ...unit.exporter import NuvemshopExporter
from ...unit.importer import NuvemshopImporter
# from .importer import SaleOrderImportMapper

ORDER_COMMAND_MAPPING = {
    'draft': 'open',
    # 'manual': 'processing',
    'progress': 'open',
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
            if binding.status is not 'cancelled':
                with session.change_context(connector_no_export=True):
                    export_state_change.delay(
                        session,
                        'nuvemshop.sale.order',
                        binding.id,
                        command=ORDER_COMMAND_MAPPING[fields.get('state')]
                    )


@nuvemshop
class SaleStatusExporter(NuvemshopExporter):
    _model_name = ['nuvemshop.sale.order']

    def run(self, binding_id, command, data=None):
        nuvemshop_record = self.backend_adapter.sale_order_command(
            binding_id, command, data=data
        )
        if nuvemshop_record:
            mapper = self.connector_env.get_connector_unit(ImportMapper)
            importer = self.unit_for(NuvemshopImporter)
            binding = self.binder.to_openerp(binding_id)
            binding = binding.with_context(connector_no_export=True)
            map_record = mapper.map_record(nuvemshop_record)
            importer._update(binding, map_record.values())
            if nuvemshop_record.get('status') == 'cancelled':
                binding.canceled_in_backend = True


@job(default_channel='root.nuvemshop')
def export_state_change(session, model_name, binding_id, command, data=None):
    """ Change state of a sales order on Nuvemshop """
    binding = session.env[model_name].browse(binding_id)
    nuvemshop_id = binding.nuvemshop_id
    backend_id = binding.backend_id.id
    env = get_environment(session, model_name, backend_id)
    exporter = env.get_connector_unit(SaleStatusExporter)
    return exporter.run(nuvemshop_id, command, data=data)
