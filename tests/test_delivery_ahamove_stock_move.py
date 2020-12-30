# -*- coding: utf-8 -*-

from odoo.addons.delivery.tests.test_delivery_stock_move import StockMoveInvoice
from odoo.tests import tagged, Form

@tagged('post_install', '-at_install')
class AhamoveStockMoveInvoice(StockMoveInvoice):

    def setUp(self):
        super(AhamoveStockMoveInvoice, self).setUp()
        self.pricelist = self.env.ref('product.list0')
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
    def test_01_delivery_stock_move(self):

        # Test if the stored fields of stock moves are computed with invoice before delivery flow
        self.sale_prepaid = self.SaleOrder.create({
            'partner_id': self.partner_misa.id,
            'partner_invoice_id': self.partner_misa.id,
            'partner_shipping_id': self.partner_misa.id,
            'pricelist_id': self.pricelist_id.id,
            'order_line': [(0, 0, {
                'name': 'Cable Management Box',
                'product_id': self.product_cable_management_box.id,
                'product_uom_qty': 2,
                'product_uom': self.product_uom_unit.id,
                'price_unit': 750000.00,
            })]
        })

        # I add delivery cost in Sales order
        delivery_wizard = Form(self.env['choose.delivery.carrier'].with_context({
            'default_order_id': self.sale_prepaid.id,
            'default_carrier_id': self.ahamove_delivery.id,
        }))
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()

        # I confirm the SO
        self.sale_prepaid.action_confirm()
        self.sale_prepaid._create_invoices()

        # I check that the invoice was created
        self.assertEqual(len(self.sale_prepaid.invoice_ids),1, "Invoice not created")

        # I confirm the invoice
        self.invoice = self.sale_prepaid.invoice_ids
        self.invoice.post()

        # I pay the invoice
        self.invoice = self.sale_prepaid.invoice_ids
        self.invoice.post()
        self.journal = self.AccountJournal.search([('type', '=', 'cash'),
                                                   ('company_id', '=',
                                                    self.sale_prepaid.company_id.id)],
                                                  limit=1)

        register_payments = self.env['account.payment.register'].with_context(
            active_ids=self.invoice.ids).create({
            'journal_id': self.journal.id,
        })
        register_payments.create_payments()

        # Check the SO after paying the invoice
        self.assertNotEqual(self.sale_prepaid.invoice_count, 0, 'Order not invoiced')
        self.assertTrue(self.sale_prepaid.invoice_status == 'invoiced', 'Order is not invoiced')
        self.assertEqual(len(self.sale_prepaid.picking_ids), 1, 'pickings not generated')

        # Check the stock moves
        moves = self.sale_prepaid.picking_ids.move_lines
        for picking in self.sale_prepaid.picking_ids:
            with Form(picking) as p:
                with p.move_ids_without_package.edit(0) as line:
                    line.reserved_availability = 2
                    line.quantity_done = 2
        self.assertEqual(moves[0].product_qty, 2, 'wrong product_qty')


        # Ship
        self.picking = self.sale_prepaid.picking_ids.action_done()
        self.sale_prepaid.picking_ids.button_validate()

        # Check the tracking reference is populated
        self.assertNotEqual(self.sale_prepaid.picking_ids.carrier_tracking_ref, False, 'Tracking reference '
                                                                            'not '
                                                                      'found')
        self.assertNotEqual(self.sale_prepaid.picking_ids.carrier_tracking_url, False, 'Tracking url not found')

        # I cancel shipment
        self.picking.cancel_shipment()
        self.assertEqual(self.picking.carrier_tracking_ref, False, 'Shipment not cancelled')
        self.assertEqual(self.picking.carrier_tracking_url, False, 'Shipment data no cleared '
                                                                   'after being cancelled')




