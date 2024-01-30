from odoo import models, api, fields, _

from odoo.exceptions import UserError, ValidationError


class PrintTemWizard(models.TransientModel):
    _name = 'qr.partner.info'

    partner_ids = fields.Many2many('res.partner', string='Khách hàng')
    water_meter_ids = fields.Many2many('qwaco.water.meter', compute="compute_water_meter",string="Đồng hồ nước")
    ward_id = fields.Many2one('res.country.ward',string="Xã/Phường")
    zone_id = fields.Many2many('res.country.zone',string="Thôn/Xóm", domain="[('ward_id', '=', ward_id)]")
    partner_info = fields.Boolean('In thông tin khách hàng')
    water_meter_info = fields.Boolean('In thông tin đồng hồ')
    print_all = fields.Boolean('In tất cả', default=False)

    @api.depends('partner_ids')
    @api.onchange('partner_ids')
    def compute_water_meter(self):
        if self.partner_ids:
            sub_id =[]
            sql = f'''select qwm.id
                        from qwaco_water_meter qwm
                             left join res_partner rp on qwm.partner_id = rp.id 
                        where rp.parent_id in %s and rp.type = 'other' '''
            self._cr.execute(sql,[tuple(self.partner_ids.ids + [0, 0])])
            rec = self._cr.dictfetchall()
            if rec:
                sub_id = [r['id'] for r in rec]
            self.water_meter_ids =[(6, 0, sub_id)]

        else: self.water_meter_ids = None

    @api.onchange('zone_id','print_all')
    def compute_print_all(self):
        if self.print_all == True and self.ward_id:
            sql = '''select id 
                    from res_partner 
                    where active = 't' 
                          and parent_id is null 
                          and type = 'contact' 
                          and zone_id in %s
                     '''
            self._cr.execute(sql, [tuple(self.zone_id.ids + [0, 0])])
            rec = self._cr.dictfetchall()
            partner = [r['id'] for r in rec]
            self.partner_ids = partner
        if self.print_all == False:
            self.partner_ids =False

    def export_report(self):
        self.ensure_one()
        if not self.partner_info and not self.water_meter_info:
            raise UserError("Vui lòng tích chọn thông tin để in mã QR !")
        report = self.env.ref('qwaco_sale.in_tem_product').report_action(self)
        return report