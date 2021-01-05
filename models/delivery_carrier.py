# -*- coding: utf-8 -*-

import logging

import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
DEFAULT_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhaGEiLCJ0eXAiOiJ1c2VyIiwiY2lkIjoiODQ4Mzg0Mzk0ODMiLCJzdGF0dXMiOiJPTkxJTkUiLCJlb2MiOm51bGwsIm5vYyI6IlwiUGhhbSBUaGkgTmdvYyBNYWlcIiIsImN0eSI6IkhBTiIsImFjY291bnRfc3RhdHVzIjoiQUNUSVZBVEVEIiwiZXhwIjoxNjA5MjExNDUzLCJwYXJ0bmVyIjoiYXJyb3doaXRlY2gifQ.wDMPf78V7xH3x74T1nRmnWME5Cquf5KsMXJLbLIpWKo'

class Ahamove(models.Model):
    _description = "Ahamove Shipping Method"
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('ahamove', 'Ahamove')])
    service_type = fields.Many2one('delivery_ahamove.service_type')
    AHAMOVE_API_BASE_URL = fields.Char(compute='_compute_ahamove_api_base_url')

    @api.depends('prod_environment')
    def _compute_ahamove_api_base_url(self):
        for carrier in self:
            if carrier.prod_environment:
                carrier.AHAMOVE_API_BASE_URL = 'https://api.ahamove.com/'
            else:
                carrier.AHAMOVE_API_BASE_URL = 'https://apistg.ahamove.com/'

    @api.onchange('prod_environment')
    def _on_change_prod_environment(self):
        if self.prod_environment:
            self.AHAMOVE_API_BASE_URL = 'https://api.ahamove.com/'
        else:
            self.AHAMOVE_API_BASE_URL = 'https://apistg.ahamove.com/'

    @api.model
    def _do_request(self, url, params, headers, type='POST'):
        """
        Execute the request to Ahamove API.
        :param url: the endpoint url
        :param params: parameters dictionary
        :param headers: headers of the request
        :param type: the method to use to make the request
        :return: a tuple ('HTTP_CODE', 'HTTP_RESPONSE')
        """
        _logger.debug("Preuri: %s - Url: %s - Type: %s - Headers: %s - Params: %s !",
                      (url, type, params))
        if type.upper() in 'GET':
            res = requests.get(url, params=params, headers=headers)
            _logger.debug("URL: %s", res.url)
        elif type.upper() in 'POST':
            res = requests.post(url, params=params, headers=headers)
            _logger.debug("URL: %s", res.url)
        return res

    def _generate_data_from_order(self, order):
        token_ahamove = self.env['ir.config_parameter'].sudo().get_param('ahamove_api_token',
                                                                         default=DEFAULT_TOKEN)
        sending_from = order.warehouse_id.partner_id
        path = '[{"address": "%s, %s"},{"address": "%s, %s", "name": "%s", "mobile": "%s"}]' % (
            sending_from.street, sending_from.city, order.partner_id.street,
            order.partner_id.city, order.partner_id.name, order.partner_id.mobile)
        _logger.debug("Path: %s", path)
        return {
            'token': token_ahamove,
            'order_time': 0,
            'path': path,
            'service_id': self.service_type.code,
            'requests': [],
            'payment_method': 'CASH',
        }

    def _generate_data_from_picking(self, picking):
        order = self.env['sale.order'].search([('name', '=', picking.origin)])
        data = self._generate_data_from_order(order[0])
        data['items'] = []
        _logger.debug("Data: %s", data)
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
        uri = 'v1/order/estimated_fee'
        headers = {
            'Accept': '*/*',
            'Cache-Control': 'no-cache'
        }
        payload = self._generate_data_from_order(order)
        try:
            res = self._do_request(self.AHAMOVE_API_BASE_URL + uri, payload, headers,
                                   type='POST')
            _logger.debug("Response: %s", res.text)
            res.raise_for_status()
            return {
                'success': True,
                'price': res.json()['total_price'],
            }
        except requests.HTTPError:
            response = res.json()
            if 'description' in response.keys():
                message = _('The order "%s" cannot be estimated because of the following error: %s') \
                      % (order.name, response['description'])
            else:
                message = _('The order "%s" cannot be estimated because of the following error: %s') \
                          % (order.name, response['title'])
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
        headers = {'Accept': '*/*', 'Cache-Control': 'no-cache'}
        result = []
        for picking in pickings:
            payload = self._generate_data_from_picking(picking)
            try:
                res = self._do_request(self.AHAMOVE_API_BASE_URL + uri, payload, headers,
                                       type='POST')
                _logger.debug("Response: %s", res.text)
                res.raise_for_status()
                result.append({'exact_price': res.json()['order']['total_pay'],
                               'tracking_number': res.json()['order_id']})
            except requests.HTTPError:
                response = res.json()
                description = response['description']
                if description:
                    message = _('The shipment %s cannot be created because of the following error: '
                            '%s') % (picking.name, description)
                else:
                    message = _('The shipment %s cannot be created because of the following error: '
                                '%s') % (picking.name, response['title'])
                raise UserError(message)

        return result

    def ahamove_get_tracking_link(self, picking):
        """Ask the tracking link to the service provider
        :param picking: record of stock.picking
        :return str: an URL containing the tracking link or False
        """

        uri = 'v1/order/shared_link'
        token_ahamove = self.env['ir.config_parameter'].sudo().get_param('ahamove_api_token',
                                                                         default=DEFAULT_TOKEN)
        payload = {
            'token': token_ahamove,
            'order_id': picking.carrier_tracking_ref
        }
        headers = {
            'Cache-Control': 'no-cache'
        }
        try:
            res = self._do_request(self.AHAMOVE_API_BASE_URL + uri, payload, headers, type='GET')
            _logger.debug("Response: %s", res.text)
            res.raise_for_status()
            return res.json()['shared_link']
        except requests.HTTPError:
            return False

    def ahamove_cancel_shipment(self, pickings):
        """
        Cancel a shipment
        :param pickings: a recordset of pickings
        """

        uri = 'v1/order/cancel'
        token_ahamove = self.env['ir.config_parameter'].sudo().get_param('ahamove_api_token',
                                                                         default=DEFAULT_TOKEN)
        headers = {
            'Cache-Control': 'no-cache'
        }
        for picking in pickings:
            payload = {
                'token': token_ahamove,
                'order_id': picking.carrier_tracking_ref,
                'comment': ''
            }
            try:
                res = self._do_request(self.AHAMOVE_API_BASE_URL + uri, payload, headers,
                                       type='GET')
                _logger.debug("Response: %s", res.text)
                res.raise_for_status()
            except requests.HTTPError:
                response = res.json()
                if response['description']:
                    message = _("Cannot cancel the picking %s due to the following error: %s") % \
                              (picking.name, response['description'])
                else:
                    message = _('The order "%s" cannot be estimated because of the following error: %s') % (
                                  picking.name, response['title']
                              )
                raise UserError(message)
