from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'
    district_id = fields.Many2one('res.country.state.district', domain="[('state_id', '=?', state_id)]")
    ward_id = fields.Many2one('res.country.ward', domain="[('district_id', '=?', district_id)]")
    zone_id = fields.Many2one('res.country.zone', domain="[('ward_id', '=?', ward_id)]")
    vietnam_full_address = fields.Text(
        compute='_compute_vietnam_full_address',
        string="VN-Partner Address",
    )

    @api.depends("street", "zone_id", "ward_id", "district_id", "state_id", "country_id")
    def _compute_vietnam_full_address(self):
        for rec in self:
            address = ""
            if rec.street:
                address += "{} ".format(rec.street + ",")
            if rec.zone_id and rec.zone_id.name:
                address += "{} ".format(rec.zone_id.name + ",")
            if rec.ward_id and rec.ward_id.name:
                address += "{} ".format(rec.ward_id.name + ",")
            if rec.district_id and rec.district_id.name:
                address += "{} ".format(rec.district_id.name + ",")
            if rec.state_id and rec.state_id.name:
                address += "{} ".format(rec.state_id.name + ",")
            # if rec.country_id and rec.country_id.name:
            #     address += "{} ".format(rec.country_id.name + ",")
            rec.vietnam_full_address = address.strip(", ")
