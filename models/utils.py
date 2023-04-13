from odoo import models
import psycopg2


class Utils(models.Model):
    _name = 'odoo_utils'
    _description = 'Common useful functions (This class is used to avoid duplicated code)'

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
