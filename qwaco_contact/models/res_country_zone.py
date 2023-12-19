# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResCountryZone(models.Model):
    _inherit = "res.country.zone"

    sequence_id = fields.Many2one('ir.sequence', string='Customer Code IDs Sequence', copy=False, required=True,
                                  ondelete='restrict')