# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AhamoveServiceType(models.Model):
    _name = 'delivery_ahamove.service_type'
    _description = 'service types provided by Ahamove'

    name = fields.Char(string='Service Type Name', required=True, translate=True, help='The name '
                                                                                       'of the '
                                                                                       'service '
                                                                                       'type')
    code = fields.Char(string='Service Code', required=True, help='The service code - Use for ' \
                                                               'calling ' \
                                                        'Ahamove '
                                                   'api\nYou can use this field for quick search')
    icon = fields.Binary(attachment=True)
    description = fields.Text('Description')

