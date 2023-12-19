{
    'name': "Extend Address",
    'summary': """Extend VN Address""",
    'description': """

    """,
    'category': 'base',
    'version': '1.0.1',
    "license": "LGPL-3",
    'external_dependencies': {
        'python': ['xlrd'],
    },
    'depends': ['contacts'],
    'data': [
        'data/res.country.state.csv',
        'data/res.country.state.district.csv',
        'data/res.country.ward.csv',
        'security/ir.model.access.csv',
        'views/base_view.xml',
        'views/partner_address.xml',
        ],
}
