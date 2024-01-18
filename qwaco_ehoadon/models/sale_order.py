from odoo import models, api, fields, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ehoadon_ids = fields.One2many('qwaco.ehoadon', 'order_id', string="eHoadon", copy=False)
    ehoadon_guid = fields.Char('Invoice GUID', related='ehoadon_ids.invoice_guid')
    ehoadon_form = fields.Char('Invoice Form', related='ehoadon_ids.invoice_form')
    ehoadon_serial = fields.Char('Invoice Serial', related='ehoadon_ids.invoice_serial')
    ehoadon_no = fields.Char('Invoice No', related='ehoadon_ids.invoice_no')
    ehoadon_mtc = fields.Char('MTC', related='ehoadon_ids.mtc')

    def _send_einvoice_automation(self):
        for record in self:
            if record.state in ['sale', 'done'] and not record.ehoadon_ids:
                return self.env['qwaco.ehoadon'].with_delay(max_retries=1, channel='root.ehoadon', eta=60*5).send_invoice_to_ws(record)

    def edit_einvoice(self,order_ids):
        for record in order_ids:
            if record.state in ['sale', 'done'] and record.ehoadon_ids:
                return self.env['qwaco.ehoadon'].with_context(fix_code=124).send_invoice_to_ws(record)

    def re_send_einvoice(self,order_ids):
        for record in order_ids:
            if record.state in ['sale', 'done'] and record.ehoadon_ids:
                return self.env['qwaco.ehoadon'].with_context(fix_code=200).send_invoice_to_ws(record)