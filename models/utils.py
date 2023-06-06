from odoo import models
import psycopg2


class Utils(models.Model):
    _name = 'odoo_utils'
    _description = 'Common useful functions (This class is used to avoid duplicated code)'

    # FUNCTION TO QUERY THE FIELDs FROM A MODEL
    def affect_many_to_one(self, request_key, object, field_in_db, field_to_get='id'):
        field = self.env[object].search([(field_in_db, '=', request_key)])[field_to_get]
        if field:
            return field
        else:
            return False

    # Function to connect to WS DB and get sequences
    def _wsconnect(self):
        ###################### dev

        return psycopg2.connect(host="3.9.25.94",
                                user="wsdev",
                                options='',
                                port="6432",
                                dbname="dbwsdev",
                                password="4qu0gAMA6hNI856sbgFN",
                                sslmode='require')

    def order_affect_address(self, client_env):

        partner = self.env['res.partner'].search([('id', '=', client_env)])
        name = partner.name
        email = partner.email
        if partner.is_company == False:

            delivery_address_list = []
            # Fill shiping address fields (if partner is person)
            for child in partner.child_ids:
                if child.type == 'delivery':
                    delivery_address = {}
                    delivery_address['name'] = name
                    delivery_address['street'] = child.street
                    delivery_address['street2'] = child.street2
                    delivery_address['zip'] = child.zip
                    state = self.affect_many_to_one(child.state_id.id, 'res.country.state', 'id', 'name')
                    delivery_address['city'] = state
                    country_code = self.affect_many_to_one(child.country_id.id, 'res.country', 'id', 'code')
                    delivery_address['country_id'] = country_code
                    delivery_address_list.append(delivery_address)
            if not delivery_address_list:
                delivery_address = {}
            else:
                delivery_address = delivery_address_list[-1]

            if partner.parent_id:
                parent = partner.parent_id
                parent_siret = parent.siret

                # Fill invoice address fields if parent company exist
                invoice_address = {}
                for child in parent.child_ids:
                    if child.type == 'invoice':
                        invoice_address['name'] = parent.name
                        invoice_address['phone'] = parent.phone
                        invoice_address['street'] = child.street
                        invoice_address['street2'] = child.street2
                        invoice_address['zip'] = child.zip
                        invoice_address['state_id'] = child.city
                        state = self.affect_many_to_one(child.state_id.id, 'res.country.state', 'id', 'name')
                        invoice_address['city'] = state
                        country_code = self.affect_many_to_one(child.country_id.id, 'res.country', 'id', 'code')
                        invoice_address['country_id'] = country_code
            else:

                # Fill invoice address fields if partner is person and no parent company
                parent_siret = None
                invoice_address = delivery_address
        else:

            # Fill invoice address fields if partner is company
            invoice_address = {}
            for child in partner.child_ids:
                if child.type == 'invoice':
                    invoice_address['name'] = name
                    invoice_address['phone'] = partner.phone
                    invoice_address['street'] = child.street
                    invoice_address['street2'] = child.street2
                    invoice_address['zip'] = child.zip
                    invoice_address['state_id'] = child.city
                    state = self.affect_many_to_one(child.state_id.id, 'res.country.state', 'id', 'name')
                    invoice_address['city'] = state
                    country_code = self.affect_many_to_one(child.country_id.id, 'res.country', 'id', 'code')
                    invoice_address['country_id'] = country_code
            delivery_address = invoice_address
            parent_siret = None
        return {
            'invoice_address': invoice_address,
            'delivery_address': delivery_address,
            'parent_siret': parent_siret,
            'email': email,
            'name': name
        }
