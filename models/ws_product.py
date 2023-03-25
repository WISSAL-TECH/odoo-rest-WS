import json
import requests
from odoo import models, fields, api
from odoo.http import request
import logging
from _datetime import datetime

_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = ['product.template']

    brand = fields.Many2one("product.brand", 'Brand')
    image_url = fields.Char('image url')
    is_virtual = fields.Boolean("is Virtual", default=False)
    create_by = fields.Char(string="Créé à partir de",
                            default="Odoo", readonly=True)
    # characteristic_ids = fields.One2many('product.characteristics', 'product_id')
    manufacturer_ref = fields.Char(string="Code constructeur")
    supplier_ids = fields.One2many('product.supplierinfo', 'product_id', string="Suppliers")
    detailed_type = fields.Selection(default="product")
    state = fields.Selection(
        selection=[("EN_STOCK", "En Stock"), ("RUPTURE_DE_STOCK", "Rupture de stock"), ("SUR_COMMANDE", "SUR COMMANDE"),
                   ("OBSOLETE", "OBSOLETE")], string="State", default="EN_STOCK")
    availabilityDate = fields.Date("Availability date")
    target = fields.Selection(selection=[("CASH", "CASH"), ("SPLIT_PAYMENT", "SPLIT PAYMENT")], string="Target",
                              default="CASH")
    isUsed = fields.Selection(
        selection=[("NEUF_SOUS_EMBALLAGE", "NEUF SOUS EMBALLAGE"), ("OCCASION_10", "OCCASION 10/10"),
                   ("OCCASION_9", "OCCASION9/10")], string="Etat", default="NEUF_SOUS_EMBALLAGE")
    installLink = fields.Char("Install link")
    characteristic_ids = fields.One2many('product.characteristics', 'product_id', "Characteristics", copy=True)
    master_product = fields.Many2one("product.master", string="Parent product", store=True)

    # set the url and headers
    # headers = {"Content-Type": "application/json", "Accept": "application/json", "Catch-Control": "no-cache"}
    # url = ""

    @api.model
    def create(self, vals):
        if "create_by" in vals:
            # 1- CREATE A PRODUCT FROM WS (Receive a product from WS)
            if 'create_by' in vals:
                # GET BRAND, COMPANY, ATTRIBUTES AND CATEGORY ID FROM THE NAMES GIVEN IN VALS
                vals['brand'] = self.create_brand(vals['brand']).id
                vals['categ_id'] = self.create_category(vals['categ_id']).id
                vals['company_id'] = request.env['res.company'].search([('name', '=', vals['company_id'])]).id

                attributes = []
                for attr in vals['attribute']:
                    attribute_items = [0, 0]
                    attr_id = self.create_attribute(attr['attribute_id']).id
                    attr_value_id = self.create_attribute_value(attr['value_id'], attr_id).id
                    attribute_items.append({
                        'attribute_id': attr_id,
                        'value_id': attr_value_id
                    })
                    print(attribute_items)
                    attributes.append(attribute_items)
                vals['characteristic_ids'] = attributes

            master_product = request.env['product.master'].search([('ref', '=', vals['manufacturer_ref'])])
            if master_product:
                vals['master_product'] = master_product.id
            else:
                new_master_product = request.env['product.master'].create(
                    {'ref': vals['manufacturer_ref'], 'name': vals['name']})
                vals['master_product'] = new_master_product.id

            [vals.pop(e) for e in ['attribute', 'product_name']]

            rec = super(Product, self).create(vals)
            return rec

        # 2- CREATE A PRODUCT FROM ODOO (Send a product to WS)
        else:
            category = self.env['product.category'].search([("id", '=', vals['categ_id'])]).name
            brand = self.env['product.brand'].search([("id", '=', vals['brand'])]).name
            product_name = request.env['product.master'].search([('id', '=', vals['master_product'])]).name
            manufacturer_ref = request.env['product.master'].search([('id', '=', vals['master_product'])]).ref

            if vals['is_virtual']:
                ws_type = "VIRTUAL"
            else:
                ws_type = "PHISICAL"

            rec = super(Product, self).create(vals)

            # FILL THE JSON DATA
            product_json = {
                "config_name": vals["name"],
                "name": product_name,
                "productBrand": brand,
                "categoryLabel": category,
                "reference": vals["manufacturer_ref"],
                "description": vals["description"],
                "images": vals["image_url"],
                "type": ws_type,
                "price": vals["list_price"],
                "refConstructor": manufacturer_ref,
                "installLink": vals["installLink"],
                "target": vals["target"],
                "isUsed": vals["isUsed"],
                "availabilityDate": vals["availabilityDate"],
                "productCharacteristics": [],
            }
            print('this is odoo creation', product_json)

            return rec

    # UPDATE A PRODUCT
    def write(self, vals):
        # THIS IS TO PREVENT "CREATE" FROM CALLING THE "WRITE" METHOD
        if len(vals.keys()) <= 2 and ('barcode' in vals.keys() or 'default_code' in vals.keys()):
            print("bb")
            return super(Product, self).write(vals)

        # 1- RECEIVE UN UPDATE FROM WS
        if 'create_by' in vals:

            if 'brand' in vals:
                vals['brand'] = self.create_brand(vals['brand']).id
            if 'categ_id' in vals:
                vals['categ_id'] = self.create_category(vals['categ_id']).id
            print(vals['attribute'])

            # UPDATE CHARACTERISTICS LIST
            attributes = [(5, 0, 0)]
            for attr in vals['attribute'][0][2]:
                print(attr)
                attribute_items = [0, 0]
                attr_id = self.create_attribute(attr['attribute_id']).id
                attr_value_id = self.create_attribute_value(attr['value_id'], attr_id).id

                attribute_items.append({
                    'attribute_id': attr_id,
                    'value_id': attr_value_id
                })
                attributes.append(attribute_items)
            vals['characteristic_ids'] = attributes
            vals.pop('attribute')

            rec = super(Product, self).write(vals)
            print("API UPDATE", vals)
            return rec

        # 1- SEND UN UPDATE/ARCHIVE TO WS FROM ODOO
        else:
            # 1- ARCHIVE A PRODUCT FROM ODOO
            if 'active' in vals.keys():
                if vals["active"] == False:
                    archived_product = {"manufacturer_ref": self.manufacturer_ref}
                    print("this is odoo archive", archived_product)

                else:
                    unarchived_product = {"manufacturer_ref": self.manufacturer_ref}
                    print("this is odoo unarchive", unarchived_product)
                return super(Product, self).write(vals)
            else:
                # 2- UPDATE FROM ODOO
                rec = super(Product, self).write(vals)
                product_ref = self.master_product.ref
                print("product ref", product_ref)

                # GET characteristics LIST
                characteristic_list = []
                for attr in self.characteristic_ids:
                    characteristic_obj = {
                        "attribute_id": attr.attribute_id.name,
                        "value_id": attr.value_id.name}
                    characteristic_list.append(characteristic_obj)

                if vals['is_virtual']:
                    ws_type = "VIRTUAL"
                else:
                    ws_type = "PHISICAL"

                # FILL THE JSON DATA
                product_json = {
                    "name": self.name,
                    "product": product_ref,
                    "brand": self.brand.name,
                    "categ_id": self.categ_id.name,
                    "description": self.description,
                    "image_url": self.image_url,
                    "type": ws_type,
                    "list_price": self.list_price,
                    "attribute": characteristic_list,
                }

                print("THIS IS AN ODOO UPDATE ", product_json)
                return rec

    def create_brand(self, brand):
        # CHECK IF THE BRAND EXISTS
        try:
            brand_id = self.env['product.brand'].search([("name", "ilike", brand)])[0]
        # CREATE A NEW ONE IF NOT EXISTING
        except:
            brand_id = self.env['product.brand'].create({'name': brand})
        return brand_id

    def create_category(self, category):
        # CHECK IF THE CATEGORY EXISTS
        try:
            new_category = self.env['product.category'].search([("name", "ilike", category)])[0]
        # CREATE A NEW ONE IF NOT EXISTING
        except:
            new_category = self.env['product.category'].create({'name': category})
        return new_category

    def create_attribute(self, attribute):
        # CHECK IF THE attribute EXISTS
        try:
            attribute_id = self.env['characteristic.name'].search([("name", "=", attribute)])[0]
        # CREATE A NEW ONE IF NOT EXISTING
        except:
            attribute_id = self.env['characteristic.name'].create({'name': attribute})

        return attribute_id

    def create_attribute_value(self, value, attr_id):
        # CHECK IF THE attribute value EXISTS
        try:
            value_id = self.env['characteristic.value'].search([("name", "=", value)])[0]
        # CREATE A NEW ONE IF NOT EXISTING
        except:
            value_id = self.env['characteristic.value'].create({'name': value, "attribute_id": attr_id})
        return value_id


class MasterProduct(models.Model):
    _name = 'product.master'

    name = fields.Char("Name")
    product_list = fields.One2many('product.template', 'master_product', 'Products list', domain="[('master_product', '=', id)]")
    ref = fields.Char(string="Manufacturer reference")


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'product brand'
    name = fields.Char(string='Brand', required=True)
    product_ids = fields.One2many(
        "product.template", "id", string="product ids", copy=True)

    def name_get(self):
        res = []
        for field in self:
            res.append((field.id, field.name))
        return res
