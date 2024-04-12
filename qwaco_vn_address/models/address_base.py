# -*- coding: utf-8 -*-
from odoo import models, fields, api, modules

import xlrd
import os

base_path = os.path.dirname(modules.get_module_path('qwaco_vn_address'))

class CountryState(models.Model):
    _inherit = 'res.country.state'

    district_ids = fields.One2many('res.country.state.district', 'state_id', 'Quận(Huyện)')
