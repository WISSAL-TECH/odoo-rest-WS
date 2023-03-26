from odoo import models, fields, api
import logging
import json
import requests

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ADDITIONAL FIELDS
    create_by = fields.Char(string="Créé à partir de ", default='Odoo')
    status = fields.Selection([('BLOCKED', 'Bloqué'), ('ACTIVE', 'Activé'), ('WAITING', 'En attente')], string="Statut", default="WAITING")
    lastname = fields.Char(string="Last name")

    # SET THE HEADERS AND URLS OF wissal-store
    headers = {"Content-Type": "application/json", "Accept": "application/json", "Catch-Control": "no-cache"}
    url_client = ""

    @api.model
    def create(self, vals):
        
        # SET THE ENVIREMENT
        utils = self.env['odoo_utils']

        # CHECK IF THE CREATION MADE BY wissal-store---------------------------------------------------------------------------------
        if 'create_by' in vals.keys():

            # CHECK TYPE OF CLIENT IF PERSON
            if vals["is_company"] == False:

                # IF CLIENT IS PERSON PUT THE title_id [res.partner.title] Madam/Mister (Many2one Relation)
                if 'title' in vals.keys():
                    title_id = utils.affect_many_to_one(vals['title'], 'res.partner.title', 'name')
                    if title_id:
                        vals['title'] = title_id
                    else:
                        vals['title'] = None

            # PUT THE country_id [res.country] (Many2one Relation)
            if 'country_id' in vals.keys():
                country_id = utils.affect_many_to_one(vals['country_id'], 'res.country', 'code')
                if country_id:
                    vals['country_id'] = country_id
                else:
                    vals['country_id'] = None
            
            # PUT THE state_id [res.country.state] (Many2one Relation)
            if 'state_id' in vals.keys():
                state_id = utils.affect_many_to_one(vals['state_id'], 'res.country.state', 'name')
                if country_id:
                    vals['state_id'] = state_id
                else:
                    vals['state_id'] = None
                    
            # Check if address of client creation 
            if vals["create_by"] == "wissal-store-address":
                client = self.env['res.partner'].search([('email', "=", vals["parent_id"])]).id
                vals["parent_id"] = client
                if 'combined_keys' in vals.keys():
                    vals.pop("combined_keys")
                
            response = super(ResPartner, self).create(vals)
            if response:
                _logger.info('\n\n\nclient created from controller (wissal-store)\n\n\n\n--->   %s\n\n\n\n', vals)
            return response

        # IF ODOO CREATION : CHECK IF COMPANY OR PERSON  THEN SEND POST REQUEST TO wissal-store API---------------------------------
        else:

            res = super(ResPartner, self).create(vals)

            # HERE IF THERE IS NO NAME AND NO LAST NAME SO IT IS ADDRESS CREATION DON'T SEND REQUEST TO wissal-store
            if (res.name == False) and (res.lastname == False):
                return res

            # QUERY FOR TITLE IF EXIST
            if 'title' in vals:
                title = utils.affect_many_to_one(vals['title'], 'res.partner.title', 'id', 'name')
            else:
                title = None
            
            # COLLECT DATA TO BE SENT IN DICT (IF PERSON CREATION)
            if vals["is_company"] == False:

                #  SEND DELIVERY ADDRESS FIELDS 
                delivery_address_list = []
                for child in res.child_ids:
                    if child.type == 'delivery':
                        delivery_address = {}
                        delivery_address['street'] = child.street
                        delivery_address['street2'] = child.street2
                        delivery_address['zip'] = child.zip
                        state = utils.affect_many_to_one(child.state_id.id, 'res.country.state', 'id', 'name')
                        delivery_address['city'] = state
                        country_code = utils.affect_many_to_one(child.country_id.id, 'res.country', 'id', 'code')
                        delivery_address['country_id'] = country_code
                        delivery_address_list.append(delivery_address)
                json_data = {
                            'person':{
                                'name': vals["name"] if "name" in vals.keys() else '',
                                'lastname': vals["lastname"] if "lastname" in vals.keys() else '',
                                'email': vals["email"] if "email" in vals.keys() else '',
                                'phone': vals["phone"] if "phone" in vals.keys() else '',
                                'mobile': self.mobile if "mobile" in self else '',
                                'title':title,
                                'status':vals["status"] if "status" in vals.keys() else '',
                            },
                            'address':delivery_address_list
                }
                
                if res:
                    _logger.info('\n\n\nclient (pesron) created from odoo,  values posted are\n\n\n\n--->   %s\n\n\n\n', json_data)
                    # response = requests.post(self.url_client, data=json.dumps(json_data), headers=self.headers)
                    # _logger.info('\n\n\n(CREATE) response from wissal-store\n\n\n\n--->>  %s\n\n\n\n', response.content)
                return res
            


    def write(self, vals):

            # SET THE ENVIREMENT
            utils = self.env['odoo_utils']

            # THIS CONDITION IS MADE BECAUSE OF
            # PATH IN THE CONTAINER usr/lib/python3/dist-packags/odoo/addons/base/models/res_partner.py line 600 (you can check it)
            # PATH IN THE CONTAINER usr/lib/python3/dist-packags/odoo/addons/base/models/res_partner.py line 142 (you can check it)
            if (len(vals.keys()) == 1 and ('is_company' in vals.keys()) or ('lang' in vals.keys()) or ('debit_limit' in vals.keys())) or len(vals.keys()) == 2 and ('vat' in vals.keys() and 'credit_limit' in vals.keys()) or ((('commercial_partner_id' in vals.keys()) or ('num_client' in vals.keys())) and  (len(vals.keys()) == 1)):
                _logger.info('\n\n\ncreate called write\n\n\n\n--->>  %s\n\n\n\n', vals)
                return super(ResPartner, self).write(vals)

            # CHECK IF UPDATE MADE BY wissal-store--------------------------------------------------------------------------------------
            if 'create_by' in vals.keys():
                
                # PUT THE country_id [res.country] (Many2one Relation)
                if 'country_id' in vals.keys():
                    country_id = utils.affect_many_to_one(vals['country_id'], 'res.country', 'code')
                    if country_id:
                        vals['country_id'] = country_id
                    else:
                        vals['country_id'] = None
                
                # PUT THE state_id [res.country.state] (Many2one Relation)
                if 'state_id' in vals.keys():
                    state_id = utils.affect_many_to_one(vals['state_id'], 'res.country.state', 'name')
                    if country_id:
                        vals['state_id'] = state_id
                    else:
                        vals['state_id'] = None

                # PUT THE title [res.partner.title] (Many2one Relation)
                if 'title' in vals.keys():
                    title_id = utils.affect_many_to_one(vals['title'], 'res.partner.title', 'name')
                    if title_id:
                        vals['title'] = title_id
                    else:
                        vals['title'] = None

                # delete address of client
                if vals["create_by"] == "wissal-store-address":
                    client_addresses = self.env['res.partner'].search([('email', "=", self.email)]).child_ids
                    if client_addresses:
                        for address in client_addresses:
                            state = address.state_id.name if address.state_id.name else ""
                            city =  address.city if address.city else ""
                            street = address.street if address.street else ""
                            combined_key = state + city + street
                            if combined_key == vals["combined_keys"]:
                                address.unlink()
                        if vals["combined_keys"]:
                            vals.pop("combined_keys")
                
                response = super(ResPartner, self).write(vals)
                _logger.info('\n\n\nresponse value is :  \n\n\n\n\n--->  %s\n\n\n\n\n\n\n', response)
                
                if response:
                    _logger.info('\n\n\nclient updated from controller \n\n\n\n\n--->  %s\n\n\n\n\n\n\n', vals)
                return response

            # UPDATE MADE BY ODOO--------------------------------------------------------------------------------------------------
            else:
                _logger.info('\n\n\nnot archive and not update of wissal-store, \n\n these are vals of wite method \n\n\n\n\n--->  %s\n\n\n\n', vals)

                # KEEP THE email IF PERSON TO SEND IT LATER AS oldMail ELSE IF COMPANY KEEP THE siret OF COMPANY TO SEND IT AS oldSiret
                unique_field = self.email

                # MAKE UPDATE
                res = super(ResPartner, self).write(vals)
                if res:

                    # COLLECT DATA TO BE SENT IN DICT (IF PERSON UPDATE)
                    if self.is_company == False:

                        # COLLECT DELIVERY ADDRESSES OF THE CLIENT
                        delivery_addresses = []
                        for child in self.child_ids:
                            delivery_address = {}
                            delivery_address['type'] = child.type
                            delivery_address['street'] = child.street
                            delivery_address['street2'] = child.street2
                            delivery_address['zip'] = child.zip
                            delivery_address['state'] = child.city
                            state = utils.affect_many_to_one(child.state_id.id, 'res.country.state', 'id', 'name')
                            delivery_address['city'] = state
                            country_code = utils.affect_many_to_one(child.country_id.id, 'res.country', 'id', 'code')
                            delivery_address['country_id'] = country_code
                            delivery_addresses.append(delivery_address)

                        json_data = {
                                    'person':{
                                        'name': self.name if "name" in self else '',
                                        'lastname': self.lastname if "lastname" in self else '',
                                        "function": self.function if "function" in self else None,
                                        "role": self.role if "role" in self else None,
                                        "title":self.title.name if 'title' in self else '' ,
                                        "status": self.status if "status" in self else '',
                                        "email": self.email if "email" in self else '',
                                        "type": self.type if "type" in self else '',
                                        "phone": self.phone if "phone" in self else '',
                                        'mobile': self.mobile if "mobile" in self else '',
                                        "old_email": unique_field
                                    },
                                    'address':delivery_addresses
                        }
                        _logger.info('\n\n\nclient (prson) updated from odoo,  values posted are \n\n\n\n\n--->  %s\n\n\n\n', json_data)
                        # response = requests.put(self.url_client, data=json.dumps(json_data), headers=self.headers)
                        # _logger.info('\n\n\n(UPDATE) response from wissal-store \n\n\n\n\n--->  %s\n\n\n\n', response.content)
                        return res

    def unlink(self):
        
        # DELETE MADE BY ODOO--------------------------------------------------------------------------------------------------
        json_data = {
            'email':self.email
        }
        if self.child_ids:
            for child in self.child_ids:
                child.unlink()
        response = super(ResPartner, self).unlink()

        if response and json_data['email'] != False:
            _logger.info('\n\n\nclient (prson) deleted from odoo,  values posted are \n\n\n\n\n--->  %s\n\n\n\n', json_data)
            # response = requests.delete(self.url_client, data=json.dumps(json_data), headers=self.headers)
            # _logger.info('\n\n\n(DELETE) response from wissal-store \n\n\n\n\n--->  %s\n\n\n\n', response.content)
        return response