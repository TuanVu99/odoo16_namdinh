# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import ast


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    qwaco_reminder_days = fields.Integer()
    qwaco_sale_product_default = fields.Many2one('product.product', string='Sale Product Default')
    qwaco_allow_discount_first_order = fields.Boolean()
    qwaco_quantity_discount_first_order = fields.Float()
    qwaco_sale_product_discount_first_order = fields.Many2one('product.product', string='Sale Product Discount')
    qwaco_excluded_water_meter_discount_first_order = fields.Many2many('qwaco.water.meter', string='Excluded Water Meter')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        #reminder_days
        reminder_days = self.env['ir.config_parameter'].sudo().get_param('qwaco.reminder_days') or 0
        res.update(qwaco_reminder_days=int(reminder_days))
        #sale_product_default
        sale_product_default = self.env['ir.config_parameter'].sudo().get_param('qwaco.sale_product_default') or False
        res.update(
            qwaco_sale_product_default=int(sale_product_default),
        )
        #allow_discount_first_order
        allow_discount_first_order = self.env['ir.config_parameter'].sudo().get_param('qwaco.allow_discount_first_order') or False
        if allow_discount_first_order and allow_discount_first_order.lower() == 'true':
            res.update(
                qwaco_allow_discount_first_order=True,
            )
        else:
            res.update(
                qwaco_allow_discount_first_order=False,
            )
        # sale_product_discount
        sale_product_discount = self.env['ir.config_parameter'].sudo().get_param('qwaco.sale_product_discount_first_order') or False
        res.update(
            qwaco_sale_product_discount_first_order=int(sale_product_discount),
        )
        # quantity_discount
        qty_discount = self.env['ir.config_parameter'].sudo().get_param(
            'qwaco.quantity_discount_first_order') or 0
        res.update(
            qwaco_quantity_discount_first_order=float(qty_discount),
        )
        # excluded_water_meter_discount_first_order
        water_meter_ids = self.env['ir.config_parameter'].sudo().get_param('qwaco.excluded_water_meter_discount_first_order') or False
        if water_meter_ids:
            res.update(
                qwaco_excluded_water_meter_discount_first_order=[(6, 0, ast.literal_eval(water_meter_ids))],
            )
        else:
            res.update(
                qwaco_excluded_water_meter_discount_first_order=[(6, 0, [])],
            )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('qwaco.reminder_days', self.qwaco_reminder_days)
        set_param('qwaco.sale_product_default', self.qwaco_sale_product_default.id)
        set_param('qwaco.allow_discount_first_order', str(self.qwaco_allow_discount_first_order))
        set_param('qwaco.sale_product_discount_first_order', self.qwaco_sale_product_discount_first_order.id)
        set_param('qwaco.quantity_discount_first_order', self.qwaco_quantity_discount_first_order)
        set_param('qwaco.excluded_water_meter_discount_first_order', self.qwaco_excluded_water_meter_discount_first_order.ids)