# -*- coding: utf-8 -*-
# Copyright (C) 2020  Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import functools
from openerp import exceptions, _
from openerp.addons.connector import related_action
from .connector import get_environment
from .unit.backend_adapter import GenericAdapter
from .unit.binder import NuvemshopBinder

unwrap_binding = functools.partial(related_action.unwrap_binding,
                                   binder_class=NuvemshopBinder)


def link(session, job, backend_id_pos=2, nuvemshop_id_pos=3):
    """ Open a Nuvem Shop URL on the admin page to view/edit the record
    related to the job.
    """
    binding_model = job.args[0]
    # shift one to the left because session is not in job.args
    backend_id = job.args[backend_id_pos - 1]
    nuvemshop_id = job.args[nuvemshop_id_pos - 1]
    env = get_environment(session, binding_model, backend_id)
    adapter = env.get_connector_unit(GenericAdapter)
    try:
        url = adapter.admin_url(nuvemshop_id)
    except ValueError:
        raise exceptions.Warning(
            _('No admin URL configured on the backend or '
              'no admin path is defined for this record.')
        )

    action = {
        'type': 'ir.actions.act_url',
        'target': 'new',
        'url': url,
    }
    return action
