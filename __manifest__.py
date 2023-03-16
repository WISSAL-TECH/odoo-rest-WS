# -*- coding: utf-8 -*-
{
    'name': "odoo_rest_ws",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'sequence': 1,
    'application': True,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['product','stock', 'sale', 'purchase'],

    # always loaded
    'data': [
        'data/settings.xml',
        'security/ir.model.access.csv',
        'views/ws_product_inherit.xml',
        'views/ws_license_keys_view.xml',
        'views/res_partner_inherit.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
