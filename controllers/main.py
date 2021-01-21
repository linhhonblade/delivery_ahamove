# -*- coding: utf-8 -*-

import logging
import json

from odoo import http
from odoo import modules, api, SUPERUSER_ID

_logger = logging.getLogger(__name__)
class AhamoveController(http.Controller):
    @http.route('/ahamove/<dbname>/update_ahamove_status/', type='json', auth='public', methods=[
        'POST'], csrf=False)
    def update_ahamove_status(self, dbname, **kw):
        _logger.debug('CONNECTED TO ODOO')
        try:
            registry = modules.registry.Registry(dbname)
            with api.Environment.manage(), registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                # data is a dictionary
                data = http.request.jsonrequest
                _logger.debug(data)
                # Find the picking attached to the shipping order
                if not data['_id'] and data['status']:
                    _logger.debug("Not found _id and status")
                    http.Response.status = "400 Bad Request"
                picking_sum = env['stock.picking'].search_count([(
            'carrier_tracking_ref', '=', data['_id'])])
                _logger.debug("Search Count Result: %d", picking_sum)
                if picking_sum == 0:
                    _logger.debug("Order Not Found")
                    http.Response.status = "404 Order not found"
                pickings = env['stock.picking'].search([('carrier_tracking_ref', '=',
                                                              data['_id'])])
                _logger.debug("Update Shipping Status %s", )
                for picking in pickings:
                    _logger.debug(picking.shipping_status)
                    picking.shipping_status = data['status']
                    _logger.debug(picking.shipping_status)
        except Exception:
            _logger.debug("Failed to update")
            http.Response.status = "404 Not Found"
        return '{"response": "OK"}'
