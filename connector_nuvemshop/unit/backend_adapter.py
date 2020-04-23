# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from urlparse import urljoin

from tiendanube.client import NubeClient
from openerp.addons.connector.unit.backend_adapter import CRUDAdapter

_logger = logging.getLogger(__name__)

recorder = {}


def call_to_key(method, arguments):
    """ Used to 'freeze' the method and arguments of a call to NuvemshopCommerce
    so they can be hashable; they will be stored in a dict.

    Used in both the recorder and the tests.
    """
    def freeze(arg):
        if isinstance(arg, dict):
            items = dict((key, freeze(value)) for key, value
                         in arg.iteritems())
            return frozenset(items.iteritems())
        elif isinstance(arg, list):
            return tuple([freeze(item) for item in arg])
        else:
            return arg

    new_args = []
    for arg in arguments:
        new_args.append(freeze(arg))
    return (method, tuple(new_args))


def record(method, arguments, result):
    """ Utility function which can be used to record test data
    during synchronisations. Call it from NuvemshopCRUDAdapter._call

    Then ``output_recorder`` can be used to write the data recorded
    to a file.
    """
    recorder[call_to_key(method, arguments)] = result


def output_recorder(filename):
    import pprint
    with open(filename, 'w') as f:
        pprint.pprint(recorder, f)
    _logger.debug('recorder written to file %s', filename)


class NuvemshopLocation(object):

    def __init__(self, location, store_id, access_token):
        self._location = location
        self.store_id = store_id
        self.access_token = access_token

    @property
    def location(self):
        if self._location == u'pt_BR':
            return "pt"
        return self._location


class NuvemShopWebServiceImage(object):

    def __init__(self, _api_url, webservice_key):
        self._api_url = _api_url
        self.webservice_key = webservice_key

    def get_image(self, resource, resource_id=None, image_id=None):
        full_url = self._api_url + 'images/' + resource
        if resource_id is not None:
            full_url += "/%s" % (resource_id,)
            if image_id is not None:
                full_url += "/%s" % (image_id)
        response = self._execute(full_url, 'GET')
        if response.content:
            image_content = base64.b64encode(response.content)
        else:
            image_content = ''

        record = {
            'type': response.headers['content-type'],
            'content': image_content,
            'id_' + resource[:-1]: resource_id,
            'id_image': image_id,
        }
        record['full_public_url'] = self.get_image_public_url(record)
        return record


class NuvemshopCRUDAdapter(CRUDAdapter):

    """ External Records Adapter for nuvemshop """
    _model_name = None
    _nuvemshop_model = None

    def __init__(self, connector_env):
        super(NuvemshopCRUDAdapter, self).__init__(connector_env)

        backend = self.backend_record

        nuvemshop = NuvemshopLocation(
            location=backend.default_lang_id.code,
            store_id=backend.store_id,
            access_token=backend.access_token)

        self.nuvemshop = nuvemshop

        self.client = NubeClient(
            self.nuvemshop.access_token
        )
        self.store = self.client.get_store(
            self.nuvemshop.store_id
        )

    def admin_url(self, nuvemshop_id=False):
        """ Some models do can't be open with ids, if your model can overrite me!
        :param nuvemshop_id:
        :return:
        """
        return urljoin(self.backend_record.url, 'admin/' + self._nuvemshop_model)

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids """
        return self.store[self._nuvemshop_model].list(fields=['id'], filters=filters)

    def read(self, id, attributes=None):
        """ Returns the information of a record """
        return self.store[self._nuvemshop_model].get(id)

    def search_read(self, filters=None):
        """ Search records according to some criterias
        and returns their information"""
        raise NotImplementedError

    def create(self, data):
        """ Create a record on the external system """
        return self.store[self._nuvemshop_model].add(data)

    def write(self, id, data):
        """ Update records on the external system """
        data['id'] = id
        if not data.get('description'):
            data['description'] = ' '
        return self.store[self._nuvemshop_model].update(data)

    def delete(self, id):
        """ Delete a record on the external system """
        return self.store[self._nuvemshop_model].delete({'id': id})

GenericAdapter = NuvemshopCRUDAdapter
