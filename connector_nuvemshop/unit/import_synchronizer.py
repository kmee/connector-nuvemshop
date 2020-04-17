# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from openerp import fields, _
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.unit.synchronizer import Importer
from openerp.addons.connector.exception import IDMissingInBackend
from ..connector import get_environment
from ..related_action import link
from datetime import datetime
_logger = logging.getLogger(__name__)


class NuvemshopImporter(Importer):

    """ Base importer for NuvemshopCommerce """

    _parent_field = False

    def __init__(self, connector_env):
        """
        :param connector_env: current environment (backend, session, ...)
        :type connector_env: :class:`connector.connector.ConnectorEnvironment`
        """
        super(NuvemshopImporter, self).__init__(connector_env)
        self.nuvemshop_id = None
        self.nuvemshop_record = None

    def _get_nuvemshop_data(self):
        """ Return the raw NuvemshopCommerce data for ``self.nuvemshop_id`` """
        return self.backend_adapter.read(self.nuvemshop_id)

    def _before_import(self):
        """ Hook called before the import, when we have the NuvemshopCommerce
        data"""

    def _is_uptodate(self, binding):
        """Return True if the import should be skipped because
        it is already up-to-date in OpenERP"""
        NUVEMSHOP_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
        dt_fmt = NUVEMSHOP_DATETIME_FORMAT
        assert self.nuvemshop_record
        if not self.nuvemshop_record:
            return  # no update date on NuvemshopCommerce, always import it.
        if not binding:
            return  # it does not exist so it should not be skipped
        sync = binding.sync_date
        if not sync:
            return
        from_string = fields.Datetime.from_string
        sync_date = from_string(sync)
        self.nuvemshop_record['updated_at'] = {}
        self.nuvemshop_record['updated_at'] = {'to': datetime.now().strftime(dt_fmt)}
        nuvemshop_date = from_string(self.nuvemshop_record['updated_at']['to'])
        # if the last synchronization date is greater than the last
        # update in nuvemshop, we skip the import.
        # Important: at the beginning of the exporters flows, we have to
        # check if the nuvemshop_date is more recent than the sync_date
        # and if so, schedule a new import. If we don't do that, we'll
        # miss changes done in NuvemshopCommerce
        return nuvemshop_date < sync_date

    def _import_dependency(self, nuvemshop_id, binding_model,
                           importer_class=None, always=False):
        """ Import a dependency.

        The importer class is a class or subclass of
        :class:`NuvemshopImporter`. A specific class can be defined.

        :param nuvemshop_id: id of the related binding to import
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param importer_cls: :class:`openerp.addons.connector.\
                                     connector.ConnectorUnit`
                             class or parent class to use for the export.
                             By default: NuvemshopImporter
        :type importer_cls: :class:`openerp.addons.connector.\
                                    connector.MetaConnectorUnit`
        :param always: if True, the record is updated even if it already
                       exists, note that it is still skipped if it has
                       not been modified on NuvemshopCommerce since the last
                       update. When False, it will import it only when
                       it does not yet exist.
        :type always: boolean
        """
        if not nuvemshop_id:
            return
        if importer_class is None:
            importer_class = NuvemshopImporter
        binder = self.binder_for(binding_model)
        if always or binder.to_openerp(nuvemshop_id) is None:
            importer = self.unit_for(importer_class, model=binding_model)
            importer.run(nuvemshop_id)

    def _import_dependencies(self):
        """ Import the dependencies for the record

        Import of dependencies can be done manually or by calling
        :meth:`_import_dependency` for each dependency.
        """
        if self._parent_field:
            self._import_parent()

    def _import_parent(self):
        parent_id = self.nuvemshop_record.get(self._parent_field)
        if parent_id:
            if self.binder.to_openerp(parent_id) is None:
                importer = self.unit_for(NuvemshopImporter)
                importer.run(parent_id)

    def _map_data(self):
        """ Returns an instance of
        :py:class:`~openerp.addons.connector.unit.mapper.MapRecord`

        """
        return self.mapper.map_record(self.nuvemshop_record)

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``_create`` or
        ``_update`` if some fields are missing or invalid.

        Raise `InvalidDataError`
        """
        return

    def _must_skip(self):
        """ Hook called right after we read the data from the backend.

        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).

        If it returns None, the import will continue normally.

        :returns: None | str | unicode
        """
        return

    def _get_binding(self):
        return self.binder.to_openerp(self.nuvemshop_id, browse=True)

    def _create_data(self, map_record, **kwargs):
        return map_record.values(for_create=True, **kwargs)

    def _create(self, data):
        """ Create the OpenERP record """
        # special check on data before import
        self._validate_data(data)
        model = self.model.with_context(connector_no_export=True)
        model = str(model).split('()')[0]
        binding = self.env[model].create(data)
        _logger.debug('%d created from nuvemshop %s', binding, self.nuvemshop_id)
        return binding

    def _update_data(self, map_record, **kwargs):
        return map_record.values(**kwargs)

    def _update(self, binding, data):
        """ Update an OpenERP record """
        # special check on data before import
        self._validate_data(data)
        binding.with_context(connector_no_export=True).write(data)
        _logger.debug('%d updated from nuvemshop %s', binding, self.nuvemshop_id)
        return

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

    def run(self, nuvemshop_id, force=False):
        """ Run the synchronization

        :param nuvemshop_id: identifier of the record on NuvemshopCommerce
        """
        self.nuvemshop_id = nuvemshop_id
        try:
            self.nuvemshop_record = self._get_nuvemshop_data()
        except IDMissingInBackend:
            return _('Record does no longer exist in NuvemshopCommerce')

        skip = self._must_skip()
        if skip:
            return skip

        binding = self._get_binding()
        if not force and self._is_uptodate(binding):
            return _('Already up-to-date.')
        self._before_import()

        # import the missing linked resources
        self._import_dependencies()

        map_record = self._map_data()

        if binding:
            record = self._update_data(map_record)
            self._update(binding, record)
        else:
            record = self._create_data(map_record)
            binding = self._create(record)
        self.binder.bind(self.nuvemshop_id, binding)

        self._after_import(binding)


NuvemshopImportSynchronizer = NuvemshopImporter


class BatchImporter(Importer):

    """ The role of a BatchImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    def run(self, filters=None):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search(filters)
        for record_id in record_ids:
            self._import_record(record_id)

    def _import_record(self, record_id):
        """ Import a record directly or delay the import of the record.

        Method to implement in sub-classes.
        """
        raise NotImplementedError


BatchImportSynchronizer = BatchImporter


class DirectBatchImporter(BatchImporter):

    """ Import the records directly, without delaying the jobs. """
    _model_name = None

    def _import_record(self, record_id):
        """ Import the record directly """
        import_record(self.session,
                      self.model._name,
                      self.backend_record.id,
                      record_id)


DirectBatchImport = DirectBatchImporter


class DelayedBatchImporter(BatchImporter):

    """ Delay import of the records """
    _model_name = None

    def _import_record(self, record_id, **kwargs):
        """ Delay the import of the records"""
        import_record.delay(self.session,
                            self.model._name,
                            self.backend_record.id,
                            record_id,
                            **kwargs)


DelayedBatchImport = DelayedBatchImporter


@related_action(action=link)
@job(default_channel='root.nuvemshop')
def import_record(session, model_name, backend_id, nuvemshop_id, force=False):
    """ Import a record from Nuvemshop """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(NuvemshopImporter)
    importer.run(nuvemshop_id, force=force)