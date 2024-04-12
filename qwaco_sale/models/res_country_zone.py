# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResCountryZone(models.Model):
    _inherit = "res.country.zone"

    team_id = fields.Many2one('crm.team', 'Sales Team', ondelete="cascade", copy=False, required=True)
