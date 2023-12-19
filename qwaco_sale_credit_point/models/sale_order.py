# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models, fields
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @property
    def credit_point_check_failed_msg(self):
        msg = _(
            "Sale Order amount total ({amount}) is higher"
            " than your available credit ({points})."
        )
        return msg.format(amount=self.amount_total, points=self.water_meter_id.credit_point)

    @property
    def credit_point_decrease_msg(self):
        return _("SO %s") % self.name

    def action_confirm(self):
        for sale in self:
            if sale.water_meter_id and sale.water_meter_id.use_credit_point and sale.water_meter_id.credit_point > 0:
                if not self.env.context.get('bypass_check_credit'):
                    self._action_check_credit()
                order_line_credit = sale.order_line.filtered(lambda l: l.is_credit)
                sale.water_meter_id.credit_point_decrease(
                    order_line_credit.price_unit, comment=self.credit_point_decrease_msg, order_id=sale.id
                )
        return super().action_confirm()

    def _action_check_credit(self):
        for sale in self:
            credit = 0
            if sale.water_meter_id and sale.water_meter_id.use_credit_point and sale.water_meter_id.credit_point > 0:
                order_line_credit = sale.order_line.filtered(lambda l: l.is_credit)
                if order_line_credit:
                    order_line_credit.unlink()
                order_line = sale.order_line.filtered(lambda l: l.product_uom_qty > 0)
                used_quantity = sum(order_line.mapped('product_uom_qty')) or 0
                if sale.water_meter_id.min_quantity > 0 and sale.water_meter_id.min_quantity > used_quantity:
                    raise UserError(_("Số nước sử dụng phải lớn hơn %s m3!") % sale.water_meter_id.min_quantity)
                product_credit = self.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.sale_product_credit') or False
                if not product_credit:
                    raise UserError(_("Vui lòng setting product credit!"))

                credit = sale.amount_total
                if sale.water_meter_id.min_credit > 0:
                    credit = sale.water_meter_id.min_credit if sale.amount_total > sale.water_meter_id.min_credit else sale.amount_total

                if credit - sale.water_meter_id.credit_point > 0:
                    credit = sale.water_meter_id.credit_point
                sale.write({'order_line': [
                    (0, False, {
                        'product_id': int(product_credit),
                        'product_uom_qty': -1,
                        'price_unit': credit,
                        'is_credit': True
                    })
                ]})
            return credit



    def _action_cancel(self):
        for sale in self:
            if sale.state in ("sale", "done"):
                order_line_credit = sale.order_line.filtered(lambda l: l.is_credit)
                if order_line_credit:
                    sale.water_meter_id.credit_point_increase(
                        order_line_credit.price_unit, _("Sale Order canceled"), order_id=sale.id
                    )
        return super()._action_cancel()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_credit = fields.Boolean("Is Credit", default=False)

