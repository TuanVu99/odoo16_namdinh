# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, exceptions, fields, models

POINT_OPERATIONS = [
    ("increase", "Increase"),
]


class ManageCreditPoint(models.TransientModel):
    _name = "wiz.manage.credit.point"
    _description = "Wizard to Manage Credit Points"

    credit_point = fields.Integer(
        string="Points",
        required=True,
    )
    water_meter_ids = fields.Many2many(
        "qwaco.water.meter",
        string="Water Meter",
        required=True,
    )
    comment = fields.Text(
        required=True,
    )
    operation = fields.Selection(
        string="Type of operation",
        selection=POINT_OPERATIONS,
        required=True,
        default="increase"
    )

    def action_update_credit(self):
        self.ensure_one()
        if not self.comment:
            raise exceptions.UserError(_("A comment is needed to the update credit"))
        for water_meter in self.water_meter_ids:
            handler = getattr(water_meter, "credit_point_" + self.operation)
            handler(self.credit_point, comment=self.comment)
