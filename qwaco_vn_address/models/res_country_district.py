# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResCountryDistrict(models.Model):
    _name = "res.country.state.district"
    _description = _("Address: District")
    _order = "code"

    @api.model
    def _get_default_vietnam_country(self):
        ids = self.env['res.country'].search([('code', '=', 'VN')])
        return ids[0]

    country_id = fields.Many2one(
        'res.country',
        required=True,
        default=_get_default_vietnam_country,
    )
    state_id = fields.Many2one(
        'res.country.state',
        required=True,
    )
    name = fields.Char(
        required=True,
        string="Dist. Name",
        translate=True
    )
    code = fields.Char(
        size=3,
        required=True,
        string="Dist. Code",
    )
