# -*- coding: utf-8 -*-

import logging

import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .ahamove_request import AhamoveRequest

_logger = logging.getLogger(__name__)

class Ahamove(models.Model):
    _description = "Ahamove Shipping Method"
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('ahamove', 'Ahamove')],
                                     ondelete={'ahamove': lambda records: record.write({
                                         'delivery_type': 'fixed'
                                     })})
    service_type = fields.Many2one('delivery_ahamove.service_type')
    def _generate_data_from_order(self, order):
        sending_from = order.warehouse_id.partner_id
        path = '[{"address": "%s, %s"},{"address": "%s, %s", "name": "%s", "mobile": "%s"}]' % (
            sending_from.street, sending_from.city, order.partner_id.street,
            order.partner_id.city, order.partner_id.name, order.partner_id.mobile)
        _logger.debug("Path: %s", path)
        return {
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
        ahamove_req = AhamoveRequest(self.prod_environment)
        try:
            res = ahamove_req.do_request(uri, payload, headers, type='POST')
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
             'tracking_number': number,
             'status': string}
        """
        uri = 'v1/order/create'
        headers = {'Accept': '*/*', 'Cache-Control': 'no-cache'}
        result = []
        ahamove_req = AhamoveRequest(self.prod_environment)
        for picking in pickings:
            payload = self._generate_data_from_picking(picking)
            try:
                res = ahamove_req.do_request(uri, payload, headers, type='POST')
                _logger.debug("Response: %s", res.text)
                res.raise_for_status()
                result.append({'exact_price': res.json()['order']['total_pay'],
                               'tracking_number': res.json()['order_id'],
                               'status': res.json()['status']})
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

        payload = {
            'order_id': picking.carrier_tracking_ref
        }
        headers = {
            'Cache-Control': 'no-cache'
        }
        ahamove_req = AhamoveRequest(self.prod_environment)
        try:
            res = ahamove_req.do_request(uri, payload, headers, type='GET')
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
        headers = {
            'Cache-Control': 'no-cache'
        }
        ahamove_req = AhamoveRequest(self.prod_environment)
        for picking in pickings:
            payload = {
                'order_id': picking.carrier_tracking_ref,
                'comment': ''
            }
            try:
                res = ahamove_req.do_request(uri, payload, headers, type='GET')
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

    @staticmethod
    def ahamove_get_avail_services(partner):
        """Get available services for partner location
            :param partner: A recordset of partner
            :return list: A list of service codes
        """
        uri = 'v1/order/service_types'
        # update partner lat and lng
        partner.geo_localize()
        payload = {
            'lat': partner.partner_latitude,
            'lng': partner.partner_longitude
        }
        headers = {
            'Cache-Control': 'no-cache'
        }
        result = []
        ahamove_req = AhamoveRequest(False, False)
        try:
            res = ahamove_req.do_request(uri, payload,
                               headers, type='GET')
            res.raise_for_status()
            for service in res.json():
                result.append(service['_id'])
            _logger.debug("Result list: %s", result)
        except requests.HTTPError:
            response = res.json()
            if response['description']:
                message = _("Cannot get list of services for the partner %s due to the following "
                            "error: %s") % (partner.name, response['description'])
            else:
                message = _("Cannot get list of services because of the following error: %s") % (
                    response['title'])
            raise UserError(message)
        return result

