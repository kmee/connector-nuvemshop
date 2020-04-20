# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from contextlib import closing, contextmanager

import openerp
from openerp import fields, _
from openerp.addons.connector.queue.job import job, related_action
from openerp.addons.connector.unit.synchronizer import Importer
from openerp.addons.connector.exception import IDMissingInBackend
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.connector import ConnectorUnit, Binder
from openerp.addons.connector.exception import (
    RetryableJobError,
    FailedJobError,
)

from ..backend import nuvemshop
from ..connector import get_environment
from ..related_action import link
from dateutil.parser.isoparser import isoparse

_logger = logging.getLogger(__name__)

RETRY_ON_ADVISORY_LOCK = 1  # seconds
RETRY_WHEN_CONCURRENT_DETECTED = 2  # seconds


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
        assert self.nuvemshop_record
        if not self.nuvemshop_record:
            return  # no update date on NuvemshopCommerce, always import it.
        if not binding:
            return  # it does not exist so it should not be skipped
        sync = binding.sync_date
        if not sync:
            return

        sync_date = fields.Datetime.from_string(sync)
        if isoparse(self.nuvemshop_record['updated_at']).replace(tzinfo=None) < sync_date:
            _logger.info('Already update: %s', self.nuvemshop_record)
            return True
        else:
            _logger.info('To update: %s', self.nuvemshop_record)
            return False

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

    @contextmanager
    def do_in_new_connector_env(self, model_name=None):
        """ Context manager that yields a new connector environment

        Using a new Odoo Environment thus a new PG transaction.

        This can be used to make a preemptive check in a new transaction,
        for instance to see if another transaction already made the work.
        """
        with openerp.api.Environment.manage():
            registry = openerp.modules.registry.RegistryManager.get(
                self.env.cr.dbname
            )
            with closing(registry.cursor()) as cr:
                try:
                    new_env = openerp.api.Environment(cr, self.env.uid,
                                                      self.env.context)
                    new_connector_session = ConnectorSession.from_env(new_env)
                    connector_env = self.connector_env.create_environment(
                        self.backend_record.with_env(new_env),
                        new_connector_session,
                        model_name or self.model._name,
                        connector_env=self.connector_env
                    )
                    yield connector_env
                except Exception as e:
                    cr.rollback()
                    raise
                else:
                    # Despite what pylint says, this a perfectly valid
                    # commit (in a new cursor). Disable the warning.
                    cr.commit()  # pylint: disable=invalid-commit

    def run(self, nuvemshop_id, **kwargs):
        """ Run the synchronization

        :param nuvemshop_id: identifier of the record on NuvemshopCommerce
        """
        self.nuvemshop_id = nuvemshop_id
        lock_name = 'import({}, {}, {}, {})'.format(
            self.backend_record._name,
            self.backend_record.id,
            self.model._name,
            self.nuvemshop_id,
        )
        # Keep a lock on this import until the transaction is committed
        self.advisory_lock_or_retry(lock_name, retry_seconds=RETRY_ON_ADVISORY_LOCK)

        try:
            if not self.nuvemshop_record:
                self.nuvemshop_record = self._get_nuvemshop_data()
        except IDMissingInBackend:
            return _('Record does no longer exist in NuvemshopCommerce')

        binding = self._get_binding()
        if not binding:
            with self.do_in_new_connector_env() as new_connector_env:
                binder = new_connector_env.get_connector_unit(Binder)
                if binder.to_openerp(self.nuvemshop_id):
                    raise RetryableJobError(
                        'Concurrent error. The job will be retried later',
                        seconds=RETRY_WHEN_CONCURRENT_DETECTED,
                        ignore_retry=True
                    )

        skip = self._must_skip()
        if skip:
            return skip

        if not kwargs.get('force') and self._is_uptodate(binding):
            return _('Already up-to-date.')

        self._import_dependencies()
        self._import(binding, **kwargs)

    def _import(self, binding, **kwargs):
        map_record = self._map_data()

        if binding:
            record = self._update_data(map_record)
            self._update(binding, record)
        else:
            record = self._create_data(map_record)
            binding = self._create(record)
        self.binder.bind(self.nuvemshop_id, binding)

        self._after_import(binding)


class TranslatableRecordImporter(NuvemshopImporter):
    """ Import one translatable record """
    _model_name = []
    _translatable_fields = {}
    _default_language = 'pt'

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super(TranslatableRecordImporter, self).__init__(environment)
        self.main_lang_data = None
        self.main_lang = None
        self.other_langs_data = None

    def find_each_language(self, record):
        languages = dict()
        languages[self._default_language] = {}

        # Get translated fields
        for field in self._translatable_fields[self.connector_env.model_name]:
            if isinstance(record[field], dict) and record[field].get(
                    self._default_language) is not None:
                languages[self._default_language][field] = \
                    record[field].get(self._default_language)
            else:
                languages[self._default_language][field] = \
                    record[field]

        # Get no translated fields
        for field in set(record.keys()) - set(
            self._translatable_fields[self.connector_env.model_name]):
            languages[self._default_language][field] = \
                record[field]

        return languages

    def _create_context(self):
        context = super(TranslatableRecordImporter, self)._create_context()
        if self.main_lang:
            context['lang'] = self.main_lang
        return context

    def _map_data(self):
        """ Returns an instance of
        :py:class:`~openerp.addons.connector.unit.mapper.MapRecord`

        """
        return self.mapper.map_record(self.main_lang_data)

    def _import(self, binding, **kwargs):
        """ Import the external record.

        Can be inherited to modify for instance the session
        (change current user, values in context, ...)

        """
        languages = self.find_each_language(self.nuvemshop_record)
        if not languages:
            raise FailedJobError(
                _('No language mapping defined. '
                  'Run "Synchronize base data".')
            )

        if self._default_language in languages:
            self.main_lang_data = languages[self._default_language]
            self.main_lang = self._default_language
            del languages[self._default_language]
        else:
            raise NotImplementedError

        self.other_langs_data = languages

        super(TranslatableRecordImporter, self)._import(binding)

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        for lang_code, lang_record in self.other_langs_data.iteritems():
            map_record = self.mapper.map_record(lang_record)
            binding.with_context(
                lang=lang_code,
                connector_no_export=True,
            ).write(map_record.values())


class BatchImporter(Importer):
    """ The role of a BatchImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """

    def run(self, filters=None):
        """ Run the synchronization """
        record_ids = self.backend_adapter.search(filters)
        _logger.info('search for nuvemshop %s returned %s', filters, record_ids)
        for record_id in record_ids:
            self._import_record(record_id['id'])

    def _import_record(self, record_id):
        """ Import a record directly or delay the import of the record.

        Method to implement in sub-classes.
        """
        raise NotImplementedError

@nuvemshop
class DirectBatchImporter(BatchImporter):
    """ Import the records directly, without delaying the jobs. """
    _model_name = None

    def _import_record(self, record_id):
        """ Import the record directly """
        import_record(self.session,
                      self.model._name,
                      self.backend_record.id,
                      record_id)


@nuvemshop
class DelayedBatchImporter(BatchImporter):
    """ Delay import of the records """
    _model_name = ['nuvemshop.product.category']

    def _import_record(self, record_id, priority=None, **kwargs):
        """ Delay the import of the records"""
        import_record.delay(self.session,
                            self.model._name,
                            self.backend_record.id,
                            record_id,
                            **kwargs)


@related_action(action=link)
@job(default_channel='root.nuvemshop')
def import_record(session, model_name, backend_id, nuvemshop_id, force=False):
    """ Import a record from Nuvemshop """
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(NuvemshopImporter)
    importer.run(nuvemshop_id, force=force)


@job(default_channel='root.nuvemshop')
def import_batch_delayed(session, model_name, backend_id, filters=None):
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(DelayedBatchImporter)
    importer.run(filters=filters)


@job(default_channel='root.nuvemshop')
def import_batch_direct(session, model_name, backend_id, filters=None):
    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(DirectBatchImporter)
    importer.run(filters=filters)
