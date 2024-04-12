# -*- coding: utf-8 -*-
{
    'name': 'Qwaco API',
    'version': '1.0.0',
    'category': 'Extra Tools',
    'author': '#',
    'support': '#',
    'license': 'OPL-1',
    'website': '#',
    'summary': 'Qwaco API',
    'live_test_url': '#',
    'external_dependencies': {
        'python': [],
    },
    'depends': ['base_setup'],
    'data': [
        'data/ir_configparameter_data.xml',
        'data/ir_cron_data.xml',
        'security/ir.model.access.csv',
        'views/rest_api_access_token.xml',
        'views/rest_api_refresh_token.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
