from odoo import models, fields, api
import logging
import json
import requests

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ADDITIONAL FIELDS
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
                    response = requests.post(self.url_client, data=json.dumps(json_data), headers=self.headers)
                    _logger.info('\n\n\n(CREATE) response from wissal-store\n\n\n\n--->>  %s\n\n\n\n', response.content)
                return res
