from odoo import models


class Utils(models.Model):
    _name = 'odoo_utils'
    _description = 'Common useful functions (This class is used to avoid duplicated code)'

    # FUNCTION TO QUERY THE FIELDs FROM A MODEL
    def affect_many_to_one(self, request_key, object, field_in_db, field_to_get = 'id'):
        field = self.env[object].search([(field_in_db, '=', request_key)])[field_to_get]
        if field:
            return field
        else:
            return False