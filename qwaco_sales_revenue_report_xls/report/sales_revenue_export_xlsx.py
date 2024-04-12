# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz

from ...report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)


class PartnerExportXlsx(models.AbstractModel):
    _name = "report.qwaco_sales_revenue_report_xls.qwaco_sales_revenue_xlsx"
    _description = "Report xlsx helpers"
    _inherit = "report.report_xlsx.abstract"

    def _get_ws_params(self, wb, data, objects):

        sales_revenue_template = {
            "order_name": {
                "header": {
                    "value": "Số hoá đơn",
                },
                "data": {
                    "value": self._render("line['order_name']"),
                },
                "width": 16,
            },
            "customer_name": {
                "header": {
                    "value": "Tên khách hàng",
                },
                "data": {
                    "value": self._render("line['customer_name']"),
                },
                "width": 36,
            },
            "water_meter": {
                "header": {
                    "value": "Mã đồng hồ",
                },
                "data": {
                    "value": self._render("line['water_meter']"),
                },
                "width": 16,
            },
            "order_date": {
                "header": {
                    "value": "Ngày ghi nước",
                },
                "data": {
                    "value": self._render("line['order_date']"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 14,
            },
            "paid_date": {
                "header": {
                    "value": "Ngày thanh toán",
                },
                "data": {
                    "value": self._render("line['paid_date']"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 14,
            },
            "invoice_date": {
                "header": {
                    "value": "Ngày xuất hoá đơn",
                },
                "data": {
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 14,
            },
            "customer_address": {
                "header": {
                    "value": "Địa chỉ",
                },
                "data": {
                    "value": self._render("line['customer_address']"),
                },
                "width": 42,
            },
            "vat": {
                "header": {
                    "value": "Mã số thuế",
                },
                "data": {
                    "value": self._render("line['vat']"),
                },
                "width": 20,
            },
            "pricelist": {
                "header": {
                    "value": "Loại hàng hoá",
                },
                "data": {
                    "value": self._render("line['pricelist']"),
                },
                "width": 30,
            },
            "old_quantity": {
                "header": {
                    "value": "Chỉ số cũ (m3)",
                },
                "data": {
                    "value": self._render("line['old_quantity']"),
                },
                "width": 14,
            },
            "new_quantity": {
                "header": {
                    "value": "Chỉ số mới (m3)",
                },
                "data": {
                    "value": self._render("line['new_quantity']"),
                },
                "width": 14,
            },
            "quantity": {
                "header": {
                    "value": "Lượng nước sử dụng (m3)",
                },
                "data": {
                    "value": self._render("line['quantity']"),
                },
                "width": 14,
            },
            "price_unit": {
                "header": {
                    "value": "Đơn giá",
                },
                "data": {
                    "value": self._render("line['price_unit']"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 14,
            },
            "discount_amount": {
                "header": {
                    "value": "Giảm giá",
                },
                "data": {
                    "value": self._render("line['discount_amount']"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 14,
            },
            "subtotal_amount": {
                "header": {
                    "value": "Thành tiền",
                },
                "data": {
                    "value": self._render("line['subtotal_amount']"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 14,
            },
            "tax_amount": {
                "header": {
                    "value": "Thuế GTGT (5%)",
                },
                "data": {
                    "value": self._render("line['tax_amount']"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 14,
            },
            "total_amount": {
                "header": {
                    "value": "Tổng tiền thanh toán",
                },
                "data": {
                    "value": self._render("line['total_amount']"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 14,
            },
            "deduct_amount": {
                "header": {
                    "value": "Khấu trừ khác",
                },
                "data": {
                    "value": self._render("line['deduct_amount']"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 14,
            },
            "total_paid": {
                "header": {
                    "value": "Tổng tiền cần thanh toán",
                },
                "data": {
                    "value": self._render("line['total_paid']"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 14,
            },
            "payment_type": {
                "header": {
                    "value": "Hình thức thanh toán",
                },
                "data": {
                    "value": self._render("line['payment_type']"),
                },
                "width": 20,
            },
        }

        wanted_list = ["order_name", "customer_name", "water_meter", "order_date", "paid_date", "invoice_date",
                       "customer_address", "vat", "pricelist", "old_quantity", "new_quantity", "quantity",
                       "price_unit", "discount_amount", "subtotal_amount", "tax_amount", "total_amount", "deduct_amount", "total_paid", "payment_type"]
        ws_params = {
            "ws_name": "Sales Revenue",
            "generate_ws_method": "_qwaco_sales_revenue_report",
            "title": "Qwaco Sales Revenue",
            "wanted_list": wanted_list,
            "col_specs": sales_revenue_template,
        }

        return [ws_params]

    def get_row_data(self, date_start, date_end):
        lines = []
        tz = pytz.timezone('Asia/Ho_Chi_Minh')
        tz_utc = pytz.timezone('UTC')
        date_start_local = tz.localize(datetime.combine(date_start, datetime.min.time()))
        date_start = date_start_local.astimezone(tz_utc).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        date_end_local = tz.localize(datetime.combine(date_end, datetime.max.time()))
        date_end = date_end_local.astimezone(tz_utc).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        print(date_start)
        print(date_end)
        orders = self.env['sale.order'].sudo().search([('state', 'in', ['sale', 'done']),
                                                        ('create_date', '>=', date_start),
                                                        ('create_date', '<=', date_end)], order="id desc")
        for order in orders:
            payment_type = "Trả sau"
            if order.payment_term_id and order.payment_term_id.code == 'pay_now':
                payment_type = "Tiền mặt"
            old_quantity = 0
            new_quantity = 0
            if order.water_meter_quantity_ids:
                for water_meter_quantity in order.water_meter_quantity_ids.filtered(lambda l: l.type == 'addition'):
                    old_quantity = water_meter_quantity.old_quantity
                    new_quantity = water_meter_quantity.new_quantity
                    continue
            quantity = new_quantity - old_quantity
            price_unit = 0
            discount_amount = 0
            deduct_amount = 0
            for line in order.order_line.filtered(lambda l: l.price_total > 0):
                price_unit = line.price_unit
                continue
            for line in order.order_line.filtered(lambda l: l.price_total < 0):
                discount_amount = abs(line.price_subtotal)
                continue
            subtotal_amount = quantity * price_unit - discount_amount
            vals = {
                'order_name': order.name,
                'customer_name': order.partner_invoice_id.name,
                'customer_address': order.partner_invoice_id.vietnam_full_address,
                'vat': order.partner_id.vat if order.partner_id.vat else "",
                'water_meter': order.water_meter_id.name,
                'order_date': order.date_order.astimezone(tz).strftime(DEFAULT_SERVER_DATE_FORMAT),
                'paid_date': order.paid_date.astimezone(tz).strftime(DEFAULT_SERVER_DATE_FORMAT) if order.paid_date else "",
                'invoice_date': order.ehoadon_ids[0].create_date.astimezone(tz).strftime(DEFAULT_SERVER_DATE_FORMAT) if order.ehoadon_ids else "",
                'pricelist': order.pricelist_id.name,
                'old_quantity': old_quantity,
                'new_quantity': new_quantity,
                'quantity': quantity,
                'price_unit': price_unit,
                'discount_amount': discount_amount,
                'subtotal_amount': subtotal_amount,
                'tax_amount': order.amount_tax,
                'total_amount': order.amount_total,
                'deduct_amount': deduct_amount,
                'total_paid': order.amount_total - deduct_amount,
                'payment_type': payment_type
            }
            lines.append(vals)
        return lines

    def _qwaco_sales_revenue_report(self, workbook, ws, ws_params, data, objects):

        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        ws_params["title"] = "Qwaco Sales Revenue"
        row_pos = self._write_ws_title(ws, row_pos, ws_params)
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_yellow_left"],
        )
        ws.freeze_panes(row_pos, 0)

        wl = ws_params["wanted_list"]

        report = objects
        date_start = report.date_start
        date_end = report.date_end
        lines = self.get_row_data(date_start, date_end)
        for line in lines:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={
                    "line": line,
                },
                default_format=FORMATS["format_tcell_left"],
            )