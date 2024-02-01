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

    sale_order_ids = fields.One2many('sale.order', 'partner_id', 'Sales Order',
                                     domain=[                                         
                                         ('is_paid','!=',True),
                                         ('state', 'in', ['sale', 'done'])
                                     ])
