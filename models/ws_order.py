from odoo import models, fields, api, _, exceptions
import logging
import json
import requests
import re
from datetime import datetime

_logger = logging.getLogger(__name__)


class WsOrder(models.Model):
    _inherit = 'sale.order'
    payment_mode = fields.Selection(string="Payment mode",
                                    selection=[('VIREMENT', 'Virement'), ('CIB_ELDAHABIA', 'Carte de credit'),
                                               ('CASH_EN_DELIVERY', 'Cash')])
    order_state = fields.Selection(string="order states",
                                   selection=[('PAID_DELIVERED', 'Livrée'),
                                              ('CREATED', 'Créée'),
                                              ('WAITING_FOR_CLIENT', 'En attente du client'),
                                              ('NOT_PAID_IN_DELIVERY', 'En cours de livraison'),
                                              ('NOT_PAID_PREPARED', 'En préparation'),
                                              ('NOT_PAID', 'En attente'),
                                              ('CLIENT_NOT_RESPONDING', 'Client ne répond pas'),
                                              ('CONFIRMED', 'Confirmée'),
                                              ('NOT_PAID_NOT_DELIVERY', 'En attente du paiement'),
                                              ('PAID_NOT_DELIVERED', 'Payée'),
                                              ('PAID_FAILED_NOT_DELIVERED', 'Paiement échoué')])
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('validate', 'Validated'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    create_by = fields.Char('Created by', default='Odoo')
    headers = {"Content-Type": "application/json", "Accept": "application/json", "Catch-Control": "no-cache"}
    # url_quotation = "https://api.tekkeys.com/api/v1/odoo/orders/quotation"
    # url_order = "https://api.tekkeys.com/api/v1/odoo/orders/order"

    @api.model
    def create(self, vals):
        # RECEIVE ORDER/QUOTATION FROM WS
        if 'create_by' in vals:

            vals["date_order"] = datetime.strptime(vals["date_order"], '%d/%m/%y %H:%M:%S')
            if vals["validity_date"]:
                vals["validity_date"] = datetime.strptime(vals["validity_date"], '%d/%m/%y %H:%M:%S')
            vals["partner_id"] = self.env["res.partner"].search([("email", "=", vals["partner_id"])]).id

            # CLIENT ADDRESSES
            if 'delivery_address' in vals:
                # SEARCH FOR EXISTING DELIVERY ADDRESS & CREATE A NEW ONE IF NOT

                delivery_address = self.env["res.partner"].search(
                    ['&', ('street', 'ilike', vals['delivery_address']['street']), ('type', '=', 'delivery')])
                if delivery_address:
                    vals['partner_shipping_id'] = delivery_address.id
                    _logger.info('\n\n\n SHIPPING ADDRESS FOUND \n\n\n\n %s \n\n\n\n', vals['partner_shipping_id'])
                else:
                    vals['partner_shipping_id'] = self.env["res.partner"].create({'type': 'delivery',
                                                                                  'create_by': "ws",
                                                                                  'is_company': False,
                                                                                  'id': vals['partner_id'],
                                                                                  'name': vals['delivery_address'][
                                                                                      'name'],

                                                                                  'phone': vals['delivery_address'][
                                                                                      'phone'],
                                                                                  'street': vals['delivery_address'][
                                                                                      'street'],
                                                                                  'zip': vals['delivery_address'][
                                                                                      'zip'],
                                                                                  'city': vals['delivery_address'][
                                                                                      'city']}).id
                    _logger.info('\n\n\n NEW SHIPPING ADDRESS FOUND \n\n\n\n %s \n\n\n\n', vals['partner_shipping_id'])

            if 'invoice_address' in vals:
                address_parent_id = self.env["res.partner"].search(
                    [('id', '=', vals['partner_id'])]).parent_id

                # SEARCH FOR EXISTING INVOICE ADDRESS & CREATE A NEW ONE IF NOT
                invoice_address = self.env["res.partner"].search(
                    ['&', ('street', 'ilike', vals['invoice_address']['street']), ('type', '=', 'invoice')])

                if invoice_address:
                    vals['partner_invoice_id'] = invoice_address.id
                    _logger.info('\n\n\n INVOICE ADDRESS FOUND \n\n\n\n %s \n\n\n\n', vals['partner_invoice_id'])
                else:
                    vals['partner_invoice_id'] = self.env["res.partner"].create({'type': 'invoice',
                                                                                 'create_by': "ws",
                                                                                 'is_company': False,
                                                                                 'id': vals['partner_id'],
                                                                                 'name':
                                                                                     vals['invoice_address'][
                                                                                         'name'],

                                                                                 'phone':
                                                                                     vals['delivery_address'][
                                                                                         'phone'],
                                                                                 'street':
                                                                                     vals['invoice_address'][
                                                                                         'street'],
                                                                                 'zip':
                                                                                     vals['invoice_address'][
                                                                                         'zip'],
                                                                                 'city':
                                                                                     vals['invoice_address'][
                                                                                         'city']}).id
                    _logger.info('\n\n\n NEW INVOICE ADDRESS CREATED \n\n\n\n %s \n\n\n\n', vals['partner_invoice_id'])

            [vals.pop(e) for e in ['create_by', 'delivery_address', 'invoice_address']]

            # FILL PRODUCTS LIST FOR THIS ORDER
            order_line_list = []
            for line in vals['order_line']:
                product_id = self.env['product.product'].search([("manufacturer_ref", "=", line['product_id'])])

                # FILL ORDER LINE FOR THIS ORDER
                line_obj = {"product_id": product_id.id,
                            "product_uom_qty": line["product_uom_qty"],
                            "price_unit": line['price_unit']}
                order_line_list.append([0, 0, line_obj])
            vals["order_line"] = order_line_list

            rec = super(WsOrder, self).create(vals)
            if rec:
                _logger.info('\n\n\n ORDER / QUOTATION CREATED FROM WS  \n\n\n\n %s \n\n\n\n', vals)
                return rec
        else:
            return super(WsOrder, self).create(vals)

    def write(self, vals):
        # Update made by WS  -------------------------------------------------------------------------
        if 'create_by' in vals:
            if 'order_state' in vals:
                self.order_state = vals['order_state']
            return super(WsOrder, self).write(vals)
        else:
            # update from odoo
            if self.state == "sale":
                vals['order_state'] = "NOT_PAID"

            return super(WsOrder, self).write(vals)






