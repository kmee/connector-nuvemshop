# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from dateutil.parser.isoparser import isoparse
from openerp import _, exceptions, fields
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.queue.job import related_action
from openerp.addons.connector.unit.synchronizer import Exporter
from openerp.addons.connector.exception import FailedJobError

from .mapper import TranslationNuvemshopExportMapper
from ..connector import get_environment

_logger = logging.getLogger(__name__)

# Exporters for Nuvemshop.
# In addition to its export job, an exporter has to:
# * check in Nuvemshop if the record has been updated more recently than the
#  last sync date and if yes, delay an import
# * call the ``bind`` method of the binder to update the last sync date

def _date_to_odoo(date):
    clean_date = isoparse(date).replace(tzinfo=None)
    new_date = fields.Datetime.to_string(clean_date)
    return new_date


class NuvemshopBaseExporter(Exporter):
    """ Base exporter for Nuvemshop """

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(NuvemshopBaseExporter, self).__init__(environment)
        self.binding_id = None
        self.nuvemshop_id = None

    def _get_openerp_data(self):
        """ Return the raw OpenERP data for ``self.binding_id`` """
        return self.env[self.model._name].browse(self.binding_id)

    def run(self, binding_id, *args, **kwargs):
        """ Run the synchronization

        :param binding_id: identifier of the binding record to export
        """
        self.binding_id = binding_id
        self.erp_record = self._get_openerp_data()

        self.nuvemshop_id = self.binder.to_backend(self.binding_id)
        result = self._run(*args, **kwargs)

        self.binder.bind(self.nuvemshop_id, self.binding_id)
        return result

    def _run(self):
        """ Flow of the synchronization, implemented in inherited classes"""
        raise NotImplementedError


class NuvemshopExporter(NuvemshopBaseExporter):
    """ A common flow for the exports to Nuvemshop """

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(NuvemshopExporter, self).__init__(environment)
        self.erp_record = None
        self.nuvemshop_record = None

    def _has_to_skip(self):
        """ Return True if the export can be skipped """
        return False

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        return

    def _map_data(self, fields=None):
        """ Convert the external record to Odoo """
        self.mapper.map_record(self.erp_record)

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``Model.create`` or
        ``Model.update`` if some fields are missing

        Raise `InvalidDataError`
        """
        return

    def _after_export(self):
        """Create records of dependants nuvemshop objects"""
        return

    def _create(self, data):
        """ Create the Nuvemshop record """
        nuvemshop_record = self.backend_adapter.create(data)
        return nuvemshop_record

    def _update(self, data):
        """ Update an Nuvemshop record """
        assert self.nuvemshop_id
        return self.backend_adapter.write(self.nuvemshop_id, data)

    def _update_erp_record(self):
        self.nuvemshop_id = self.nuvemshop_record.get('id')
        self.erp_record.write({
            'created_at': _date_to_odoo(
                 self.nuvemshop_record.get('created_at')),
            'updated_at': _date_to_odoo(
                self.nuvemshop_record.get('updated_at'))
        })

    def _run(self, fields=None):
        """ Flow of the synchronization, implemented in inherited classes"""
        assert self.binding_id
        assert self.erp_record

        # should be created with all the fields
        if not self.nuvemshop_id:
            fields = None

        if self._has_to_skip():
            return

        self.erp_record = self.erp_record.with_context(
            lang=self.backend_record.default_lang_id.code
        )
        # export the missing linked resources
        self._export_dependencies()
        map_record = self.mapper.map_record(self.erp_record)

        if self.nuvemshop_id:
            record = map_record.values(fields=fields)
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            try:
                self.nuvemshop_record = self._update(record)
            except:
                raise FailedJobError
            self._update_erp_record()
        else:
            record = map_record.values(for_create=True)
            if fields is None:
                fields = {}
            record.update(fields)
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            try:
                self.nuvemshop_record = self._create(record)
            except:
                raise FailedJobError
            self._update_erp_record()
            if self.nuvemshop_id == 0:
                raise exceptions.Warning(
                    _("Record on Nuvemshop have not been created"))
        self._after_export()
        message = _('Record exported with ID %s on Nuvemshop.')
        return message % self.nuvemshop_id


class TranslationNuvemshopExporter(NuvemshopExporter):

    @property
    def mapper(self):
        if self._mapper is None:
            self._mapper = self.connector_env.get_connector_unit(
                TranslationNuvemshopExportMapper)
        return self._mapper

    def _map_data(self, fields=None):
        """ Convert the external record to OpenERP """
        self.mapper.convert(self.get_record_by_lang(), fields=fields)

    def get_record_by_lang(self, record_id):
        # get the backend's languages
        languages = self.backend_record.language_ids
        records = {}
        # for each languages:
        for language in languages:
            # get the translated record
            record = self.model.with_context(
                lang=language['code']).browse(record_id)
            # put it in the dict
            records[language] = record
        return records


def related_action_record(session, job):
    binding_model = job.args[0]
    binding_id = job.args[1]
    record = session.env[binding_model].browse(binding_id)
    odoo_name = record.openerp_id._name

    action = {
        'name': _(odoo_name),
        'type': 'ir.actions.act_window',
        'res_model': odoo_name,
        'view_type': 'form',
        'view_mode': 'form',
        'res_id': record.openerp_id.id,
    }
    return action


@job(default_channel='root.nuvemshop')
@related_action(action=related_action_record)
def export_record(session, model_name, binding_id, fields=None):
    """ Export a record on Nuvemshop """
    record = session.env[model_name].browse(binding_id)
    env = get_environment(session, model_name, record.backend_id.id)
    exporter = env.get_connector_unit(NuvemshopExporter)
    return exporter.run(binding_id, fields=fields)

def delay_export(session, model_name, record_id, fields=None, priority=20):
    """ Delay a job which export a binding record.

    (A binding record being a ``external.res.partner``,
    ``external.product.product``, ...)
    """
    if session.context.get('connector_no_export'):
        return
    export_record.delay(
        session, model_name, record_id, fields=fields, priority=priority)


def delay_export_all_bindings(
        session, model_name, record_id, fields=None, priority=20):
    """ Delay a job which export all the bindings of a record.

    In this case, it is called on records of normal models and will delay
    the export for all the bindings.
    """
    if session.context.get('connector_no_export'):
        return
    model = session.env[model_name]
    record = model.browse(record_id)
    for binding in record.nuvemshop_bind_ids:
        export_record.delay(session, binding._model._name, binding.id,
                            fields=fields, priority=priority)
