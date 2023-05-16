
import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    keys_ids = fields.One2many('product.virtual.keys', 'product', string='keys', domain="[('product', '=', id)]")


class ProductKey(models.Model):
    _name = 'product.virtual.keys'
    _description = 'virtual product keys or licence'

    key = fields.Char(string='Key')
    reference_key = fields.Char(string='Reference key')
    is_used = fields.Boolean("is used", default=False)
    is_viewed = fields.Boolean("is viewed", default=False)
    is_reserved = fields.Boolean("is reserved", default=False)
    order_number = fields.Many2one('sale.order',string="Order number")
    product = fields.Many2one('product.product', string='Product', domain="[('is_virtual', '=', True)]")
    create_by = fields.Char(string="Created By", default="Odoo", readonly=True)
    manufacturer_ref = fields.Char(related='product.manufacturer_ref', string='Manufacture reference')
    active = fields.Boolean(default=True)
