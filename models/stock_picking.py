# -*- coding: utf-8 -*-

from odoo import fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shipping_status = fields.Char('Shipping Status', translate=True)

    def send_to_shipper(self):
        super(StockPicking, self).send_to_shipper()
        res = self.carrier_id.send_shipping(self)[0]
        if res['status']:
            self.shipping_status = res['status']