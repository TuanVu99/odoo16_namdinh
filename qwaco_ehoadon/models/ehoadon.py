from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from .dto.invoice import InvoiceDTO
from .dto.invoice_details import InvoiceDetailsDTO
from .dto.cmd_obj import CommandObjectDTO
from .dto.data import DataDTO
from base64 import b64encode, b64decode
from dateutil.relativedelta import relativedelta

import json
import pytz
import datetime
import requests
import logging

_logger = logging.getLogger(__name__)

TIMEOUT = 60


class eHoadon(models.Model):
    _name = "qwaco.ehoadon"
    _description = "Qwaco eHoadon"

    order_id = fields.Many2one('sale.order', 'Sale Order')
    invoice_guid = fields.Char('Invoice GUID')
    invoice_form = fields.Char('Invoice Form')
    invoice_serial = fields.Char('Invoice Serial')
    invoice_no = fields.Char('Invoice No')
    mtc = fields.Char('MTC')

    def get_first_date_of_month(self, year, month):
        """Return the first date of the month.

        Args:
            year (int): Year
            month (int): Month

        Returns:
            date (datetime): First date of the current month
        """
        first_date = datetime.datetime(year, month, 1)
        return first_date.strftime("%d/%m/%Y")

    def get_last_date_of_month(self, year, month):
        """Return the last date of the month.

        Args:
            year (int): Year, i.e. 2022
            month (int): Month, i.e. 1 for January

        Returns:
            date (datetime): Last date of the current month
        """
        next_month = datetime.datetime(year, month, 28) + datetime.timedelta(days=4)
        last_date = next_month - datetime.timedelta(days=next_month.day)
        return last_date.strftime("%d/%m/%Y")

    def _generate_template(self, sale_order):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        ehoadon_tax_rate = get_param('ehoadon.tax_rate', '10')
        ehoadon_tax_rate_id = get_param('ehoadon.tax_rate_id', '3')
        ehoadon_invoice_form = get_param('ehoadon.invoice_form', '1')
        ehoadon_invoice_serial = get_param('ehoadon.invoice_serial', 'C23TAA')
        cmdtype = 101
        BuyerUnitName = ""
        BuyerName = "KHÁCH LẺ"
        BuyerTaxCode = ""
        ReceiverEmail = ""
        BuyerAddress = ""
        Note = ""
        invoice_string_id = str(sale_order.id)
        if sale_order.partner_id.name:
            BuyerName = sale_order.partner_id.name

        if sale_order.partner_id.email:
            ReceiverEmail = sale_order.partner_id.email

        if sale_order.partner_id.vietnam_full_address:
            BuyerAddress = sale_order.water_meter_id.partner_id.vietnam_full_address

        if sale_order.partner_id.vat:
            BuyerTaxCode = sale_order.partner_id.vat

        if sale_order.water_meter_id:
            if sale_order.water_meter_id.partner_id.vietnam_full_address:
                BuyerAddress = sale_order.water_meter_id.partner_id.vietnam_full_address

            if sale_order.water_meter_id.partner_id.name:
                BuyerName = sale_order.water_meter_id.partner_id.name
        # start filter invoice type
        partner_invoice = sale_order.partner_id.child_ids.filtered(lambda x: x.type == 'invoice')
        if partner_invoice:
            partner_invoice = partner_invoice[0] if len(partner_invoice) > 0 else partner_invoice
            if partner_invoice.vietnam_full_address:
                BuyerAddress = partner_invoice.vietnam_full_address
            if partner_invoice.name:
                BuyerName =  partner_invoice.name
        # end filter invoice type
        tz = pytz.timezone(self.env.user.tz if self.env.user.tz else "Asia/Ho_Chi_Minh")
        order_date = sale_order.date_order.astimezone(tz)
        # InvoiceDate = sale_order.write_date.astimezone(tz).isoformat('T')
        InvoiceDate = datetime.datetime.now(tz).isoformat('T')
        last_date = sale_order.water_meter_id.setting_date if sale_order.water_meter_id.setting_date else False
        current_balance = 0
        if last_date:
            diff_date = (order_date.date() - last_date).days
        user_define = {"NgayDocThangNay": order_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                       "NgayDocThangTruoc": last_date.strftime(DEFAULT_SERVER_DATE_FORMAT) if last_date else "",
                       "MaKH": sale_order.partner_id.customer_code if sale_order.partner_id.customer_code else "",
                       "SeriDongHo": sale_order.water_meter_id.name if sale_order.water_meter_id else "",
                       "ChiSoDHThangTruoc": "{:.3f}".format(round(sale_order.water_meter_id.balance, 3)),
                       "ChiSoDHThangNay": 0,
                       "SoNgaySuDung": diff_date if last_date else 0
                       }
        domain_water_meter_current = [('order_id', '!=', False),
                                        ('order_id', '=', sale_order.id),
                                        ('water_meter_id', '=', sale_order.water_meter_id.id)]
        water_meter_current = self.env['qwaco.water.meter.quantity.history'].sudo().search(domain_water_meter_current, limit=1, order="create_date desc")
        if water_meter_current and water_meter_current.type == 'addition':
            current_balance = water_meter_current.new_quantity
            user_define.update({"ChiSoDHThangNay": "{:.3f}".format(round(current_balance, 3)),
                                "ChiSoDHThangTruoc": "{:.3f}".format(round(water_meter_current.old_quantity, 3))})
        domain_water_meter_old = [('order_id', '!=', False),
                ('order_id', '!=', sale_order.id),
                ('order_id.state', 'in', ['sale', 'done']),
                ('water_meter_id', '=', sale_order.water_meter_id.id)]
        water_meter_old = self.env['qwaco.water.meter.quantity.history'].sudo().search(domain_water_meter_old, limit=1, order="create_date desc")
        if water_meter_old and water_meter_old.type == 'addition':
            order_date_old = water_meter_old.order_id.date_order.astimezone(tz)
            last_date = water_meter_old.order_id.date_order.astimezone(tz)
            qty_prev_month = water_meter_old.new_quantity
            diff_date = (order_date - order_date_old).days
            user_define.update({"NgayDocThangTruoc": order_date_old.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                "ChiSoDHThangTruoc": "{:.3f}".format(round(qty_prev_month, 3)),
                                "SoNgaySuDung": diff_date
                                })
        # end user define
        if last_date:
            d2 = order_date - relativedelta(months=1)
            d1 = last_date
            period_year = d2.year
            months = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
            count_months = []
            totalmonts = (d2.year - d1.year) * 12 + d2.month - 11 + 12 - d1.month
            for i in range(totalmonts):
                count_months.append(months[(d1.month + i - 1) % 12])
            if len(count_months) > 0:
                period_month = " & ".join(x for x in count_months)
            else:
                period_month = order_date.month
            qty_this_month = 0
            list_invoice_details = []
            for line in sale_order.order_line.filtered(lambda x: x.product_uom_qty > 0):
                # ItemName = "Nước tiêu thụ tháng {month} năm {year} từ ngày {from_date} đến ngày {to_date}".format(
                #                     month=period_month, year=period_year, from_date=period_from_date, to_date=period_to_date)
                ItemName = "Nước tiêu thụ tháng {month} năm {year}".format(
                    month=period_month, year=period_year)
                UnitName = "m3"
                Price = abs(line.price_unit)
                Qty = abs(line.product_uom_qty)
                qty_this_month = abs(line.product_uom_qty)
                DiscountRate = 0.00
                DiscountAmount = 0.00
                Amount = abs(line.price_subtotal)
                TaxAmount = abs(line.price_tax)
                IsDiscount = False
                product_line = InvoiceDetailsDTO(ItemName=ItemName, UnitName=UnitName, Qty=Qty,
                                                 Price=Price, Amount=Amount, DiscountRate=DiscountRate,
                                                 DiscountAmount=DiscountAmount,
                                                 TaxRateID=int(ehoadon_tax_rate_id), TaxRate=float(ehoadon_tax_rate),
                                                 TaxAmount=TaxAmount, IsDiscount=IsDiscount
                                                 )
                list_invoice_details.append(product_line)

            for line in sale_order.order_line.filtered(lambda x: x.product_uom_qty < 0):
                product_discount_first_order = self.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.sale_product_discount_first_order') or False
                if product_discount_first_order and line.product_id.id == int(product_discount_first_order):
                    quantity_discount = self.env['ir.config_parameter'].sudo().get_param(
                        'qwaco.quantity_discount_first_order')
                    ItemName = "Giảm giá {qty} m3 đầu tiên".format(qty=float(quantity_discount))
                else:
                    ItemName = "Khấu trừ khác"
                UnitName = "m3"
                Qty = 0.0
                Price = 0.0
                Amount = abs(line.price_subtotal)
                DiscountRate = 0.00
                DiscountAmount = 0.00
                TaxAmount = abs(line.price_tax)
                IsDiscount = True
                product_line = InvoiceDetailsDTO(ItemName=ItemName, UnitName=UnitName, Qty=Qty,
                                                 Price=Price, Amount=Amount, DiscountRate=DiscountRate,
                                                 DiscountAmount=DiscountAmount,
                                                 TaxRateID=int(ehoadon_tax_rate_id), TaxRate=float(ehoadon_tax_rate),
                                                 TaxAmount=TaxAmount, IsDiscount=IsDiscount
                                                 )
                list_invoice_details.append(product_line)
            if not current_balance > 0:
                last_balance = sale_order.water_meter_id.balance + qty_this_month
                user_define['ChiSoDHThangNay'] = "{:.3f}".format(round(last_balance, 3))
            UserDefine = json.dumps(user_define,
                                    default=lambda o: o.__dict__,
                                    ensure_ascii=False)
            invoice = InvoiceDTO(InvoiceTypeID=1, InvoiceDate=InvoiceDate, BuyerName=BuyerName, BuyerTaxCode=BuyerTaxCode,
                                 BuyerUnitName=BuyerUnitName, BuyerAddress=BuyerAddress, BuyerBankAccount="", PayMethodID=3,
                                 ReceiveTypeID=3,
                                 ReceiverEmail=ReceiverEmail, ReceiverMobile="", ReceiverAddress="", ReceiverName="",
                                 Note=Note,
                                 BillCode="", CurrencyID="VND", ExchangeRate=1.0, InvoiceForm=ehoadon_invoice_form, InvoiceSerial=ehoadon_invoice_serial,
                                 InvoiceNo=0, UserDefine=UserDefine)
            if invoice_string_id:
                command_obj = CommandObjectDTO(invoice, list_invoice_details, [], 0, invoice_string_id, InvoiceAction=8)
                data = DataDTO(CmdType=int(cmdtype), CommandObject=[command_obj])
                data_json = json.dumps(data,
                                       default=lambda o: o.__dict__,
                                       ensure_ascii=False)
                return data_json
        return None

    def send_invoice_to_ws(self, order_id):
        data_json = self._generate_template(order_id)
        if self._context.get('fix_code')==200:
            data_json = self._generate_template_re_send(order_id)
        if self._context.get('fix_code')==124:
            data_json = self._generate_template_edit(order_id)
        partnerGUID = self.env["ir.config_parameter"].sudo().get_param("ehoadon.pguid") or False
        if data_json and partnerGUID:
            _logger.info("Data json eHoadon:" + data_json)
            CommandData = str(b64encode(bytes(data_json, 'utf-8')), 'utf-8')
            data_exec = {"partnerGUID": partnerGUID,
                         "CommandData": CommandData}
            data_exec_json = json.dumps(data_exec,
                              default=lambda o: o.__dict__,
                              ensure_ascii=False)
            self.action_send_invoice_to_ws(data_exec_json, order_id)

    def action_send_invoice_to_ws(self, data_json, order_id):
        request_url = self.env["ir.config_parameter"].sudo().get_param("ehoadon.url")
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            res = requests.post(
                request_url,
                headers=headers,
                data=data_json, timeout=60)
            status = res.status_code
            if int(status) in (204, 404):  # Page not found, no response
                raise self.env['res.config.settings'].get_config_warning(
                    _("Something went wrong with your request to eHoadon"))
            else:
                _logger.info("Data response eHoadon:" + str(res.json()))
                response = res.json()
                vals = json.loads(str(b64decode(response['d']).decode('utf-8')))
                if vals['Status'] == 0:
                    obj = json.loads(vals['Object'])

                    if obj[0]['Status'] == 0:
                        self.sudo().create({"order_id": order_id.id,
                                            "invoice_guid": obj[0]['InvoiceGUID'],
                                            "invoice_form": obj[0]['InvoiceForm'],
                                            "invoice_serial": obj[0]['InvoiceSerial'],
                                            "invoice_no": obj[0]['InvoiceNo'],
                                            "mtc": obj[0]['MTC'],
                                            })
                    else:
                        _logger.error(obj[0]['MessLog'])
                        raise self.env['res.config.settings'].get_config_warning(obj[0]['MessLog'])
                else:
                    _logger.error(vals['Object'])
                    raise self.env['res.config.settings'].get_config_warning(vals['Object'])
        except requests.HTTPError as error:
            if error.response.status_code in (204, 404):
                status = error.response.status_code
                response = ""
                raise error
            else:
                _logger.exception("Bad request : %s !", error.response.content)
                if error.response.status_code in (400, 401, 410):
                    raise error
                    # _logger.error(error)
                _logger.error(_("Something went wrong with your request to eHoadon"))
                raise self.env['res.config.settings'].get_config_warning(
                    _("Something went wrong with your request to eHoadon"))
        except IOError:
            _logger.error(_("Something went wrong with your request to eHoadon"))
            raise self.env['res.config.settings'].get_config_warning(
                _("Something went wrong with your request to eHoadon"))
        return True

    def _generate_template_re_send(self, sale_order):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        ehoadon_tax_rate = get_param('ehoadon.tax_rate', '10')
        ehoadon_tax_rate_id = get_param('ehoadon.tax_rate_id', '3')
        ehoadon_invoice_form = get_param('ehoadon.invoice_form', '1')
        ehoadon_invoice_serial = get_param('ehoadon.invoice_serial', 'C23TAA')
        cmdtype = 200
        BuyerUnitName = ""
        BuyerName = "KHÁCH LẺ"
        BuyerTaxCode = ""
        ReceiverEmail = ""
        BuyerAddress = ""
        Note = ""
        invoice_string_id = str(sale_order.id)
        if sale_order.partner_id.name:
            BuyerName = sale_order.partner_id.name

        if sale_order.partner_id.email:
            ReceiverEmail = sale_order.partner_id.email

        if sale_order.partner_id.vietnam_full_address:
            BuyerAddress = sale_order.water_meter_id.partner_id.vietnam_full_address

        if sale_order.partner_id.vat:
            BuyerTaxCode = sale_order.partner_id.vat

        if sale_order.water_meter_id:
            if sale_order.water_meter_id.partner_id.vietnam_full_address:
                BuyerAddress = sale_order.water_meter_id.partner_id.vietnam_full_address

            if sale_order.water_meter_id.partner_id.name:
                BuyerName = sale_order.water_meter_id.partner_id.name
        # start filter invoice type
        partner_invoice = sale_order.partner_id.child_ids.filtered(lambda x: x.type == 'invoice')
        if partner_invoice:
            partner_invoice = partner_invoice[0] if len(partner_invoice) > 0 else partner_invoice
            if partner_invoice.vietnam_full_address:
                BuyerAddress = partner_invoice.vietnam_full_address
            if partner_invoice.name:
                BuyerName = partner_invoice.name
        # end filter invoice type
        tz = pytz.timezone(self.env.user.tz if self.env.user.tz else "Asia/Ho_Chi_Minh")
        order_date = sale_order.date_order.astimezone(tz)
        # InvoiceDate = sale_order.write_date.astimezone(tz).isoformat('T')
        InvoiceDate = datetime.datetime.now(tz).isoformat('T')
        last_date = sale_order.water_meter_id.setting_date if sale_order.water_meter_id.setting_date else False
        current_balance = 0
        if last_date:
            diff_date = (order_date.date() - last_date).days
        user_define = {"NgayDocThangNay": order_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                       "NgayDocThangTruoc": last_date.strftime(DEFAULT_SERVER_DATE_FORMAT) if last_date else "",
                       "MaKH": sale_order.partner_id.customer_code if sale_order.partner_id.customer_code else "",
                       "SeriDongHo": sale_order.water_meter_id.name if sale_order.water_meter_id else "",
                       "ChiSoDHThangTruoc": "{:.3f}".format(round(sale_order.water_meter_id.balance, 3)),
                       "ChiSoDHThangNay": 0,
                       "SoNgaySuDung": diff_date if last_date else 0
                       }
        domain_water_meter_current = [('order_id', '!=', False),
                                      ('order_id', '=', sale_order.id),
                                      ('water_meter_id', '=', sale_order.water_meter_id.id)]
        water_meter_current = self.env['qwaco.water.meter.quantity.history'].sudo().search(domain_water_meter_current,
                                                                                           limit=1,
                                                                                           order="create_date desc")
        if water_meter_current and water_meter_current.type == 'addition':
            current_balance = water_meter_current.new_quantity
            user_define.update({"ChiSoDHThangNay": "{:.3f}".format(round(current_balance, 3)),
                                "ChiSoDHThangTruoc": "{:.3f}".format(round(water_meter_current.old_quantity, 3))})
        domain_water_meter_old = [('order_id', '!=', False),
                                  ('order_id', '!=', sale_order.id),
                                  ('order_id.state', 'in', ['sale', 'done']),
                                  ('water_meter_id', '=', sale_order.water_meter_id.id)]
        water_meter_old = self.env['qwaco.water.meter.quantity.history'].sudo().search(domain_water_meter_old, limit=1,
                                                                                       order="create_date desc")
        if water_meter_old and water_meter_old.type == 'addition':
            order_date_old = water_meter_old.order_id.date_order.astimezone(tz)
            last_date = water_meter_old.order_id.date_order.astimezone(tz)
            qty_prev_month = water_meter_old.new_quantity
            diff_date = (order_date - order_date_old).days
            user_define.update({"NgayDocThangTruoc": order_date_old.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                "ChiSoDHThangTruoc": "{:.3f}".format(round(qty_prev_month, 3)),
                                "SoNgaySuDung": diff_date
                                })
        # end user define
        if last_date:
            d2 = order_date - relativedelta(months=1)
            d1 = last_date
            period_year = order_date.year
            months = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
            count_months = []
            totalmonts = (d2.year - d1.year) * 12 + d2.month - 11 + 12 - d1.month
            for i in range(totalmonts):
                count_months.append(months[(d1.month + i - 1) % 12])
            if len(count_months) > 0:
                period_month = " & ".join(x for x in count_months)
            else:
                period_month = order_date.month
            qty_this_month = 0
            list_invoice_details = []
            for line in sale_order.order_line.filtered(lambda x: x.product_uom_qty > 0):
                # ItemName = "Nước tiêu thụ tháng {month} năm {year} từ ngày {from_date} đến ngày {to_date}".format(
                #                     month=period_month, year=period_year, from_date=period_from_date, to_date=period_to_date)
                ItemName = "Nước tiêu thụ tháng {month} năm {year}".format(
                    month=period_month, year=period_year)
                UnitName = "m3"
                Price = abs(line.price_unit)
                Qty = abs(line.product_uom_qty)
                qty_this_month = abs(line.product_uom_qty)
                DiscountRate = 0.00
                DiscountAmount = 0.00
                Amount = abs(line.price_subtotal)
                TaxAmount = abs(line.price_tax)
                IsDiscount = False
                product_line = InvoiceDetailsDTO(ItemName=ItemName, UnitName=UnitName, Qty=Qty,
                                                 Price=Price, Amount=Amount, DiscountRate=DiscountRate,
                                                 DiscountAmount=DiscountAmount,
                                                 TaxRateID=int(ehoadon_tax_rate_id), TaxRate=float(ehoadon_tax_rate),
                                                 TaxAmount=TaxAmount, IsDiscount=IsDiscount,ItemTypeID=0
                                                 )
                list_invoice_details.append(product_line)

            for line in sale_order.order_line.filtered(lambda x: x.product_uom_qty < 0):
                product_discount_first_order = self.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.sale_product_discount_first_order') or False
                if product_discount_first_order and line.product_id.id == int(product_discount_first_order):
                    quantity_discount = self.env['ir.config_parameter'].sudo().get_param(
                        'qwaco.quantity_discount_first_order')
                    ItemName = "Giảm giá {qty} m3 đầu tiên".format(qty=float(quantity_discount))
                else:
                    ItemName = "Khấu trừ khác"
                UnitName = "m3"
                Qty = 0.0
                Price = 0.0
                Amount = abs(line.price_subtotal)
                DiscountRate = 0.00
                DiscountAmount = 0.00
                TaxAmount = abs(line.price_tax)
                IsDiscount = True
                product_line = InvoiceDetailsDTO(ItemName=ItemName, UnitName=UnitName, Qty=Qty,
                                                 Price=Price, Amount=Amount, DiscountRate=DiscountRate,
                                                 DiscountAmount=DiscountAmount,
                                                 TaxRateID=int(ehoadon_tax_rate_id), TaxRate=float(ehoadon_tax_rate),
                                                 TaxAmount=TaxAmount, IsDiscount=IsDiscount,ItemTypeID=0
                                                 )
                list_invoice_details.append(product_line)
            if not current_balance > 0:
                last_balance = sale_order.water_meter_id.balance + qty_this_month
                user_define['ChiSoDHThangNay'] = "{:.3f}".format(round(last_balance, 3))
            UserDefine = json.dumps(user_define,
                                    default=lambda o: o.__dict__,
                                    ensure_ascii=False)
            invoice = InvoiceDTO(InvoiceTypeID=1, InvoiceDate=InvoiceDate, BuyerName=BuyerName,
                                 BuyerTaxCode=BuyerTaxCode,
                                 BuyerUnitName=BuyerUnitName, BuyerAddress=BuyerAddress, BuyerBankAccount="",
                                 PayMethodID=3,
                                 ReceiveTypeID=3,
                                 ReceiverEmail=ReceiverEmail, ReceiverMobile="", ReceiverAddress="", ReceiverName="",
                                 Note=Note,
                                 BillCode="", CurrencyID="VND", ExchangeRate=1.0, InvoiceForm=ehoadon_invoice_form,
                                 InvoiceSerial=ehoadon_invoice_serial,
                                 InvoiceNo=sale_order.ehoadon_no, UserDefine=UserDefine)

            if invoice_string_id:
                command_obj = CommandObjectDTO(invoice, list_invoice_details, [], 0, invoice_string_id, InvoiceAction=8)
                data = DataDTO(CmdType=int(cmdtype), CommandObject=[command_obj])
                data_json = json.dumps(data,
                                       default=lambda o: o.__dict__,
                                       ensure_ascii=False)
                return data_json
        return None

    def _generate_template_edit(self, sale_order):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        ehoadon_tax_rate = get_param('ehoadon.tax_rate', '10')
        ehoadon_tax_rate_id = get_param('ehoadon.tax_rate_id', '3')
        ehoadon_invoice_form = get_param('ehoadon.invoice_form', '1')
        ehoadon_invoice_serial = get_param('ehoadon.invoice_serial', 'C23TAA')
        cmdtype = 124
        BuyerUnitName = ""
        BuyerName = "KHÁCH LẺ"
        BuyerTaxCode = ""
        ReceiverEmail = ""
        BuyerAddress = ""
        Note = ""
        invoice_string_id = str(sale_order.id) +'_dc'
        if sale_order.partner_id.name:
            BuyerName = sale_order.partner_id.name

        if sale_order.partner_id.email:
            ReceiverEmail = sale_order.partner_id.email

        if sale_order.partner_id.vietnam_full_address:
            BuyerAddress = sale_order.water_meter_id.partner_id.vietnam_full_address

        if sale_order.partner_id.vat:
            BuyerTaxCode = sale_order.partner_id.vat

        if sale_order.water_meter_id:
            if sale_order.water_meter_id.partner_id.vietnam_full_address:
                BuyerAddress = sale_order.water_meter_id.partner_id.vietnam_full_address

            if sale_order.water_meter_id.partner_id.name:
                BuyerName = sale_order.water_meter_id.partner_id.name
        # start filter invoice type
        partner_invoice = sale_order.partner_id.child_ids.filtered(lambda x: x.type == 'invoice')
        if partner_invoice:
            partner_invoice = partner_invoice[0] if len(partner_invoice) > 0 else partner_invoice
            if partner_invoice.vietnam_full_address:
                BuyerAddress = partner_invoice.vietnam_full_address
            if partner_invoice.name:
                BuyerName = partner_invoice.name
        # end filter invoice type
        tz = pytz.timezone(self.env.user.tz if self.env.user.tz else "Asia/Ho_Chi_Minh")
        order_date = sale_order.date_order.astimezone(tz)
        # InvoiceDate = sale_order.write_date.astimezone(tz).isoformat('T')
        InvoiceDate = datetime.datetime.now(tz).isoformat('T')
        last_date = sale_order.water_meter_id.setting_date if sale_order.water_meter_id.setting_date else False
        current_balance = 0
        if last_date:
            diff_date = (order_date.date() - last_date).days
        user_define = {"NgayDocThangNay": order_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
                       "NgayDocThangTruoc": last_date.strftime(DEFAULT_SERVER_DATE_FORMAT) if last_date else "",
                       "MaKH": sale_order.partner_id.customer_code if sale_order.partner_id.customer_code else "",
                       "SeriDongHo": sale_order.water_meter_id.name if sale_order.water_meter_id else "",
                       "ChiSoDHThangTruoc": "{:.3f}".format(round(sale_order.water_meter_id.balance, 3)),
                       "ChiSoDHThangNay": 0,
                       "SoNgaySuDung": diff_date if last_date else 0
                       }
        domain_water_meter_current = [('order_id', '!=', False),
                                      ('order_id', '=', sale_order.id),
                                      ('water_meter_id', '=', sale_order.water_meter_id.id)]
        water_meter_current = self.env['qwaco.water.meter.quantity.history'].sudo().search(domain_water_meter_current,
                                                                                           limit=1,
                                                                                           order="create_date desc")
        if water_meter_current and water_meter_current.type == 'addition':
            current_balance = water_meter_current.new_quantity
            user_define.update({"ChiSoDHThangNay": "{:.3f}".format(round(current_balance, 3)),
                                "ChiSoDHThangTruoc": "{:.3f}".format(round(water_meter_current.old_quantity, 3))})
        domain_water_meter_old = [('order_id', '!=', False),
                                  ('order_id', '!=', sale_order.id),
                                  ('order_id.state', 'in', ['sale', 'done']),
                                  ('water_meter_id', '=', sale_order.water_meter_id.id)]
        water_meter_old = self.env['qwaco.water.meter.quantity.history'].sudo().search(domain_water_meter_old, limit=1,
                                                                                       order="create_date desc")
        if water_meter_old and water_meter_old.type == 'addition':
            order_date_old = water_meter_old.order_id.date_order.astimezone(tz)
            last_date = water_meter_old.order_id.date_order.astimezone(tz)
            qty_prev_month = water_meter_old.new_quantity
            diff_date = (order_date - order_date_old).days
            user_define.update({"NgayDocThangTruoc": order_date_old.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                "ChiSoDHThangTruoc": "{:.3f}".format(round(qty_prev_month, 3)),
                                "SoNgaySuDung": diff_date
                                })
        # end user define
        if last_date:
            d2 = order_date - relativedelta(months=1)
            d1 = last_date
            period_year = order_date.year
            months = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
            count_months = []
            totalmonts = (d2.year - d1.year) * 12 + d2.month - 11 + 12 - d1.month
            for i in range(totalmonts):
                count_months.append(months[(d1.month + i - 1) % 12])
            if len(count_months) > 0:
                period_month = " & ".join(x for x in count_months)
            else:
                period_month = order_date.month
            qty_this_month = 0
            list_invoice_details = []
            for line in sale_order.order_line.filtered(lambda x: x.product_uom_qty > 0):
                # ItemName = "Nước tiêu thụ tháng {month} năm {year} từ ngày {from_date} đến ngày {to_date}".format(
                #                     month=period_month, year=period_year, from_date=period_from_date, to_date=period_to_date)
                ItemName = "Nước tiêu thụ tháng {month} năm {year}".format(
                    month=period_month, year=period_year)
                UnitName = "m3"
                Price =0
                Qty = 0
                qty_this_month = 0
                DiscountRate = 0.00
                DiscountAmount = 0.00
                Amount = 0
                TaxAmount = 0
                IsDiscount = False
                product_line = InvoiceDetailsDTO(ItemName=ItemName, UnitName=UnitName, Qty=Qty,
                                                 Price=Price, Amount=Amount, DiscountRate=DiscountRate,
                                                 DiscountAmount=DiscountAmount,
                                                 TaxRateID=int(ehoadon_tax_rate_id), TaxRate=float(ehoadon_tax_rate),
                                                 TaxAmount=TaxAmount, IsDiscount=IsDiscount , ItemTypeID=4,
                                                 )
                list_invoice_details.append(product_line)

            for line in sale_order.order_line.filtered(lambda x: x.product_uom_qty < 0):
                product_discount_first_order = self.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.sale_product_discount_first_order') or False
                if product_discount_first_order and line.product_id.id == int(product_discount_first_order):
                    quantity_discount = self.env['ir.config_parameter'].sudo().get_param(
                        'qwaco.quantity_discount_first_order')
                    ItemName = "Giảm giá {qty} m3 đầu tiên".format(qty=float(quantity_discount))
                else:
                    ItemName = "Khấu trừ khác"
                UnitName = "m3"
                Qty = 0.0
                Price = 0.0
                Amount = 0
                DiscountRate = 0.00
                DiscountAmount = 0.00
                TaxAmount = 0
                IsDiscount = True
                product_line = InvoiceDetailsDTO(ItemName=ItemName, UnitName=UnitName, Qty=Qty,
                                                 Price=Price, Amount=Amount, DiscountRate=DiscountRate,
                                                 DiscountAmount=DiscountAmount,
                                                 TaxRateID=int(ehoadon_tax_rate_id), TaxRate=float(ehoadon_tax_rate),
                                                 TaxAmount=TaxAmount, IsDiscount=IsDiscount
                                                 )
                list_invoice_details.append(product_line)
            if not current_balance > 0:
                last_balance = sale_order.water_meter_id.balance + qty_this_month
                user_define['ChiSoDHThangNay'] = "{:.3f}".format(round(last_balance, 3))
            UserDefine = json.dumps(user_define,
                                    default=lambda o: o.__dict__,
                                    ensure_ascii=False)
            invoice = InvoiceDTO(InvoiceTypeID=1, InvoiceDate=InvoiceDate, BuyerName=BuyerName,
                                 BuyerTaxCode=BuyerTaxCode,
                                 BuyerUnitName=BuyerUnitName, BuyerAddress=BuyerAddress, BuyerBankAccount="",
                                 PayMethodID=3,
                                 ReceiveTypeID=3,
                                 ReceiverEmail=ReceiverEmail, ReceiverMobile="", ReceiverAddress="", ReceiverName="",
                                 Note=Note,
                                 BillCode="", CurrencyID="VND", ExchangeRate=1.0, InvoiceForm=ehoadon_invoice_form,
                                 InvoiceSerial=ehoadon_invoice_serial,
                                 InvoiceNo=0, UserDefine=UserDefine)
            invoice.Reason = "Điều chỉnh thông tin hóa đơn"
            invoice.OriginalInvoiceIdentify = f'''[{sale_order.ehoadon_form}]_[{sale_order.ehoadon_serial}]_[{sale_order.ehoadon_no}]'''
            if invoice_string_id:
                command_obj = CommandObjectDTO(invoice, list_invoice_details, [], 0, invoice_string_id, InvoiceAction=8)
                data = DataDTO(CmdType=int(cmdtype), CommandObject=[command_obj])
                data_json = json.dumps(data,
                                       default=lambda o: o.__dict__,
                                       ensure_ascii=False)
                return data_json
        return None
