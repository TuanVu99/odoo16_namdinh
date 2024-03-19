{
    'name': "Qwaco Printer",
    'summary': """Qwaco Printer""",
    'description': """
        Qwaco Printer
    """,
    'category': 'Sales/CRM',
    'version': '1.0.1',
    "license": "LGPL-3",
    "external_dependencies": {"python": ["pyOpenSSL"]},
    'depends': ['qwaco_ehoadon', 'qwaco_sale', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/qwaco_printer_data.xml',
        'views/qwaco_printer_views.xml',
        'views/qwaco_printer_template.xml',
    ],
    'assets': {
            'web.assets_backend': [
                'qwaco_printer/static/src/scss/doc_print.scss',
                'qwaco_printer/static/src/js/lib/*',
                'qwaco_printer/static/src/js/print_button_widget.js',
                'qwaco_printer/static/src/js/syncPrinterWidget.js',
                'qwaco_printer/static/src/js/inheritFormRenderer.js',
                'qwaco_printer/static/src/views/*.xml',
            ]
        }
}
