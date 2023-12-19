from odoo import models, fields, api


class WaterMeter(models.Model):
    _inherit = 'qwaco.water.meter'

    water_meter_quantity_ids = fields.One2many('qwaco.water.meter.quantity.history', 'water_meter_id', string='Qwaco Water Meter History')


    
