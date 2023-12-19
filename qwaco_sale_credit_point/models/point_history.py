# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models

POINT_OPERATIONS = [
    ("replace", "Replace"),
    ("increase", "Increase"),
    ("decrease", "Decrease"),
]


class PointHistory(models.Model):
    _name = "qwaco.credit.point.history"
    _description = "Credit Point History"
    _rec_name = "water_meter_id"

    water_meter_id = fields.Many2one(
        comodel_name="qwaco.water.meter",
        string="Water Meter",
        required=True,
    )
    operation = fields.Selection(
        selection=POINT_OPERATIONS,
        required=True,
    )
    amount = fields.Monetary(
        currency_field="credit_point_currency_id",
        readonly=True,
        default=0,
        required=True,
    )
    credit_point_currency_id = fields.Many2one(
        related="water_meter_id.credit_point_currency_id",
        readonly=True,
    )
    order_id = fields.Many2one('sale.order', string='Sale Order', copy=False)
    comment = fields.Char()
