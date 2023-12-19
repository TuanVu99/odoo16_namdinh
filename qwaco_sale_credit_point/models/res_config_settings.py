# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import ast


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    qwaco_sale_product_credit = fields.Many2one('product.product', string='Sale Product Credit')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        #sale_product_credit
        sale_product_credit = self.env['ir.config_parameter'].sudo().get_param('qwaco.sale_product_credit') or False
        res.update(
            qwaco_sale_product_credit=int(sale_product_credit),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('qwaco.sale_product_credit', self.qwaco_sale_product_credit.id)