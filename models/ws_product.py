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

    # set the url and headers
    # headers = {"Content-Type": "application/json", "Accept": "application/json", "Catch-Control": "no-cache"}
    # url = ""

    @api.model
    def create(self, vals):
        if "create_by" in vals:
            # 1- CREATE A PRODUCT FROM WS (Receive a product from WS)
            if 'create_by' in vals.keys():
                # GET BRAND, COMPANY, ATTRIBUTES AND CATEGORY ID FROM THE NAMES GIVEN IN VALS
                vals['brand'] = self.create_brand(vals['brand']).id
                vals['categ_id'] = self.create_category(vals['categ_id']).id
                vals['company_id'] = request.env['res.company'].search([('name', '=', vals['company_id'])]).id

                attributes = []
                for attr in vals['attribute']:
                    attribute_items = [0, 0]
                    attr_id = self.create_attribute(attr['attribute_id']).id
                    values_list = []
                    for value in attr['value_ids']:
                        attr_value_id = self.create_attribute_value(value, attr_id).id
                        values_list.append(attr_value_id)
                    print(values_list)
                    attribute_items.append({
                        'attribute_id': attr_id,
                        'value_ids': values_list
                    })
                    attributes.append(attribute_items)
                vals['attribute_line_ids'] = attributes
                vals.pop('attribute')

            return super(Product, self).create(vals)

        # 2- CREATE A PRODUCT FROM ODOO (Send a product to WS)
        else:
            category = self.env['product.category'].search([("id", '=', vals['categ_id'])]).name
            brand = self.env['product.brand'].search([("id", '=', vals['brand'])]).name

            # GET SUPPLIERS LIST AND PUT IT IN THE REQUESTED STRUCTURE
            # supplier_list = []
            # for key in vals['seller_ids']:
            #     supplier_obj = {
            #         "fournisseur": key[2]['name'],
            #         "qte": key[2]["min_qty"],
            #         "prix": key[2]["price"]
            #     }
            #     supplier_list.append(supplier_obj)

            # GET characteristic LIST AND PUT IT IN THE REQUESTED STRUCTURE
            # characteristic_list = []
            # for attr in vals['attribute_line_ids']:
            #     attribute_name = self.env['product.attribute'].search([("id", "=", attr[2]['attribute_id'])]).name
            #     # value_name = self.env['product.attribute.value'].search(
            #     #     [("id", "=", attr[2]['value_ids'][0][2][0])]).name
            #
            #     attribute_obj = {"title": attribute_name, }
            #     value_list = []  # GET ALL THE VALUES FOR THIS ATTRIBUTE
            #     for value in attr[2]['value_ids'][0][2]:
            #         value_name = self.env['product.attribute.value'].search(
            #             [("id", "=", value)]).name
            #         value_list.append(value_name)
            #         attribute_obj["value"] = value_list
            #     characteristic_list.append(attribute_obj)
            # print(characteristic_list)

            if vals['is_virtual']:
                ws_type = "VIRTUAL"
            else:
                ws_type = "PHISICAL"

            # FILL THE JSON DATA
            product_json = {
                "name": vals["name"],
                "productBrand": brand,
                "categoryLabel": category,
                "reference": vals["default_code"],
                "description": vals["description"],
                "images": vals["image_url"],
                "type": ws_type,
                "price": vals["list_price"],
                "refConstructor": vals["manufacturer_ref"],
                "installLink": vals["installLink"],
                "target": vals["target"],
                "isUsed": vals["isUsed"],
                "availabilityDate": vals["availabilityDate"],
                "productCharacteristics": [],
            }
            print('this is odoo creation', product_json)

            return super(Product, self).create(vals)

    # UPDATE A PRODUCT
    def write(self, vals):
        # THIS IS TO PREVENT "CREATE" FROM CALLING THE "WRITE" METHOD
        if len(vals.keys()) <= 2 and ('barcode' in vals.keys() or 'default_code' in vals.keys()):
            return super(Product, self).write(vals)

        # 1- RECEIVE UN UPDATE FROM TEKKEYS
        if 'create_by' in vals.keys():
            # GET BRAND, COMPANY AND CATEGORY ID FROM THE NAME GIVEN IN VALS
            if 'brand' in vals:
                vals['brand'] = self.create_brand(vals['brand']).id
            if 'categ_id' in vals:
                vals['categ_id'] = self.create_category(vals['categ_id']).id
            if 'company_id' in vals:
                vals['company_id'] = request.env['res.company'].search([('name', '=', vals['company_id'])]).id

            # SELECT PRODUCT TYPE FROM THE DATA GIVEN IN VALS
            if 'detailed_type' in vals:
                if vals['detailed_type'] in ["storable product", "product"]:
                    detailed_type = "product"
                elif vals['detailed_type'] == "service":
                    detailed_type = "service"
                elif vals['detailed_type'] == "consumable":
                    detailed_type = "consu"

            # UPDATE CHARACTERISTICS LIST
            attributes = [(5, 0, 0)]
            for attr in vals['attribute'][0][2]:
                attribute_items = [0, 0]
                print(attr['attribute_id'])
                print(attr['value_ids'])
                attr_id = self.create_attribute(attr['attribute_id']).id
                values_list = []
                for value in attr['value_ids']:
                    attr_value_id = self.create_attribute_value(value, attr_id).id
                    values_list.append(attr_value_id)
                print(values_list)

                attribute_items.append({
                    'attribute_id': attr_id,
                    'value_ids': values_list
                })

                attributes.append(attribute_items)
            vals['attribute_line_ids'] = attributes
            vals.pop('attribute')
            print(vals['attribute_line_ids'])


            # existing_attribute_list = []
            # for attribute in self.attribute_line_ids:
            #
            #     values_list = []
            #     for value in attribute.value_ids:
            #         values_list.append(value.name)
            #     existing_attribute_list.append({
            #         'attribute_id': attribute.attribute_id.name,
            #         'value_ids': values_list
            #     })
            #
            # attributes = [5, 0, 0]
            # new_attrs_list = []
            # my_list = existing_attribute_list
            # for i in range(len(vals['attribute'][0][2])):
            #     for exist_attr in existing_attribute_list:
            #         attr = vals['attribute'][0][2][i]
            #         if attr['attribute_id'] == exist_attr['attribute_id']:
            #             attr_id = self.env['product.attribute'].search([("name", "ilike", attr['attribute_id'])])[0].id
            #             if attr['value_ids'][0] not in exist_attr['value_ids']:
            #                 attr_value_id = self.create_attribute_value(attr['value_ids'][0], attr_id).id
            #                 exist_attr['value_ids'].append(attr_value_id)
            #                 my_list = existing_attribute_list
            #             vals['attribute'][0][2].pop(i)
            #
            #         else:
            #             new_attrs_list.append(attr)
            #
            #     if new_attrs_list:
            #         for item in new_attrs_list:
            #             print("new found", item)
            #             my_list.append(item)

            rec = super(Product, self).write(vals)
            print("API UPDATE", vals)
            return rec
        else:
            return super(Product, self).write(vals)

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
            attribute_id = self.env['product.attribute'].search([("name", "=", attribute)])[0]

        # CREATE A NEW ONE IF NOT EXISTING
        except:
            attribute_id = self.env['product.attribute'].create({'name': attribute})

        return attribute_id

    def create_attribute_value(self, value, attr_id):
        # CHECK IF THE attribute value EXISTS
        try:
            value_id = self.env['product.attribute.value'].search([("name", "=", value)])[0]
        # CREATE A NEW ONE IF NOT EXISTING
        except:
            value_id = self.env['product.attribute.value'].create({'name': value, "attribute_id": attr_id})
        return value_id


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'product brand'
    name = fields.Char(string='Brand', required=True)
    product_ids = fields.One2many(
        "product.template", "id", string="product ids")

    def name_get(self):
        res = []
        for field in self:
            res.append((field.id, field.name))
        return res
