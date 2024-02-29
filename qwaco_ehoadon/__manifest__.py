{
    'name': "eHoaDon Integration",
    'summary': """
        eHoaDon Integration""",
    'description': """
        eHoaDon Integration
    """,
    'author': "Baotnp",
    'website': "#",
    "license": "LGPL-3",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale', 'base_automation', 'queue_job'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/config_parameter.xml',
        'data/data_automation.xml',
        'data/queue_job_channel_data.xml',
        'views/sale_views.xml',
        'wizard/sale_edit_ehoadon.xml',
        'wizard/sale_resend_ehoadon.xml'
    ],
}
# -*- coding: utf-8 -*-
