from odoo import models, fields, api
from ast import literal_eval

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_default_vietnam_country(self):
        country = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
        return country.id

    # @api.model
    # def _search_state(self):
    #     state_ids = self.env['ir.config_parameter'].sudo().get_param(
    #         'qwaco.filter_state') or False
    #     if state_ids and len(literal_eval(state_ids)):
    #         domain = "[('country_id', '=?', country_id), ('id', 'in', %s)]" % state_ids
    #     else:
    #         domain = "[('country_id', '=?', country_id)]"
    #     return domain
    #
    # @api.model
    # def _search_district(self):
    #     district_ids = self.env['ir.config_parameter'].sudo().get_param(
    #         'qwaco.filter_district') or False
    #     if district_ids and len(literal_eval(district_ids)) > 0:
    #         domain = "[('state_id', '=?', state_id), ('id', 'in', %s)]" % district_ids
    #     else:
    #         domain = "[('state_id', '=?', state_id)]"
    #     return domain
    #
    # @api.model
    # def _search_ward(self):
    #     ward_ids = self.env['ir.config_parameter'].sudo().get_param(
    #         'qwaco.filter_ward') or False
    #     if ward_ids and len(literal_eval(ward_ids)) > 0:
    #         domain = "[('district_id', '=?', district_id), ('id', 'in', %s)]" % ward_ids
    #     else:
    #         domain = "[('district_id', '=?', district_id)]"
    #     return domain
    #
    # @api.model
    # def _search_zone(self):
    #     zone_ids = self.env['ir.config_parameter'].sudo().get_param(
    #         'qwaco.filter_zone') or False
    #     if zone_ids and len(literal_eval(zone_ids)) > 0:
    #         domain = "[('ward_id', '=', ward_id), ('id', 'in', %s)]" % zone_ids
    #     else:
    #         domain = "[('ward_id', '=?', ward_id)]"
    #     return domain

    def _employee_ids_domain(self):
        # employee_ids is considered a safe field and as such will be fetched as sudo.
        # So try to enforce the security rules on the field to make sure we do not load employees outside of active companies
        return [('company_id', 'in', self.env.company.ids + self.env.context.get('allowed_company_ids', []))]

    customer_code = fields.Char(string="Customer Code", readonly=True, copy=False)
    contract_no = fields.Char(string="Contract No", readonly=True, copy=False)
    popular_name = fields.Char(string="Popular Name", copy=False)
    water_meter_ids = fields.One2many('qwaco.water.meter', 'partner_id', string='Water Meter')
    water_meter_child_ids = fields.One2many('qwaco.water.meter', compute='_compute_water_meter_child_ids', string="Water Meter List", readonly=False)
    # state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',
    #                            domain=_search_state)
    # district_id = fields.Many2one('res.country.state.district', domain=_search_district)
    # ward_id = fields.Many2one('res.country.ward', domain=_search_ward)
    # zone_id = fields.Many2one('res.country.zone', domain=_search_zone)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    district_id = fields.Many2one('res.country.state.district')
    ward_id = fields.Many2one('res.country.ward')
    zone_id = fields.Many2one('res.country.zone')
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',
                                 domain="[('code', '=', 'VN')]")
    id_number = fields.Char(string='Identification Number', index=True, copy=False,
                      help="The ID itself. For example, Driver License number of this person")

    _sql_constraints = [
        ('contract_no_uniq', 'unique(contract_no)',
         'Constraints with the same contract no are unique per contact.'),
        ('id_number_uniq', 'unique(id_number)',
         'Constraints with the same id number are unique per contact.')
    ]

    @api.model
    def default_get(self, fields):
        vals = super(ResPartner, self).default_get(fields)
        country = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
        vals['country_id'] = country.id
        return vals

    @api.onchange('type')
    def _onchange_type(self):
        for partner in self:
            self.state_id = False
            self.district_id = False
            self.ward_id = False
            self.zone_id = False
            self.street = False
            domain = [('country_id', '=?', partner.country_id.id)]
            if not partner.type or (partner.type and partner.type != 'invoice'):
                state_ids = self.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.filter_state') or False
                if state_ids and len(literal_eval(state_ids)):
                    domain += [('id', 'in', literal_eval(state_ids))]
            return {'domain': {'state_id': domain}}

    @api.onchange('country_id')
    def _onchange_country_id(self):
        for partner in self:
            partner.state_id = False
            domain = [('country_id', '=?', partner.country_id.id)]
            if not partner.type or (partner.type and partner.type != 'invoice'):
                state_ids = self.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.filter_state') or False
                if state_ids and len(literal_eval(state_ids)):
                    domain += [('id', 'in', literal_eval(state_ids))]
            return {'domain': {'state_id': domain}}

    @api.onchange('state_id')
    def _onchange_state_id(self):
        for partner in self:
            partner.district_id = False
            domain = [('state_id', '=?', partner.state_id.id)]
            if not partner.type or (partner.type and partner.type != 'invoice'):
                district_ids = self.env['ir.config_parameter'].sudo().get_param(
                        'qwaco.filter_district') or False
                if district_ids and len(literal_eval(district_ids)) > 0:
                    domain += [('id', 'in', literal_eval(district_ids))]
            return {'domain': {'district_id': domain}}

    @api.onchange('district_id')
    def _onchange_district_id(self):
        for partner in self:
            partner.ward_id = False
            domain = [('district_id', '=?', partner.district_id.id)]
            if not partner.type or (partner.type and partner.type != 'invoice'):
                ward_ids = self.env['ir.config_parameter'].sudo().get_param(
                        'qwaco.filter_ward') or False
                if ward_ids and len(literal_eval(ward_ids)) > 0:
                    domain += [('id', 'in', literal_eval(ward_ids))]
            return {'domain': {'ward_id': domain}}

    @api.onchange('ward_id')
    def _onchange_ward_id(self):
        for partner in self:
            partner.zone_id = False
            domain = [('ward_id', '=?', partner.ward_id.id)]
            if not partner.type or (partner.type and partner.type != 'invoice'):
                zone_ids = self.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.filter_zone') or False
                if zone_ids and len(literal_eval(zone_ids)) > 0:
                    domain += [('id', 'in', literal_eval(zone_ids))]
            return {'domain': {'zone_id': domain}}


    @api.depends()
    def _compute_water_meter_child_ids(self):
        for record in self:
            record.water_meter_child_ids = self.env['qwaco.water.meter'].sudo().\
                search([('partner_id', 'in', record.child_ids.ids)])

    @api.model
    def create(self, vals):
        if vals.get('district_id') and vals.get('ward_id') and vals.get('zone_id') and \
                (not vals.get('type') or (vals.get('type') and vals.get('type') != 'invoice')):
            district_code = self.env['res.country.state.district'].browse(int(vals.get('district_id'))).code
            ward_code = self.env['res.country.ward'].browse(int(vals.get('ward_id'))).code
            zone_code = self.env['res.country.zone'].browse(int(vals.get('zone_id'))).code
            sequence = self.env['res.country.zone'].browse(int(vals.get('zone_id'))).sequence_id.next_by_id()
            vals['customer_code'] = district_code + ward_code + zone_code + sequence
        res = super(ResPartner, self).create(vals)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        for partner in partners:
            if partner.district_id and partner.ward_id and partner.zone_id and partner.type != 'invoice':
                district_code = partner.district_id.code
                ward_code = partner.ward_id.code
                zone_code = partner.zone_id.code
                sequence = partner.zone_id.sequence_id.next_by_id()
                partner.customer_code = district_code + ward_code + zone_code + sequence
        return partners

    @api.onchange('child_ids')
    def onchange_child_ids(self):
        for child in self.child_ids:
            if not child.contract_no and child.type != 'invoice':
                child.contract_no = self.env['ir.sequence'].next_by_code('res.partner.contract_no')

    def write(self, vals):
        result = super(ResPartner, self).write(vals)
        for partner in self:
            if partner.child_ids:
                for child in partner.child_ids:
                    if not child.contract_no and child.type != 'invoice':
                        child.contract_no = self.env['ir.sequence'].next_by_code('res.partner.contract_no')
        return result

    def _get_contact_name(self, partner, name):
        return "%s" % name