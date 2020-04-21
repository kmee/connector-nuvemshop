# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import _
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Deleter
from ..connector import get_environment


class NuvemshopDeleter(Deleter):
    """ Base deleter for Nuvemshop """

    _model_name = [
        'nuvemshop.product.category'
    ]

    def run(self, external_id):
        """ Run the synchronization, delete the record on Nuvemshop

        :param external_id: identifier of the record to delete
        """
        self.backend_adapter.delete(external_id)
        return _('Record %s deleted on Nuvemshop on resource %s') % (
            external_id)


@job(default_channel='root.nuvemshop')
def delete_record(session, model_name, backend_id, nuvemshop_id):
    """ Delete a record on Nuvemshop """
    env = get_environment(session, model_name, backend_id)
    deleter = env.get_connector_unit(NuvemshopDeleter)
    return deleter.run(nuvemshop_id)


def delay_delete_record(session, model_name, record_id, priority=30):
    if session.context.get('connector_no_export'):
        return
    delete_record.delay(session, model_name, record_id, priority=priority)


def delay_delete_all_bindings(session, model_name, record_id, priority=30):
    if session.context.get('connector_no_export'):
        return
    model = session.env[model_name]
    record = model.browse(record_id)
    for binding in record.nuvemshop_bind_ids:
        delete_record.delay(session, binding._model._name, backend_id=binding.backend_id.id, nuvemshop_id=binding.nuvemshop_id,priority=priority)
