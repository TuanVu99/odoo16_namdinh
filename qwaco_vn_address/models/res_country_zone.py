# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResCountryZone(models.Model):
    _name = "res.country.zone"
    _description = _("Address: Zone")
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
    district_id = fields.Many2one(
        'res.country.state.district',
        required=True,
        domain="[('state_id', '=', state_id)]"
    )
    ward_id = fields.Many2one(
        'res.country.ward',
        required=True,
        domain="[('district_id', '=', district_id)]"
    )
    name = fields.Char(
        required=True,
        string="Zone Name",
        help="Administrative divisions of a country. E.g. Fed. State, Department, Canton",
        translate=True
    )
    code = fields.Char(
        size=3,
        required=True,
        string="Zone Code",
    )