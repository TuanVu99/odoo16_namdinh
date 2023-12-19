from odoo import models, fields, api


class WaterMeter(models.Model):
    _name = 'qwaco.water.meter'
    _description = "Qwaco Water Meter"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        required=True,
        string="Water Meter",
        tracking=True
    )
    state = fields.Selection([('active', 'Active'), ('inactive', 'Inactive')], required=True, default='active', tracking=True)
    reason = fields.Text("Reason")
    partner_id = fields.Many2one('res.partner', tracking=True)
    balance = fields.Float("Current Balance", default=0, digits='Product Unit of Measure', tracking=True)
    first_balance = fields.Float("First Balance", digits='Product Unit of Measure', default=0, tracking=True)
    manufacturing_date = fields.Date("Manufacturing Date")
    expired_date = fields.Date("Expired Date")
    setting_date = fields.Date("Setting Date")
    batch_number = fields.Char("Batch Number")

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'Constraints with the same name are unique per water meter.'),
    ]


    
