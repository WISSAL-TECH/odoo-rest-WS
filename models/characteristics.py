from odoo import models, fields, api


class Characteristics(models.Model):
    _name = 'product.characteristics'

    attribute_id = fields.Many2one("characteristic.name", "Name", ondelete='restrict', required=True, index=True)
    value_id = fields.Many2one("characteristic.value", "Value", domain="[('attribute_id', '=', attribute_id)]",
                               relation='characteristic_value_product_characteristics_rel', ondelete='restrict')
    product_id = fields.Many2one('product.template', ondelete='cascade', index=True)


class CharacteristicsName(models.Model):
    _name = 'characteristic.name'

    name = fields.Char("Name")
    value_ids = fields.One2many('characteristic.value', 'attribute_id', copy=True)
    # characteristic_ids = fields.One2many('product.characteristics', 'attribute_id', "Lines")
    product_id = fields.Many2one('product.template', store=True)


class CharacteristicsValue(models.Model):
    _name = 'characteristic.value'

    name = fields.Char("Name")
    characteristic_id = fields.Many2one("product.characteristics",
                                        relation='characteristic_value_product_characteristics_rel', copy=False,
                                        invisible=1)
    attribute_id = fields.Many2one("characteristic.name", ondelete='cascade', required=True, index=True,
                                 )









