# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models


class WaterMeter(models.Model):
    _inherit = "qwaco.water.meter"

    use_credit_point = fields.Boolean("Use Credit Point", default=False)

    credit_point = fields.Monetary(
        string="Points Attribution",
        currency_field="credit_point_currency_id",
        readonly=True,
        default=0,
    )
    yearly_point_increase = fields.Monetary(
        string="Yearly points increase",
        currency_field="credit_point_currency_id",
        readonly=True,
        compute="_compute_yearly_point_increase",
    )
    credit_history_ids = fields.One2many(
        comodel_name="qwaco.credit.point.history",
        inverse_name="water_meter_id",
    )
    credit_point_currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self._default_credit_point_currency_id(),
    )
    min_quantity = fields.Float('Min Quantity', digits='Product Unit of Measure', required=True, default=0)
    min_credit = fields.Float('Min Credit', currency_field="credit_point_currency_id", required=True, default=0)

    def _default_credit_point_currency_id(self):
        curr=self.env['res.currency'].search([('name', '=', 'VND')], limit=1)
        return curr.id if curr else None

    @api.constrains("credit_point", "min_quantity", "min_credit")
    def _check_credit_point(self):
        for water in self:
            if water.credit_point < 0:
                raise exceptions.ValidationError(
                    _("You can't set a credit point lower than 0")
                )

            if water.min_quantity < 0:
                raise exceptions.ValidationError(
                    _("You can't set a min quantity lower than 0")
                )

            if water.min_credit < 0:
                raise exceptions.ValidationError(
                    _("You can't set a min credit lower than 0")
                )

    def action_update_credit_point(self):
        """Open update credit point wizard."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "wiz.manage.credit.point",
            "src_model": "qwaco.water.meter",
            "view_mode": "form",
            "target": "new",
            "context": {"default_water_meter_ids": self.ids},
        }

    def _credit_point_update(self, amount, comment=""):
        self.credit_point = amount

    def credit_point_replace(self, amount, comment=""):
        self._credit_point_update(amount, comment=comment)

    def credit_point_increase(self, amount, comment="", order_id=None):
        self._credit_point_update(self.credit_point + amount, comment=comment)
        self.update_history(amount, "increase", comment, order_id=order_id)

    def credit_point_decrease(self, amount, comment="", order_id=None):
        self._credit_point_update(self.credit_point - amount, comment=comment)
        self.update_history(amount, "decrease", comment, order_id=order_id)

    def update_history(self, amount, operation, comment, order_id=None):
        history_model = self.env["qwaco.credit.point.history"]
        vals = {
            "water_meter_id": self.id,
            "operation": operation,
            "amount": amount,
            "comment": comment,
            "order_id": order_id
        }
        return history_model.create(vals)

    def _compute_yearly_point_increase(self):
        self.env.cr.execute(
            """select water_meter_id, sum(amount) from qwaco_credit_point_history
            where operation='increase' and water_meter_id in %s
            and date_part('year', create_date)=date_part('year', CURRENT_DATE)
            group by water_meter_id""",
            (tuple(self.ids),),
        )
        amounts = dict(self.env.cr.fetchall())
        for record in self:
            record.yearly_point_increase = amounts.get(record.id, 0)
