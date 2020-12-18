# -*- coding: utf-8 -*-
# from odoo import http


# class DeliveryAhamove(http.Controller):
#     @http.route('/delivery_ahamove/delivery_ahamove/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/delivery_ahamove/delivery_ahamove/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('delivery_ahamove.listing', {
#             'root': '/delivery_ahamove/delivery_ahamove',
#             'objects': http.request.env['delivery_ahamove.delivery_ahamove'].search([]),
#         })

#     @http.route('/delivery_ahamove/delivery_ahamove/objects/<model("delivery_ahamove.delivery_ahamove"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('delivery_ahamove.object', {
#             'object': obj
#         })
