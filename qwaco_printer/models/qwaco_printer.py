from odoo import models, fields, api

class QwacoPrinter(models.Model):
    _name = 'qwaco.printer'
    _description = 'Qwaco Printer'

    name = fields.Char(string='Name', required=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    model_name = fields.Char(string='Model', required=True, readonly=True, related='model_id.model')
    printer_name = fields.Char(string='Printer Name', required=True)
    printer_type = fields.Selection([('thermal', 'Thermal Printer')], string='Printer Type', required=True, default='thermal')
    active = fields.Boolean(string='Active', default=True)

    @api.model
    def get_prepared_data(self, args):
        qwaco_printer_id = args.get('qwaco_printer_id')
        res_id = args.get('res_id')
        printer = self.browse(qwaco_printer_id)
        order = self.env[printer.model_name].browse(res_id)
        # return data to print
        if order:
            data = self.env['ir.qweb']._render('qwaco_printer.sale_order_receipt', {'o': order, 'user': self.env.user})
            return data
        return False




