# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ReminderCategory(models.Model):
    _name = "qwaco.reminder.category"
    _description = "Reminder Category"

    name = fields.Char("Name")
    sequence = fields.Integer("Sequence", default=0)


class SaleOrderReminder(models.Model):
    _name = "qwaco.sale.order.reminder"
    _description = "Sale Order Reminder"

    order_id = fields.Many2one('sale.order', required=True, ondelete="cascade", copy=False)
    reminder_category_id = fields.Many2one('qwaco.reminder.category', required=True, ondelete="cascade", copy=False)
    user_id = fields.Many2one('res.users', string="User Reminder", ondelete="cascade", copy=False)
    reminder_date = fields.Date(string="Reminder Date", copy=False)
    actual_reminder_date = fields.Date(string="Actual Reminder Date", copy=False)
    is_processed = fields.Boolean(
        string="Is processed", help="Has the reminder been processed", default=False)

    _sql_constraints = [
        ('order_reminder_uniq', 'unique(order_id, reminder_category_id)',
         'Constraints with the same reminder are unique per order.'),
    ]