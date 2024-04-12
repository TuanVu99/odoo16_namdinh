# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import ast


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    qwaco_filter_state_ids = fields.Many2many('res.country.state', string='Filter State', domain="[('country_id.code', '=', 'VN')]")
    qwaco_filter_district_ids = fields.Many2many('res.country.state.district', string='Filter District')
    qwaco_filter_ward_ids = fields.Many2many('res.country.ward', string='Filter Ward')
    qwaco_filter_zone_ids = fields.Many2many('res.country.zone', string='Filter Zone')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        state_ids = self.env['ir.config_parameter'].sudo().get_param('qwaco.filter_state') or False
        #state
        if state_ids:
            res.update(
                qwaco_filter_state_ids=[(6, 0, ast.literal_eval(state_ids))],
            )
        else:
            res.update(
                qwaco_filter_state_ids=[(6, 0, [])],
            )
        #district
        district_ids = self.env['ir.config_parameter'].sudo().get_param('qwaco.filter_district') or False
        if district_ids:
            res.update(
                qwaco_filter_district_ids=[(6, 0, ast.literal_eval(district_ids))],
            )
        else:
            res.update(
                qwaco_filter_district_ids=[(6, 0, [])],
            )
        #ward
        ward_ids = self.env['ir.config_parameter'].sudo().get_param('qwaco.filter_ward') or False
        if ward_ids:
            res.update(
                qwaco_filter_ward_ids=[(6, 0, ast.literal_eval(ward_ids))],
            )
        else:
            res.update(
                qwaco_filter_ward_ids=[(6, 0, [])],
            )
        # zone
        zone_ids = self.env['ir.config_parameter'].sudo().get_param('qwaco.filter_zone') or False
        if zone_ids:
            res.update(
                qwaco_filter_zone_ids=[(6, 0, ast.literal_eval(zone_ids))],
            )
        else:
            res.update(
                qwaco_filter_zone_ids=[(6, 0, [])],
            )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('qwaco.filter_state', self.qwaco_filter_state_ids.ids)
        set_param('qwaco.filter_district', self.qwaco_filter_district_ids.ids)
        set_param('qwaco.filter_ward', self.qwaco_filter_ward_ids.ids)
        set_param('qwaco.filter_zone', self.qwaco_filter_zone_ids.ids)
