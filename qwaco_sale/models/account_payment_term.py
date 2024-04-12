# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    code = fields.Selection([('pay_now', 'Pay Now'), ('pay_later', 'Pay Later')])

