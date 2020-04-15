# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields
from openerp.addons.connector.connector import (ConnectorEnvironment,
                                                install_in_connector)
from openerp.addons.connector.checkpoint import checkpoint

install_in_connector()


def get_environment(session, model_name, backend_id):
    """ Create an environment to work with.  """
    backend_record = session.env['nuvemshop.backend'].browse(backend_id)
    env = ConnectorEnvironment(backend_record, session, model_name)
    lang = backend_record.default_lang_id
    lang_code = lang.code if lang else 'en_US'
    if lang_code == session.context.get('lang'):
        return env
    else:
        with env.session.change_context(lang=lang_code):
            return env


class NuvemShopBinding(models.AbstractModel):
    """ Abstract Model for the Bindigs.

    All the models used as bindings between nuvemshop and OpenERP
    (``nuvemshop.res.partner``, ``nuvemshop.product.product``, ...) should
    ``_inherit`` it.
    """
    _name = 'nuvemshop.binding'
    _inherit = 'external.binding'
    _description = 'Nuvemshop Binding (abstract)'

    # openerp_id = openerp-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='nuvemshop.backend',
        string='Nuvemshop Backend',
        required=True,
        ondelete='restrict',
    )
    nuvemshop_id = fields.Char(string='ID on NuvemShop')

    _sql_constraints = [
        ('nuvemshop_uniq', 'unique(backend_id, nuvemshop_id)',
         'A binding already exists with the same Nuvem Shop ID.'),
    ]


def add_checkpoint(session, model_name, record_id, backend_id):
    """ Add a row in the model ``connector.checkpoint`` for a record,
    meaning it has to be reviewed by a user.

    :param session: current session
    :type session: :class:`openerp.addons.connector.session.ConnectorSession`
    :param model_name: name of the model of the record to be reviewed
    :type model_name: str
    :param record_id: ID of the record to be reviewed
    :type record_id: int
    :param backend_id: ID of the WooCommerce Backend
    :type backend_id: int
    """
    return checkpoint.add_checkpoint(session, model_name, record_id,
                                     'nuvemshop.backend', backend_id)
