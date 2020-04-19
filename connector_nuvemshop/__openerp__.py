# -*- coding: utf-8 -*-
# Copyright 2020 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Connector-nuvemshop',
    'summary': """
        Connector Nuvem Shop""",
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'https://github.com/oca',
    'depends': [
        'base',
        'connector',
        'connector_ecommerce',
        'product_m2mcategories',
        'product_multi_image',
    ],
    'data': [
        "views/menus_view.xml",

        "views/backend_view.xml",
        "views/product_category_view.xml",
    ],
    'demo': [
    ],
}
