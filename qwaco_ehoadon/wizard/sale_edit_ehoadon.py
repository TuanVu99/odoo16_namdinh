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
    _name = 'sale.edit.ehoadon'
    _description = 'Báo cáo tồn kho vật tư'

    file_data = fields.Binary(string='File')
    type = fields.Selection([('sign',"HĐ đã phát hành"),('no_sign',"HĐ chưa phát hành")],string="Loại HĐ cần điều chỉnh",default="no_sign")

    def edit_ehoadon(self):
        data = base64.b64decode(self.file_data)
        df = pd.read_excel(io.BytesIO(data))

        order_ids =[]
        # Xử lý dữ liệu từ DataFrame df, ví dụ:
        if self.type == 'sign':
            for row in df['Invoice']:
                einvoice_sign = self.env['qwaco.ehoadon'].search([
                    ('invoice_no' ,'=',row),
                    ('write_date', '>=',datetime.strptime('2024-01-01 00:00:00','%Y-%m-%d 00:00:00')),
                    ('write_date', '<=',
                     datetime.strptime('2024-01-31 23:59:59','%Y-%m-%d 23:59:59')),
                    ])
                order_ids.append(einvoice_sign.order_id)
            return self.env['sale.order'].edit_einvoice(order_ids)
        else:
            einvoice_no = []
            for row in df['Invoice']:
                einvoice_no.append(row)
            einvoice_sign = self.env['qwaco.ehoadon'].search([
                    ('invoice_no' ,'not in',einvoice_no),
                    ('write_date', '>=',datetime.strptime('2024-01-01 00:00:00','%Y-%m-%d 00:00:00')),
                    ('write_date', '<=',
                     datetime.strptime('2024-01-31 23:59:59','%Y-%m-%d 23:59:59')),
                    ])
            for einvoice in einvoice_sign:
                order_ids.append(einvoice.order_id)
            return self.env['sale.order'].re_send_einvoice(order_ids)


