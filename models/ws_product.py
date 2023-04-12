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
    master_product = fields.Many2one("product.master", string="Parent product", store=True, ondelete='cascade')
    created_from_master_product = fields.Boolean(default=False)

    # set the url and headers
    # headers = {"Content-Type": "application/json", "Accept": "application/json", "Catch-Control": "no-cache"}
    # url = ""

    @api.model
    def create(self, data):
        if "create_by" in data:
            brand = self.create_brand(data['brand']).id
            category = self.create_category(data['categ_id']).id
            vals_list = {}
            for vals in data["product"]:
                # 1- CREATE PRODUCTs FROM WS (Receive a product from WS)

                vals_list['company_id'] = request.env['res.company'].search([('name', '=', vals['company_id'])]).id
                vals_list['name'] = vals['name']
                vals_list['target'] = vals['target']
                vals_list['isUsed'] = vals['isUsed']
                vals_list['detailed_type'] = vals['detailed_type']
                vals_list['image_url'] = vals['image_url']
                vals_list['is_virtual'] = vals['is_virtual']
                vals_list['list_price'] = vals['list_price']
                vals_list['manufacturer_ref'] = vals['manufacturer_ref']
                vals_list['purchase_ok'] = vals['purchase_ok']
                vals_list['sale_ok'] = vals['sale_ok']
                vals_list['company_id'] = vals['company_id']

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
                vals_list['characteristic_ids'] = attributes

                master_product = request.env['product.master'].search([('ref', '=', data['product_ref'])])
                if master_product:
                    vals_list['master_product'] = master_product.id
                else:
                    new_master_product = request.env['product.master'].create(
                        {'ref': data['product_ref'],
                         'name': data['name'],
                         'brand': brand,
                         'categ_id': category,
                         'create_by': "ws"})
                    vals_list['master_product'] = new_master_product.id

                rec = super(Product, self).create(vals_list)
            return rec

        # 2- CREATE A PRODUCT FROM ODOO (Send a product to WS)
        else:
            category = self.env['product.category'].search([("id", '=', data['categ_id'])]).name
            product_name = request.env['product.master'].search([('id', '=', data['master_product'])]).name
            manufacturer_ref = request.env['product.master'].search([('id', '=', data['master_product'])]).ref

            if data['is_virtual']:
                ws_type = "VIRTUAL"
            else:
                ws_type = "PHISICAL"

            # GET characteristics LIST
            characteristic_list = []
            for attr in data['characteristic_ids']:
                characteristic_obj = {
                    "name": attr.attribute_id.name,
                    "value": attr.value_id.name}
                characteristic_list.append(characteristic_obj)

            rec = super(Product, self).create(data)

            # FILL THE JSON DATA
            product_json = {
                "name": data["name"],
                "reference": data["manufacturer_ref"],
                "description": data["description"],
                "images": data["image_url"],
                "type": ws_type,
                "active": False,
                "state": data["state"],
                "price": data["list_price"],
                "refeConstructor": manufacturer_ref,
                "installLink": data["installLink"],
                "target": data["target"],
                "isUsed": data["isUsed"],
                "availabilityDate": data["availabilityDate"],
                "productCharacteristics": characteristic_list,
            }

            if rec.created_from_master_product:
                print("not sending to ws")
            else:
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
            if 'attribute' in vals:
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
                        "name": attr.attribute_id.name,
                        "value": attr.value_id.name}
                    characteristic_list.append(characteristic_obj)

                if vals['is_virtual']:
                    ws_type = "VIRTUAL"
                else:
                    ws_type = "PHISICAL"

                # FILL THE JSON DATA
                product_json = {
                    "name": self.name,
                    "reference": self.manufacturer_ref,
                    "refeConstructor": product_ref,
                    "description": self.description,
                    "image_url": self.image_url,
                    "price": self.list_price,
                    "productCharacteristics": characteristic_list,
                    "updater": False,
                    "availabilityDate": self.availabilityDate,
                    "display": False,
                    "type": ws_type,
                    "state": self.state,
                    "installLink": self.installLink,
                    "target": self.target
                }
                if self.created_from_master_product:
                    print("not sending update to ws")
                else:
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
    brand = fields.Many2one("product.brand", 'Brand')
    product_list = fields.One2many('product.template', 'master_product', 'Products list',
                                   domain="[('master_product', '=', id)]")
    ref = fields.Char(string="Manufacturer reference")
    create_by = fields.Char("Created by")
    categ_id = fields.Many2one('product.category', 'Product Category', change_default=True,
                               group_expand='_read_group_categ_id',
                               help="Select category for the current product")

    @api.model
    def create(self, vals):
        # SEND MULTIPLE PRODUCTS AT ONCE FROM ODOO
        if "create_by" not in vals:
            configurations_list = []
            configurations_obj = {}
            for item in vals["product_list"]:
                item[2]['created_from_master_product'] = True
                # GET CHARACTERISTICS LIST FOR EVERY PRODUCT
                characteristic_list = []
                for attr in item[2]["characteristic_ids"]:
                    attribute_name = self.env['characteristic.name'].search([("id", "=", attr[2]['attribute_id'])]).name
                    value_name = self.env['characteristic.value'].search([("id", "=", attr[2]['value_id'])]).name
                    characteristic_obj = {
                        "name": attribute_name,
                        "value": value_name}
                    characteristic_list.append(characteristic_obj)

                # FILL NEEDED DATA FOR EACH PRODUCT
                configurations_obj["name"] = item[2]["name"]
                configurations_obj["refeConstructor"] = vals["ref"]
                configurations_obj["reference"] = item[2]["manufacturer_ref"]
                configurations_obj["discount"] = False
                configurations_obj["state"] = False
                configurations_obj["script"] = False
                configurations_obj["active"] = False
                configurations_obj["updater"] = False
                configurations_obj["productName"] = False
                configurations_obj["display"] = False
                configurations_obj["type"] = False
                configurations_obj["description"] = item[2]["description"]
                configurations_obj["images"] = item[2]["image_url"]
                configurations_obj["price"] = item[2]["list_price"]
                configurations_obj["installLink"] = item[2]["installLink"]
                configurations_obj["target"] = item[2]["target"]
                configurations_obj["isUsed"] = item[2]["isUsed"]
                configurations_obj["availabilityDate"] = item[2]["availabilityDate"]
                configurations_obj["productCharacteristics"] = characteristic_list
                configurations_list.append(configurations_obj)

            category = self.env['product.category'].search([("id", '=', vals['categ_id'])]).name
            brand = self.env['product.brand'].search([("id", '=', vals['brand'])]).name

            # FILL THE FINAL JSON OBJECT TO SEND TO WS
            products_list = {
                "description": False,
                "categoryId": category,
                "brand": {
                    "name": brand,
                    "reference": False},
                "comments": False,
                "activate": False,
                "target": False,
                "product_name": vals["name"],
                "refeConstructor": vals["ref"],
                "configurations": configurations_list,
            }

            print(products_list)
            rec = super(MasterProduct, self).create(vals)
            # for product in rec.product_list:
            #     product.created_from_master_product = True
            return rec
        else:
            return super(MasterProduct, self).create(vals)


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
