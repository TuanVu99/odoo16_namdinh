# -*- coding: utf-8 -*-

from datetime import timedelta, date, datetime
import base64

import os
from io import BytesIO
import openpyxl
from openpyxl.styles import NamedStyle, Font, Border, Side, Alignment

from openpyxl.worksheet import filters
from odoo import api, fields, models
import pandas as pd
import os,io
from io import BytesIO

class SaleListReport(models.TransientModel):
    _name = 'sale.resend.ehoadon'
    _description = 'Báo cáo tồn kho vật tư'

    def re_send_confirm(self):
        return self.env['sale.order'].re_send_einvoice()

