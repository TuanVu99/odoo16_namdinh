from odoo import models, fields, api
from ast import literal_eval
from datetime import datetime
from dateutil.relativedelta import relativedelta

class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_product_pricelist = fields.Many2one(
        comodel_name='product.pricelist',
        string="Pricelist",
        compute='_compute_product_pricelist',
        inverse="_inverse_product_pricelist",
        company_dependent=False,
        domain=lambda self: [('company_id', 'in', (self.env.company.id, False))],
        tracking = True,
        help="This pricelist will be used, instead of the default one, for sales to the current partner")

    # sale_order_ids = fields.One2many('sale.order', 'partner_id', 'Sales Order',
    #                                  domain=[
    #                                      ('create_date', '<',
    #                                       (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-01 00:00:00')),
    #                                      ('create_date', '>=',
    #                                       (datetime.now() - relativedelta(months=0)).strftime('%Y-%m-01 00:00:00')),
    #                                      ('is_paid','!=',True),('state', 'in', ['sale', 'done'])
    #                                  ])

    x_sale_order_ids = fields.Many2many('sale.order', compute="compute_order",string="Danh sách Báo giá")

    def compute_order(self):
        self.ensure_one()
        if self.id:
            domain = [('partner_id','=',self.id) ,
                ('create_date', '<',
                 (datetime.now() + relativedelta(months=1)).strftime('%Y-%m-01 00:00:00')),
                ('create_date', '>=',
                 (datetime.now() - relativedelta(months=0)).strftime('%Y-%m-01 00:00:00')),
                ('is_paid', '!=', True), ('state', 'in', ['sale', 'done'])
            ]
            order_ids = self.env['sale.order'].search(domain)
            self.x_sale_order_ids = [(6, 0, order_ids.ids)] or None
        else:
            self.x_sale_order_ids = None
