# -*- coding: utf-8 -*-

from datetime import datetime
import json
import logging

import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

TIMEOUT = 20
AHAMOVE_API_BASE_URL = 'https://apistg.ahamove.com/'

class Ahamove(models.Model):
    _description = "Ahamove Shipping Method"
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('ahamove', 'Ahamove')])
    service_type = fields.Many2one('delivery_ahamove.service_type')

    @api.model
    def _do_request(self, preuri, uri, params={}, headers={}, type='POST'):
        """
        Execute the request to Ahamove API.
        :param uri: the url to contact
        :param params: parameters dictionary
        :param headers: headers of the request
        :param type: the method to use to make the request
        :param preuri: pre url to prepend to param uri
        :return: a tuple ('HTTP_CODE', 'HTTP_RESPONSE')
        """
        _logger.debug("Preuri: %s - Uri: %s - Type: %s - Headers: %s - Params: %s !", (preuri, uri,
                                                                                       type,
                                                                                  headers,
                                                                          params))

        if type.upper() in 'GET':
            res = requests.request(type.lower(), preuri + uri, params=params, timeout=TIMEOUT)
            _logger.debug("URL: %s", res.url)
        elif type.upper() in 'POST':
            res = requests.request(type.lower(), preuri + uri, data=params, headers=headers,
                                       timeout=TIMEOUT)
            _logger.debug("URL: %s", res.url)
        else:
            raise Exception(_('Method not supported [%s] not in [GET or POST]') % (type))
        return res

    def _generate_data_from_order(self, order):
        token_ahamove = self.env['ir.config_parameter'].sudo().get_param('ahamove_api_token', default='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhaGEiLCJ0eXAiOiJ1c2VyIiwiY2lkIjoiODQ4Mzg0Mzk0ODMiLCJzdGF0dXMiOiJPTkxJTkUiLCJlb2MiOm51bGwsIm5vYyI6IlwiUGhhbSBUaGkgTmdvYyBNYWlcIiIsImN0eSI6IkhBTiIsImFjY291bnRfc3RhdHVzIjoiQUNUSVZBVEVEIiwiZXhwIjoxNjA4NzE1NzUyLCJwYXJ0bmVyIjoiYXJyb3doaXRlY2gifQ.uTDVjsMfx6aqhh-k7nVo-hGyBzklGH0ZZ3L_QnnA2-M')
        path_to = {
            'address': '%s, %s' % (order.partner_id.street, order.partner_id.city),
            'name': order.partner_id.name,
            'mobile': order.partner_id.mobile
        }
        sending_from = order.warehouse_id.partner_id
        path_from = {
            'address': '%s, %s' % (sending_from.street, sending_from.city)
        }
        return {
            'token': token_ahamove,
            'order_time': 0,
            'path': [path_from, path_to],
            'services': [{'_id': self.service_type.code}],
            'requests': [],
            'payment_method': 'CASH',
        }

    def _generate_data_from_picking(self, picking):
        order = self.env['sale.order'].search([('name', '=', picking.origin)])
        data = self._generate_data_from_order(order[0])
        services = data.pop('services')
        data['service_id'] = services[0]['_id']
        data['requests'] = []
        data['items'] = []
        data['order_time'] = 0
        return data

    def ahamove_rate_shipment(self, order):
        """
        Get estimated shipping price from Ahamove
        :param order: record of sale.order
        :return dict: {'success': boolean,
                       'price': a float,
                       'error_message': a string containing an error message,
                       'warning_message': a string containing a warning message}
        """
        uri = 'v2/order/estimated_fee'
        headers = {'Content-Type': 'application/json'}
        data_json = json.dumps(self._generate_data_from_order(order))
        try:
            res = self._do_request(AHAMOVE_API_BASE_URL, uri, data_json, headers,
                                   type='POST')
            _logger.debug("Response: %s", res.text)
            res.raise_for_status()
            return {
                'success': True,
                'price': res.json()[0]['total_price'],
            }
        except requests.HTTPError as e:
            try:
                response = e.response.json()
                error = response.get('error', {}).get('message')
            except Exception:
                error = None
            if not error:
                raise e
            message = _('The order "%s" cannot be estimated because of the following error: %s') % (
                order.name, error
            )
            raise UserError(message)

    def ahamove_send_shipping(self, pickings):
        """
        Send the package to the service provide
        :param pickings: A recordset of pickings
        :return list: A list of dictionaries (one per picking) containing of the form:
            {'exact_price': price,
             'tracking_number': number}
        """
        uri = 'v1/order/create'
        headers = {'Accept': '*/*', 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        result = []
        for picking in pickings:
            data_json = json.dumps(self._generate_data_from_picking(picking))
            try:
                res = self._do_request(AHAMOVE_API_BASE_URL, uri, data_json, headers, type='POST')
                _logger.debug("Response: %s", res.text)
                res.raise_for_status()
                result.append({'exact_price': res.json()['order']['total_pay'],
                               'tracking_number': res.json()['shared_link']})
            except requests.HTTPError as e:
                try:
                    response = e.response.json()
                    error = response.get('error', {}).get('message')
                except Exception:
                    error = None
                if not error:
                    raise e
                message = _('The shipment %s cannot be created because of the following error: '
                            '%s') % (picking.name, error)
                raise UserError(message)
        return result


