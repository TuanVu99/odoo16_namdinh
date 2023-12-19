{
    'name': "Qwaco Sale",
    'summary': """Qwaco Sale""",
    'description': """
        Qwaco Sale
    """,
    'category': 'Sales/CRM',
    'version': '1.0.1',
    "license": "LGPL-3",
    'external_dependencies': {
    },
    'depends': ['qwaco_contact', 'sale', 'account'],
    'data': [
        "data/ir_cron_data.xml",
        "security/ir.model.access.csv",
        "views/sale_views.xml",
        "views/account_payment_term_views.xml",
        "views/res_config_settings_view.xml",
        "views/water_meter.xml"
        ],
}
