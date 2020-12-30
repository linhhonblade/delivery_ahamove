# -*- coding: utf-8 -*-

from odoo.tests import common, Form

from odoo.addons.delivery.tests.test_delivery_cost import TestDeliveryCost

@common.tagged('post_install', '-at_install')
class TestDeliveryAPI(TestDeliveryCost):

    def setUp(self):
        super(TestDeliveryAPI, self).setUp()
        self.partner_misa = self.env.ref('delivery_ahamove.res_partner_misa')
        self.ahamove_delivery = self.env.ref('delivery_ahamove.ahamove_sieu_toc')

        # the tests hereunder assume all the price and address in VND,
        self.env.cr.execute(
            "UPDATE res_company SET currency_id = %s WHERE id = %s",
            [self.env.ref('base.VND').id, self.env.company.id]
        )
        self.pricelist.currency_id = self.env.ref('base.VND').id
        # The tests hereunder assume company location in vietnam
        self.env.cr.execute(
            "UPDATE res_partner SET street = %s, state_id = %s, country_id = %s WHERE id = %s",
            ['725 Hẻm số 7 Thành Thái, Phường 14, Quận 10',
             self.env.ref('base.state_vn_VN-SG').id,
             self.env.ref('base.vn').id,
             self.env.company.partner_id.id]
        )

    def test_00_delivery_cost(self):
        # In order to test Ahamove Carrier Cost
        # Create sales order with Ahamove Delivery Method

        self.sale_order_ahamove = self.SaleOrder.create({
            'partner_id': self.partner_misa.id,
            'partner_invoice_id': self.partner_misa.id,
            'partner_shipping_id': self.partner_misa.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [(0, 0, {
                'name': 'PC Assamble + 2GB RAM',
                'product_id': self.product_4.id,
                'product_uom_qty': 1,
                'product_uom': self.product_uom_unit.id,
                'price_unit': 750000.00,
            })],
        })

        self.product_something_cute = self.Product.create({
            'sale_ok': True,
            'list_price': 750000.00,
            'standard_price': 300000.00,
            'uom_id': self.product_uom_hour.id,
            'uom_po_id': self.product_uom_hour.id,
            'name': 'Cuteness',
            'categ_id': self.product_category.id,
            'type': 'product',
            'qty_available': 10.0
        })

        # I add delivery cost in Sale order
        delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context({
            'default_order_id': self.sale_order_ahamove.id,
            'default_carrier_id': self.ahamove_delivery.id
        }))
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.update_price()
        choose_delivery_carrier.button_confirm()

        # I check sales order after added delivery cost

        line = self.SaleOrderLine.search([('order_id', '=', self.sale_order_ahamove.id),
                                          ('product_id', '=', self.ahamove_delivery.product_id.id)])
        self.assertEqual(len(line), 1, "Delivery cost is not added")

        # I confirm the sales order
        self.sale_order_ahamove.action_confirm()

        # Check the stock moves
        self.picking = self.sale_order_ahamove.picking_ids[0]
        self.picking.action_done()
        self.picking.button_validate()

        # Check the tracking reference is populated
        self.assertNotEqual(self.picking.carrier_tracking_ref, False, 'Tracking reference not found')
        # self.assertNotEqual(self.picking.carrier_tracking_url, False, 'Tracking url not found')

        # I cancel shipment
        self.picking.cancel_shipment()
        self.assertEqual(self.picking.carrier_tracking_ref, False, 'Shipment not cancelled')
        self.assertEqual(self.picking.carrier_tracking_url, False, 'Shipment data no cleared '
                                                                   'after being cancelled')



