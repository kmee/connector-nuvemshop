# -*- coding: utf-8 -*-
# Copyright (C) 2020  Daniel Sadamo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from ..sale_order.exporter import export_state_change
import logging

from openerp.addons.connector_ecommerce.event import (
    on_picking_out_done,
    on_tracking_number_added
)

_logger = logging.getLogger(__name__)


@on_tracking_number_added
def delay_export_tracking_number(session, model_name, record_id):
    """
    Call a job to export the tracking number to a existing picking that
    must be in done state.
    """
    picking = session.env[model_name].browse(record_id)
    sale = picking.sale_id
    if picking.state != 'done':
        return
    if not sale:
        return
    data = {
        'shipping_tracking_number': picking.carrier_tracking_ref,
        'shipping_tracking_url': picking.shipping_tracking_url
    }
    for nuvemshop_sale in sale.nuvemshop_bind_ids:
        export_state_change.delay(
            session, 'nuvemshop.sale.order', nuvemshop_sale.id, command='fullfill',
            data=data
        )


@on_picking_out_done
def picking_out_done(session, model_name, record_id, picking_method):
    picking = session.env[model_name].browse(record_id)
    sale = picking.sale_id
    if not sale:
        return
    for nuvemshop_sale in sale.nuvemshop_bind_ids:
        export_state_change.delay(
            session, 'nuvemshop.sale.order', nuvemshop_sale.id, command='pack',
        )
