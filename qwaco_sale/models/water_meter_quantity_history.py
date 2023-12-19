from odoo import models, fields, api


class WaterMeterHistory(models.Model):
    _name = 'qwaco.water.meter.quantity.history'
    _description = "Qwaco Water Meter History"

    water_meter_id = fields.Many2one('qwaco.water.meter', string='Water Meter', required=True, copy=False)
    order_id = fields.Many2one('sale.order', string='Sale Order', copy=False)
    old_quantity = fields.Float('Old Quantity', digits='Product Unit of Measure', required=True, default=0)
    new_quantity = fields.Float('New Quantity', digits='Product Unit of Measure', required=True, default=0)
    type = fields.Selection([('addition', 'Added'), ('deduction', 'Deducted')], string='Type', default='addition')