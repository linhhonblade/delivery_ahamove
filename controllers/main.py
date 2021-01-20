# -*- coding: utf-8 -*-

import logging
import json

from odoo import http

_logger = logging.getLogger(__name__)
class AhamoveController(http.Controller):
    @http.route('/ahamove/update_ahamove_status/', type='json', auth='public', methods=['POST'], \
                                                                                csrf=False)
    def update_ahamove_status(self):
        _logger.debug('CONNECTED TO ODOO')

        # data is a dictionary
        data = http.request.jsonrequest
        _logger.debug(data)
        # Find the picking attached to the shipping order
        if not data['_id'] and data['status']:
            http.Response.status = "400 Bad Request"
        picking_sum = http.request.env['stock.picking'].sudo().search_count([(
            'carrier_tracking_ref', '=', data['_id'])])
        if picking_sum == 0:
            _logger.debug("Order Not Found")
            http.Response.status = "404 Order not found"
        pickings = http.request.env['stock.picking'].sudo().search([('carrier_tracking_ref', '=',
                                                              data['_id'])])
        _logger.debug("Update Shipping Status %s", )
        for picking in pickings:
            _logger.debug(picking.shipping_status)
            picking.shipping_status = data['status']
            _logger.debug(picking.shipping_status)
        return '{"response": "OK"}'
