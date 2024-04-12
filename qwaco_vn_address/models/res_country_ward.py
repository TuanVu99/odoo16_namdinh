# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResCountryWard(models.Model):
    _name = "res.country.ward"
    _description = _("Address: Ward")
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
    name = fields.Char(
        required=True,
        string="War. Name",
        help="Administrative divisions of a country. E.g. Fed. State, Department, Canton",
        translate=True
    )
    code = fields.Char(
        size=3,
        required=True,
        string="War. Code",
    )
