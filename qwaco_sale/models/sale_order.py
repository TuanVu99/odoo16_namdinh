# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, datetime
from ast import literal_eval
import pytz
import logging

_logger = logging.getLogger(__name__)

READONLY_FIELD_STATES = {
    state: [('readonly', False)]
    for state in {'sale', 'done', 'cancel'}
}

class SaleOrder(models.Model):
    _inherit = "sale.order"

    water_meter_id = fields.Many2one('qwaco.water.meter', string='Water Meter', required=True, copy=False)
    contract_no = fields.Char(related="water_meter_id.partner_id.contract_no")
    popular_name = fields.Char(related="partner_id.popular_name")
    reminder_ids = fields.One2many('qwaco.sale.order.reminder', 'order_id', string='Reminder List')
    is_paid = fields.Boolean(string="Paid", default=False, copy=False, tracking=True)
    show_paid_button = fields.Boolean(compute='_compute_show_paid_button')
    paid_date = fields.Datetime('Paid Date', readonly=True)
    zone_id = fields.Many2one('res.country.zone', related='water_meter_id.partner_id.zone_id', string='Zone')
    ward_id = fields.Many2one('res.country.ward', related='water_meter_id.partner_id.ward_id', string='Ward')
    water_meter_quantity_ids = fields.One2many('qwaco.water.meter.quantity.history', 'order_id', string='Qwaco Water Meter')
    date_order = fields.Datetime(
        string="Order Date",
        required=True, readonly=False, copy=False,
        states=READONLY_FIELD_STATES,
        help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.",
        default=fields.Datetime.now)
    x_old_quantity = fields.Float('Old Quantity',compute ='compute_water',default=0)
    x_new_quantity = fields.Float('New Quantity',compute ='compute_water',default=0)
    x_tieu_thu = fields.Float('Số lượng nước tiêu thụ',compute ='compute_tieu_thu',default=0)
    x_giam_gia = fields.Float('Giảm giá',compute ='compute_giam_gia',default=0)
    x_amount_text = fields.Char("Bằng chữ",compute ='compute_bang_chu')
    x_customer_phone = fields.Char("Điện thoại", related='partner_id.phone')
    x_customer_address = fields.Text("Địa chỉ", related='partner_id.vietnam_full_address')
    x_meter_address = fields.Text("Địa chỉ ĐH", related='water_meter_id.partner_id.vietnam_full_address')
    x_ky= fields.Char("Kỳ tt", compute="compute_ky")

    def compute_ky(self):
        for r in self:
            r.x_ky = 'tháng '+ str(r.create_date.month)+'/'+str(r.create_date.year)

    @api.depends('water_meter_quantity_ids')
    def compute_water(self):
        for r in self:
            if r.water_meter_quantity_ids:
                for line in r.water_meter_quantity_ids:
                    r.x_new_quantity = line.new_quantity
                    r.x_old_quantity = line.old_quantity
            else:
                r.x_new_quantity = 0
                r.x_old_quantity = 0

    @api.depends('order_line')
    def compute_tieu_thu(self):
        for r in self:
            if r.order_line:
                for line in r.order_line.filtered(lambda l: l.product_template_id.id == 1):
                    r.x_tieu_thu = line.product_uom_qty or 0
            else:
                r.x_tieu_thu = 0

    @api.depends('order_line')
    def compute_giam_gia(self):
        for r in self:
            if r.order_line and any(line.product_template_id.id == 5 for line in r.order_line):
                for line in r.order_line.filtered(lambda l: l.product_template_id.id == 5):
                    r.x_giam_gia = line.product_uom_qty
            else:
                r.x_giam_gia =0

    @api.depends('amount_total')
    def number_to_words(self,amount):
        units = ["", "Mười", "Hai Mươi", "Ba Mươi", "Bốn Mươi", "Năm Mươi", "Sáu Mươi", "Bảy Mươi", "Tám Mươi",
                 "Chín Mươi"]
        digits = ["", "Một", "Hai", "Ba", "Bốn", "Năm", "Sáu", "Bảy", "Tám", "Chín"]

        amount_str = str(amount)
        length = len(amount_str)

        result = ""

        for i in range(length):
            digit = int(amount_str[i])
            if digit > 0:
                result += units[length - i - 1] + " " + digits[digit] + " "

        return result.strip()

    @api.depends('amount_total')
    def compute_bang_chu(self):
        for r  in self:
            r.x_amount_text = r.number_to_words(int(r.amount_total)) or ""

    def get_first_date_of_month(self, year, month):
        """Return the first date of the month.

        Args:
            year (int): Year
            month (int): Month

        Returns:
            date (datetime): First date of the current month
        """
        first_date = datetime(year, month, 1)
        return first_date

    def get_last_date_of_month(self, year, month):
        """Return the last date of the month.

        Args:
            year (int): Year, i.e. 2022
            month (int): Month, i.e. 1 for January

        Returns:
            date (datetime): Last date of the current month
        """
        next_month = datetime(year, month, 28) + timedelta(days=4)
        last_date = next_month - timedelta(days=next_month.day)
        return last_date

    @api.depends('payment_term_id', 'state')
    def _compute_show_paid_button(self):
        for order in self:
            if order.payment_term_id and order.payment_term_id.code == 'pay_later' \
                    and order.state in ('done', 'sale'):
                order.show_paid_button = True
            else:
                order.show_paid_button = False

    @api.onchange('partner_id')
    def _onchange_partner_id_warning(self):
        super(SaleOrder, self)._onchange_partner_id_warning()
        self.water_meter_id = False
        return {'domain': {'water_meter_id': [('partner_id', 'in', self.partner_id.child_ids.ids),
                                              ('state', '=', 'active')]}}


    @api.onchange('water_meter_id')
    def _onchange_water_meter_id(self):
        for order in self:
            zone_id = order.water_meter_id.partner_id.zone_id if order.water_meter_id.partner_id.zone_id else order.water_meter_id.partner_id.parent_id.zone_id
            if zone_id.team_id:
                order.team_id = zone_id.team_id.id

    @api.depends('partner_id', 'water_meter_id')
    def _compute_partner_invoice_id(self):
        for order in self:
            order.partner_invoice_id = order.water_meter_id.partner_id if order.water_meter_id and \
                                                                          order.water_meter_id.partner_id else False

    @api.depends('partner_id', 'water_meter_id')
    def _compute_partner_shipping_id(self):
        for order in self:
            order.partner_shipping_id = order.water_meter_id.partner_id if order.water_meter_id and \
                                                                          order.water_meter_id.partner_id else False

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            confirm_date = fields.Datetime.now()
            order.write({'date_order': confirm_date})
            if not order.payment_term_id:
                raise UserError(_("Please select Payment Terms before confirm order !"))
            if order.payment_term_id.code == 'pay_now':
                order.write(order._prepare_paid_values())
            qty_total = sum(line.product_uom_qty for line in order.order_line.filtered(
                            lambda l: l.product_uom_qty > 0))
            if order.water_meter_id:
                if order.water_meter_id.balance > 0:
                    last_qty = order.water_meter_id.balance
                else:
                    last_qty = order.water_meter_id.first_balance
                balance = last_qty + qty_total
                order.water_meter_id.with_context(tracking_disable=True).write({'balance': balance})
                vals = {'water_meter_id': order.water_meter_id.id,
                        'old_quantity': last_qty,
                        'new_quantity': balance,
                        'order_id': order.id
                       }
                self.env['qwaco.water.meter.quantity.history'].create(vals)
        return res

    def action_paid(self):
        for order in self:
            if not order.is_paid and order.payment_term_id and order.payment_term_id.code == 'pay_later':
                payment_term = self.env['account.payment.term'].sudo().search([('code', '=', 'pay_now')], limit=1)
                if not payment_term:
                    raise UserError(_("Please setting method Pay Now in Payment Term !"))
                vals = order._prepare_paid_values()
                vals['payment_term_id'] = payment_term.id
                order.write(vals)

    def _cron_action_reminder(self):
        reminder_cates = self.env['qwaco.reminder.category'].search([])
        if reminder_cates:
            reminder_days = self.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.reminder_days') or 7
            reminder_date = fields.Datetime.now() - timedelta(days=int(reminder_days))
            orders = self.env['sale.order'].sudo().search([('is_paid', '=', False),
                                                           ('state', 'in', ('sale', 'done')),
                                                           ('date_order', '<', reminder_date)])
            first_remind = reminder_cates.filtered(lambda l: l.sequence == 1)
            for order in orders:
                if not order.reminder_ids:
                    vals = {'order_id': order.id,
                            'reminder_category_id': first_remind.id,
                            'reminder_date': fields.datetime.now()
                            }
                    self.env['qwaco.sale.order.reminder'].create(vals)
        return

    def _cron_create_sale_quotation(self):
        _logger.info("------ Start Create Sale Quotation ------")
        product_default = self.env['ir.config_parameter'].sudo().get_param('qwaco.sale_product_default')
        if not product_default:
            raise UserError(_('Missing product default settings!'))
        product = self.env['product.product'].browse(int(product_default))
        if not product:
            raise UserError(_('Product not exist!'))
        period_date = self.env['ir.config_parameter'].sudo().get_param('qwaco.period_date_order', False)
        if not period_date:
            raise UserError(_('Missing Period Date!'))
        tz = pytz.timezone("Asia/Ho_Chi_Minh")
        tz_utc = pytz.timezone('UTC')
        period_date = datetime.strptime(period_date, DEFAULT_SERVER_DATE_FORMAT)
        today = fields.Datetime.now().astimezone(tz)
        if not (period_date.year == today.year and period_date.month == today.month):
            period_str = '%s-%s-01' % (today.year, today.strftime('%m'))
            _logger.info("Set Period Date: %s" % period_str)
            self.env['ir.config_parameter'].sudo().set_param('qwaco.period_date_order', period_str)
            period_date = today
        period_month = period_date.month
        period_year = period_date.year
        start_date_this_month = self.get_first_date_of_month(period_year, period_month)
        end_date_this_month = self.get_last_date_of_month(period_year, period_month)
        start_time_localize = tz.localize(datetime.combine(start_date_this_month, datetime.min.time()))
        start_time_utc = start_time_localize.astimezone(tz_utc).strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        end_time_localize = tz.localize(datetime.combine(end_date_this_month, datetime.max.time()))
        end_time_utc = end_time_localize.astimezone(tz_utc).strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        sale_order = self.env['sale.order'].sudo().search([('water_meter_id', '!=', False),
                                                           ('date_order', '>=', start_time_utc),
                                                           ('date_order', '<=', end_time_utc),
                                                           ('state', '!=', 'cancel')])
        meters = self.env['qwaco.water.meter'].sudo().search([('state', '=', 'active'),
                                                              ('partner_id', '!=', False),
                                                              ('partner_id.parent_id', '!=', False),
                                                              ('id', 'not in', sale_order.water_meter_id.ids)
                                                              ])
        _logger.info("Total Meters: %s" % len(meters.ids))
        meter_create = 0
        for meter in meters:
            try:
                team_id = False
                user_id = False
                zone_id = meter.partner_id.zone_id if meter.partner_id.zone_id else meter.partner_id.parent_id.zone_id
                if zone_id.team_id:
                    team_id = zone_id.team_id.id
                order_line = [(0, 0, {'product_id': product.id, 'product_uom_qty': 0})]
                vals = {'water_meter_id': meter.id,
                        'partner_id': meter.partner_id.parent_id.id,
                        'partner_invoice_id': meter.partner_id.id,
                        'partner_shipping_id': meter.partner_id.id,
                        'team_id': team_id,
                        'user_id': user_id,
                        'order_line': order_line
                        }
                self.env['sale.order'].sudo().create(vals)
                meter_create += 1
            except Exception as e:
                _logger.error(e)
                pass
        _logger.info("%s Meters Create Success" % meter_create)
        _logger.info("------ End Create Sale Quotation ------")

    def _discount_first_order(self, price=None):
        for order in self:
            _logger.info("_discount_first_order")
            discount_first_order = self.env['ir.config_parameter'].sudo().get_param(
                'qwaco.allow_discount_first_order') or False
            if discount_first_order and discount_first_order.lower() == 'true':
                excluded_water_meter = self.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.excluded_water_meter_discount_first_order', [])
                if excluded_water_meter and len(literal_eval(excluded_water_meter)) > 0 and order.water_meter_id \
                    and order.water_meter_id.id in literal_eval(excluded_water_meter):
                    rule_discount = False
                else:
                    rule_discount = True
                product_discount = self.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.sale_product_discount_first_order') or False
                quantity_discount = self.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.quantity_discount_first_order') or False
                if product_discount and quantity_discount and rule_discount:
                    is_first_order = self.env['sale.order'].sudo().search([('state', 'in', ('sale', 'done')),
                                                                           ('water_meter_id', '=', order.water_meter_id.id),
                                                                           ('id', '!=', order.id)], limit=1)
                    if not is_first_order:
                        order_line_not_discount = order.order_line.filtered(
                            lambda l: l.product_id.id != int(product_discount))
                        sum_quantity = sum(order_line_not_discount.mapped('product_uom_qty')) or 0
                        if sum_quantity > 0:
                            quantity = sum_quantity if float(quantity_discount) > sum_quantity \
                                else float(quantity_discount)
                            quantity = -1 * quantity
                            discount_line_first_order = order.order_line.filtered(
                                lambda l: l.product_id.id == int(product_discount))
                            if price and float(price) > 0:
                                price_unit = price
                            else:
                                price_unit = order_line_not_discount[0].price_unit
                            if discount_line_first_order:
                                if discount_line_first_order.product_uom_qty != quantity:
                                    discount_line_first_order.write({'product_uom_qty': quantity,
                                                                     'price_unit': price_unit
                                                                     })
                            else:
                                order.write({'order_line': [
                                    (0, False, {
                                        'product_id': int(product_discount),
                                        'product_uom_qty': quantity,
                                        'price_unit': price_unit
                                    })
                                ]})

    def get_discount_amount(self):
        for order in self:
            # product_discount = self.env['ir.config_parameter'].sudo().get_param(
            #     'qwaco.sale_product_discount_first_order') or False
            # amount_discount = 0
            # if product_discount:
            #     amount_discount = order.order_line.filtered(lambda l: l.product_id.id == int(product_discount)).price_subtotal or 0
            amount_discount = 0
            for line in order.order_line.filtered(lambda x: x.product_uom_qty < 0):
                amount_discount += abs(line.price_subtotal)
            return amount_discount

    def _action_cancel(self):
        for order in self:
            if order.water_meter_id:
                meter_quantity = self.env['qwaco.water.meter.quantity.history'].sudo().search([('order_id', '=', order.id),
                                                                                               ('water_meter_id', '=', order.water_meter_id.id)],
                                                                                                 limit=1, order="id desc")
                if meter_quantity and meter_quantity.type == 'addition':
                    qty = meter_quantity.new_quantity - meter_quantity.old_quantity
                    old_qty = order.water_meter_id.balance
                    new_qty = order.water_meter_id.balance - qty
                    order.water_meter_id.with_context(tracking_disable=True).write({'balance': new_qty})
                    vals = {'water_meter_id': order.water_meter_id.id,
                            'old_quantity': old_qty,
                            'new_quantity': new_qty,
                            'order_id': order.id,
                            'type': 'deduction'
                            }
                    self.env['qwaco.water.meter.quantity.history'].create(vals)
        return super(SaleOrder, self)._action_cancel()

    def _prepare_paid_values(self):
        return {
            'is_paid': True,
            'paid_date': fields.Datetime.now()
        }
