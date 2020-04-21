# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from openerp import models

from openerp.addons.connector.unit.mapper import ExportMapper
from openerp.addons.connector.exception import MappingError

LANG_ODOO_NUVEMSHOP = {
    'en_US': 'en',
    'pt_BR': 'pt',
    'es_ES': 'es',
}
_logger = logging.getLogger(__name__)

# to be used until the one in OCA/connector is fixed, the issue being
# that it returns a recordset instead of an id
# see https://github.com/OCA/connector/pull/194

class NuvemshopExportMapper(ExportMapper):

    def _map_direct(self, record, from_attr, to_attr):
        res = super(NuvemshopExportMapper, self)._map_direct(record,
                                                              from_attr,
                                                              to_attr) or ''
        column = self.model._all_columns[from_attr].column
        if column._type == 'boolean':
            return res and 1 or 0
        elif column._type == 'float':
            res = str(res)
        return res


class TranslationNuvemshopExportMapper(NuvemshopExportMapper):

    def convert_languages(self, records_by_language, translatable_fields):
        res = {}
        for field in [x[0] for x in self.direct]:
            if field in translatable_fields:
                res[field] = {}
                for language_id in self.backend_record.language_ids:
                    res[field][LANG_ODOO_NUVEMSHOP[language_id.code]] = records_by_language[language_id][field]
            else:
                res[field] = records_by_language[self.backend_record.default_lang_id][field]
        return res
