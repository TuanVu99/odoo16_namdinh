# -*- coding: utf-8 -*-
from ..main import *
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.mimetypes import guess_mimetype
from odoo import _, tools
from odoo.exceptions import UserError
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

import pytz

_logger = logging.getLogger(__name__)
# editable

OUT__customer__call_method__SUCCESS_CODE = 200  # editable

error_code = "01"
# api_prefix = "/api/qwaco/sale"
api_prefix = "%s/sale" % qwaco_api_prefix

SUPPORTED_IMAGE_MIMETYPES = ['image/gif', 'image/jpe', 'image/jpeg', 'image/jpg', 'image/png', 'image/svg+xml']
SUPPORTED_IMAGE_EXTENSIONS = ['.gif', '.jpe', '.jpeg', '.jpg', '.png', '.svg']


class SaleControllerREST(http.Controller):

    @http.route('%s/get_list_sale' % api_prefix, methods=['POST'], type='http', auth='none', csrf=False)  # Upgraded
    @check_permissions
    def api__sale__get_list_sale(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        meter_code = jdata.get('meter_code')
        # # Convert json data into Odoo vals:
        uid = request.env['res.users'].sudo().browse(request.session.uid)
        data = []
        if meter_code and len(meter_code) > 0:
            orders = request.env['sale.order'].sudo().search([('team_id.member_ids', 'in', uid.ids),
                                                              ('team_id', '!=', False),
                                                              ('water_meter_id.name', '=', meter_code),
                                                              ('water_meter_id.state', '=', 'active'),
                                                              ('state', 'in', ('draft', 'sent'))])
        else:
            orders = request.env['sale.order'].sudo().search([('team_id.member_ids', 'in', uid.ids),
                                                              ('team_id', '!=', False),
                                                              ('water_meter_id', '!=', False),
                                                              ('water_meter_id.state', '=', 'active'),
                                                              ('state', 'in', ('draft', 'sent'))])
        tz = pytz.timezone(str(uid.partner_id.tz) if uid.partner_id.tz else "Asia/Ho_Chi_Minh")

        banghi = 0
        for order in orders:
            if banghi > 260:
                break  # Trả về request 60 bản ghi

            if order.water_meter_id.balance > 0:
                last_quantity = order.water_meter_id.balance
            else:
                last_quantity = order.water_meter_id.first_balance

            ##if order.water_meter_id and order.water_meter_id.partner_id.vietnam_full_address:
            ##    address = order.water_meter_id.partner_id.vietnam_full_address
            ##else:
            address = order.partner_id.vietnam_full_address  # Địa chỉ khách hàng (không phải địa chỉ lắp đồng hồ)

            popular_name = order.partner_id.popular_name

            # if order.water_meter_id and order.water_meter_id.partner_id and order.water_meter_id.partner_id.name:
            #    name = order.water_meter_id.partner_id.name
            # else:
            name = order.partner_id.name  # Tên khách hàng, không phải tên đại diện lắp đồng hồ

            if order.partner_id.id_number:
                id_number = order.partner_id.id_number
            else:
                id_number = ""

            vals = {'order_no': order.name,
                    'customer': {'name': name,
                                 'popular_name': popular_name,
                                 'id_number': id_number,  # Thêm thông tin CCDC với cá nhân / MST với tổ chức
                                 'address': address
                                 },
                    'meter': {'code': order.water_meter_id.name,
                              'address': order.water_meter_id.partner_id.vietnam_full_address,
                              # Thêm thông tin địa chỉ lắp đồng hồ
                              'last_quantity': round(last_quantity, 3)
                              },
                    'create_date': order.create_date.astimezone(tz).strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'is_paid': order.is_paid
                    }
            data.append(vals)
            banghi += 1  # Tăng số đếm bản ghi

            # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'data': data
                }
            }),
        )

    @http.route('%s/get_list_sale_confirmations' % api_prefix, methods=['POST'], type='http', auth='none',
                csrf=False)  # Upgraded
    @check_permissions
    def api__sale__get_list_sale_confirmations(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        meter_code = jdata.get('meter_code')
        payment_term = jdata.get('payment_term')
        # # Convert json data into Odoo vals:
        uid = request.env['res.users'].sudo().browse(request.session.uid)
        data = []
        if not payment_term or payment_term not in "pay_later":
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        payment_term_id = request.env['account.payment.term'].sudo().search([('code', '=', payment_term)], limit=1)
        if meter_code and len(meter_code) > 0:
            orders = request.env['sale.order'].sudo().search([('team_id.member_ids', 'in', uid.ids),
                                                              ('team_id', '!=', False),
                                                              ('water_meter_id.name', '=', meter_code),
                                                              ('water_meter_id.state', '=', 'active'),
                                                              ('payment_term_id', '=', payment_term_id.id),
                                                              ('state', 'in', ('sale', 'done'))])
        else:
            orders = request.env['sale.order'].sudo().search([('team_id.member_ids', 'in', uid.ids),
                                                              ('team_id', '!=', False),
                                                              ('water_meter_id', '!=', False),
                                                              ('water_meter_id.state', '=', 'active'),
                                                              ('payment_term_id', '=', payment_term_id.id),
                                                              ('state', 'in', ('sale', 'done'))])

        tz = pytz.timezone(str(uid.partner_id.tz) if uid.partner_id.tz else "Asia/Ho_Chi_Minh")

        banghi = 0
        for order in orders:
            if banghi > 260:
                break  # Trả về request 60 bản ghi

            if order.water_meter_id.balance > 0:
                last_quantity = order.water_meter_id.balance
            else:
                last_quantity = order.water_meter_id.first_balance

            # if order.water_meter_id and order.water_meter_id.partner_id.vietnam_full_address:
            #    address = order.water_meter_id.partner_id.vietnam_full_address
            # else:
            address = order.partner_id.vietnam_full_address  # Lấy địa chỉ khách hàng

            popular_name = order.partner_id.popular_name

            if order.partner_id.id_number:
                id_number = order.partner_id.id_number
            else:
                id_number = ""

            # if order.water_meter_id and order.water_meter_id.partner_id and order.water_meter_id.partner_id.name:
            #    name = order.water_meter_id.partner_id.name
            # else:
            name = order.partner_id.name  # Lấy tên khách hàng

            vals = {'order_no': order.name,
                    'customer': {'name': name,
                                 'popular_name': popular_name,
                                 'id_number': id_number,  # Thêm thông tin CCDC với cá nhân / MST với tổ chức
                                 'address': address
                                 },
                    'meter': {'code': order.water_meter_id.name,
                              'address': order.water_meter_id.partner_id.vietnam_full_address,
                              # Thêm thông tin địa chỉ lắp đồng hồ
                              'last_quantity': round(last_quantity, 3)
                              },
                    'create_date': order.create_date.astimezone(tz).strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'is_paid': order.is_paid
                    }
            data.append(vals)
            banghi += 1  # Tăng số đếm bản ghi

            # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'data': data
                }
            }),
        )

    @http.route('%s/update_sale_info' % api_prefix, methods=['POST'], type='http', auth='none', csrf=False)  # Upgraded
    @check_permissions
    def api__sale__update_sale_info(self, **kw):
        order_no = kw.get('order_no')
        quantity = kw.get('quantity')
        files = request.httprequest.files.getlist("images[]")
        # # Convert json data into Odoo vals:
        if not order_no or not quantity:
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        order = request.env['sale.order'].sudo().search([('name', '=', order_no), ('state', 'in', ('draft', 'sent'))],
                                                        limit=1)
        if order:
            try:
                new_quantity = float(quantity)
                if order.water_meter_id.balance > 0:
                    last_qty = order.water_meter_id.balance
                else:
                    last_qty = order.water_meter_id.first_balance
                if new_quantity <= last_qty:
                    error_descrip = _('Chỉ số mới phải lớn hơn chỉ số cũ !')
                    error = error_code
                    _logger.error(error_descrip)
                    return error_response(400, error, error_descrip)
                used_quantity = new_quantity - last_qty
                if order.water_meter_id and order.water_meter_id.use_credit_point and order.water_meter_id.min_quantity > 0:
                    if used_quantity < order.water_meter_id.min_quantity:
                        min_quantity = last_qty + order.water_meter_id.min_quantity
                        error_descrip = _('Chỉ số mới phải lớn hơn %s m3 !' % min_quantity)
                        error = error_code
                        _logger.error(error_descrip)
                        return error_response(400, error, error_descrip)
                product_default = request.env['ir.config_parameter'].sudo().get_param(
                    'qwaco.sale_product_default') or False
                order_line = order.order_line.filtered(lambda l: not l.product_uom_qty < 0)
                if product_default:
                    order_line = order_line.filtered(
                        lambda l: l.product_id.id == int(product_default))
                order_line.write({'product_uom_qty': used_quantity})
                price_unit = sum(order_line.mapped('price_unit')) or 0
                order._discount_first_order(price=price_unit)
                if order.water_meter_id and order.water_meter_id.use_credit_point and order.water_meter_id.credit_point > 0:
                    order._action_check_credit()
                attachment_ids = []
                for file in files:
                    data_image = file.read()
                    mimetype = guess_mimetype(data_image)
                    if mimetype not in SUPPORTED_IMAGE_MIMETYPES:
                        format_error_msg = _("Uploaded image's format is not supported. Try with: %s",
                                             ', '.join(SUPPORTED_IMAGE_EXTENSIONS))
                        error_descrip = format_error_msg
                        error = error_code
                        _logger.error(error_descrip)
                        return error_response(400, error, error_descrip)
                    attachment_id = request.env['ir.attachment'].sudo().create({
                        'name': file.filename,
                        'datas': base64.b64encode(tools.image_process(data_image)),
                        'res_model': 'sale.order', 'res_id': order.id})
                    # 'res_model': 'mail.compose.message', 'res_id': 0})
                    attachment_ids.append(attachment_id.id)
                if len(attachment_ids) > 0:
                    order.with_user(get_user_id()).message_post(attachment_ids=attachment_ids, body='Ghi nước')
            except UserError as e:
                error_descrip = _('Something went wrong !')
                error = error_code
                _logger.error(e)
                return error_response(400, error, error_descrip)

            # if order.water_meter_id and order.water_meter_id.partner_id.vietnam_full_address:
            #    address = order.water_meter_id.partner_id.vietnam_full_address
            # else:
            address = order.partner_id.vietnam_full_address

            popular_name = order.partner_id.popular_name

            # if order.water_meter_id and order.water_meter_id.partner_id and order.water_meter_id.partner_id.name:
            #    name = order.water_meter_id.partner_id.name
            # else:
            name = order.partner_id.name

            if order.partner_id.id_number:  # Bổ sung thông tin CCCD / MST
                id_number = order.partner_id.id_number
            else:
                id_number = ""

            vals = {'order_no': order.name,
                    'customer': {'name': name,
                                 'popular_name': popular_name,
                                 'id_number': id_number,
                                 'address': address
                                 },
                    'meter': {'code': order.water_meter_id.name,
                              'last_quantity': round(last_qty, 3),
                              'used_quantity': round(used_quantity, 3),
                              'current_quantity': round(new_quantity, 3)
                              },
                    'amount_total': order.amount_total,
                    'amount_untaxed': order.amount_untaxed + abs(order.get_discount_amount()),
                    'amount_tax': order.amount_tax,
                    'amount_discount': abs(order.get_discount_amount()),
                    'price_unit': price_unit
                    }
        else:
            error_descrip = _('Hoá đơn không tồn tại !')
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': vals
            }),
        )

    @http.route('%s/confirm' % api_prefix, methods=['POST'], type='http', auth='none', csrf=False)
    @check_permissions
    def api__sale__confirm(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        payment_term = jdata.get('payment_term')
        order_no = jdata.get('order_no')
        if not order_no or not payment_term:
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if payment_term not in ("pay_now", "pay_later"):
            error_descrip = _("Hình thức thanh toán chưa đúng !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        order = request.env['sale.order'].sudo().search([('name', '=', order_no),
                                                         ('state', '!=', 'cancel')], limit=1)
        if order:
            if payment_term == "pay_now":
                if order.state not in ('sale', 'done'):
                    payment_term = request.env['account.payment.term'].sudo().search([('code', '=', 'pay_now')],
                                                                                     limit=1)
                    order.with_user(request.session.uid).write({'payment_term_id': payment_term.id})
                    order.sudo().with_context(bypass_check_credit=True).action_confirm()
                elif order.state in ('sale', 'done'):
                    order.with_user(request.session.uid).action_paid()
            else:
                if order.state not in ('sale', 'done'):
                    payment_term = request.env['account.payment.term'].sudo().search([('code', '=', 'pay_later')],
                                                                                     limit=1)
                    order.with_user(request.session.uid).write({'payment_term_id': payment_term.id})
                    order.sudo().with_context(bypass_check_credit=True).action_confirm()
        else:
            error_descrip = _('Hoá đơn không tồn tại !')
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True
            }),
        )

    @http.route('%s/review' % api_prefix, methods=['POST'], type='http', auth='none', csrf=False)  # Upgraded
    @check_permissions
    def api__sale__print_review(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        order_no = jdata.get('order_no')
        # # Convert json data into Odoo vals:
        uid = request.env['res.users'].sudo().browse(request.session.uid)
        if not order_no:
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        order = request.env['sale.order'].sudo().search([('name', '=', order_no)], limit=1)
        tz = pytz.timezone(str(uid.partner_id.tz) if uid.partner_id.tz else "Asia/Ho_Chi_Minh")
        if order:
            last_date = order.water_meter_id.setting_date if order.water_meter_id.setting_date else False
            # current_date = order.date_order.astimezone(tz).date() - relativedelta(months=1)
            # period = order_month.strftime("%m/%Y")
            current_date = order.date_order.astimezone(tz) - relativedelta(months=1)
            period_month = current_date.month
            period_year = current_date.year
            order_line = order.order_line.filtered(lambda l: l.product_uom_qty > 0)
            price_unit = sum(order_line.mapped('price_unit')) or 0
            used_quantity = sum(order_line.mapped('product_uom_qty')) or 0
            quant_his = request.env['qwaco.water.meter.quantity.history'].sudo().search([('order_id', '=', order.id),
                                                                                         ('water_meter_id', '=',
                                                                                          order.water_meter_id.id)]
                                                                                        , limit=1, order="id desc")
            if quant_his and quant_his.type == 'addition':
                last_qty = quant_his.old_quantity
                new_quantity = quant_his.new_quantity
                used_quantity = quant_his.new_quantity - quant_his.old_quantity
            else:
                if order.water_meter_id.balance > 0:
                    last_qty = order.water_meter_id.balance
                else:
                    last_qty = order.water_meter_id.first_balance
                new_quantity = last_qty + used_quantity

            domain_water_meter_old = [('order_id', '!=', False),
                                      ('order_id', '!=', order.id),
                                      ('order_id.state', 'in', ['sale', 'done']),
                                      ('water_meter_id', '=', order.water_meter_id.id)]
            water_meter_old = request.env['qwaco.water.meter.quantity.history'].sudo().search(domain_water_meter_old,
                                                                                              limit=1,
                                                                                              order="create_date desc")
            if water_meter_old:
                last_date = water_meter_old.order_id.date_order.astimezone(tz)

            if last_date:
                d2 = current_date
                d1 = last_date
                months = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
                count_months = []
                totalmonts = (d2.year - d1.year) * 12 + d2.month - 11 + 12 - d1.month
                for i in range(totalmonts):
                    count_months.append(months[(d1.month + i - 1) % 12])
                if len(count_months) > 0:
                    period_month = " & ".join(x for x in count_months)

            # if order.water_meter_id and order.water_meter_id.partner_id.vietnam_full_address:
            #    address = order.water_meter_id.partner_id.vietnam_full_address
            # else:
            address = order.partner_id.vietnam_full_address

            ehoadon_tracking_url = request.env['ir.config_parameter'].sudo().get_param(
                'ehoadon.tracking_url') or False
            ehoadon_message = ""
            if order.is_paid and ehoadon_tracking_url:
                ehoadon_message = "Quý khách lấy hóa đơn điện tử vui lòng truy cập vào đường dẫn sau %s" % ehoadon_tracking_url

            popular_name = order.partner_id.popular_name

            # if order.water_meter_id and order.water_meter_id.partner_id and order.water_meter_id.partner_id.name:
            #    name = order.water_meter_id.partner_id.name
            # else:
            name = order.partner_id.name

            if order.partner_id.id_number:  # Bổ sung thông tin CCCD / MST
                id_number = order.partner_id.id_number
            else:
                id_number = ""

            period = "{month}/{year}".format(month=period_month, year=period_year)

            data = {'order_no': order.name,
                    'customer': {'name': name,
                                 'popular_name': popular_name,
                                 'id_number': id_number,
                                 'address': address,
                                 'phone': order.partner_id.phone if order.partner_id.phone else "",
                                 'customer_code': order.partner_id.customer_code,
                                 'contract_no': order.water_meter_id.partner_id.contract_no
                                 },
                    'period': period,
                    'meter': {'code': order.water_meter_id.name,
                              'last_quantity': round(last_qty, 3),
                              'used_quantity': round(used_quantity, 3),
                              'current_quantity': round(new_quantity, 3),
                              'unit': "m3",
                              },
                    'amount_total': abs(order.amount_total),
                    'amount_untaxed': order.amount_untaxed + abs(order.get_discount_amount()),
                    'amount_tax': order.amount_tax,
                    'amount_discount': abs(order.get_discount_amount()),
                    'price_unit': price_unit,
                    'is_paid': order.is_paid,
                    'vat_percent': "5%",
                    'print_date': fields.datetime.now().astimezone(tz).strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'ehoadon_no': order.ehoadon_mtc if order.ehoadon_mtc and order.is_paid else "",
                    'ehoadon_message': ehoadon_message
                    }
        else:
            error_descrip = _('Hoá đơn không tồn tại !')
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'data': data
                }
            }),
        )

    @http.route('%s/reminder/get_list_sale' % api_prefix, methods=['POST'], type='http', auth='none',
                csrf=False)  # Upgraded
    @check_permissions
    def api__sale__reminder__get_list_sale(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        meter_code = jdata.get('meter_code')
        reminder_category = jdata.get('reminder_category')
        if not reminder_category:
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        # # Convert json data into Odoo vals:
        uid = request.env['res.users'].sudo().browse(request.session.uid)
        reminder_cat = request.env['qwaco.reminder.category'].sudo().search([('id', '=', int(reminder_category))])
        if int(reminder_category) == 9:
            reminder_cat = request.env['qwaco.reminder.category'].sudo().search(
                [('id', '=', 1)])  # Gán trường bất kỳ với trường hợp search tất cả (reminder_category = 0)
        data = []
        tz = pytz.timezone("Asia/Ho_Chi_Minh")
        date_start = fields.datetime.now().astimezone(tz).strftime(DEFAULT_SERVER_DATE_FORMAT)

        if reminder_cat:

            domain = [('order_id.team_id.member_ids', 'in', uid.ids),
                      ('order_id.team_id', '!=', False),
                      ('order_id.state', 'in', ('sale', 'done')),
                      ('order_id.is_paid', '=', False),
                      ('reminder_category_id', '=', reminder_cat.id),
                      ('reminder_date', '<=', date_start),
                      ('is_processed', '=', False)]
            if int(reminder_category) == 9:  # Loại bỏ điều kiện reminder_category trong domain tìm kiếm
                domain = [('order_id.team_id.member_ids', 'in', uid.ids),
                          ('order_id.team_id', '!=', False),
                          ('order_id.state', 'in', ('sale', 'done')),
                          ('order_id.is_paid', '=', False),
                          ('reminder_date', '<=', date_start),
                          ('is_processed', '=', False)]
            if meter_code and len(meter_code) > 0:
                domain += [('order_id.water_meter_id.name', '=', meter_code)]

            order_reminders = request.env['qwaco.sale.order.reminder'].sudo().search(domain)

            banghi = 0

            for reminder in order_reminders:
                if banghi > 260:  # Trả về 260 bản ghi
                    break

                quant_his = request.env['qwaco.water.meter.quantity.history'].sudo().search(
                    [('order_id', '=', reminder.order_id.id),
                     ('water_meter_id', '=', reminder.order_id.water_meter_id.id),
                     ('type', '=', 'addition')], limit=1)
                if quant_his:
                    last_qty = quant_his.old_quantity
                    new_quantity = quant_his.new_quantity
                    used_quantity = quant_his.new_quantity - quant_his.old_quantity

                # if reminder.order_id.water_meter_id and reminder.order_id.water_meter_id.partner_id.vietnam_full_address:
                #    address = reminder.order_id.water_meter_id.partner_id.vietnam_full_address
                # else:
                address = reminder.order_id.partner_id.vietnam_full_address  # Lấy địa chỉ khách hàng

                popular_name = reminder.order_id.partner_id.popular_name

                if reminder.order_id.partner_id.id_number:  # Lấy CCCD / MST của khách hàng
                    id_number = reminder.order_id.partner_id.id_number
                else:
                    id_number = ""

                # if reminder.order_id.water_meter_id and reminder.order_id.water_meter_id.partner_id and reminder.order_id.water_meter_id.partner_id.name:
                #    name = reminder.order_id.water_meter_id.partner_id.name
                # else:
                name = reminder.order_id.partner_id.name  # Lấy tên khách hàng

                vals = {'order_no': reminder.order_id.name,
                        'customer': {'name': name,
                                     'popular_name': popular_name,
                                     'id_number': id_number,
                                     'address': address
                                     },
                        'meter': {'code': reminder.order_id.water_meter_id.name,
                                  'address': reminder.order_id.water_meter_id.partner_id.vietnam_full_address,
                                  'last_quantity': round(last_qty, 3),
                                  'used_quantity': round(used_quantity, 3),
                                  'current_quantity': round(new_quantity, 3),
                                  'unit': "m3"
                                  },
                        'is_paid': reminder.order_id.is_paid,
                        'reminder': {'name': reminder.reminder_category_id.name,
                                     'sequence': reminder.reminder_category_id.sequence,
                                     'date': reminder.reminder_date.strftime(
                                         DEFAULT_SERVER_DATE_FORMAT),
                                     }
                        }
                data.append(vals)
                banghi += 1
        else:
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'data': data
                }
            }),
        )

    @http.route('%s/reminder/update_sale_info' % api_prefix, methods=['POST'], type='http', auth='none', csrf=False)
    @check_permissions
    def api__sale__reminder__update_sale_info(self, **kw):
        order_no = kw.get('order_no')
        payment_term = kw.get('payment_term')
        files = request.httprequest.files.getlist("images[]")
        # # Convert json data into Odoo vals:
        if not order_no or not payment_term:
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if payment_term not in ("pay_now", "pay_later"):
            error_descrip = _("Hình thức thanh toán chưa đúng !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        order = request.env['sale.order'].sudo().search([('name', '=', order_no),
                                                         ('state', 'in', ('sale', 'done'))], limit=1)
        uid = request.env['res.users'].sudo().browse(request.session.uid)
        if order:
            try:
                attachment_ids = []
                for file in files:
                    data_image = file.read()
                    mimetype = guess_mimetype(data_image)
                    if mimetype not in SUPPORTED_IMAGE_MIMETYPES:
                        format_error_msg = _("Uploaded image's format is not supported. Try with: %s",
                                             ', '.join(SUPPORTED_IMAGE_EXTENSIONS))
                        error_descrip = format_error_msg
                        error = error_code
                        _logger.error(error_descrip)
                        return error_response(400, error, error_descrip)
                    attachment_id = request.env['ir.attachment'].sudo().create({
                        'name': file.filename,
                        'datas': base64.b64encode(tools.image_process(data_image)),
                        'res_model': 'sale.order', 'res_id': order.id})
                    # 'res_model': 'mail.compose.message', 'res_id': 0})
                    attachment_ids.append(attachment_id.id)
                if len(attachment_ids) > 0:
                    order.with_user(get_user_id()).message_post(attachment_ids=attachment_ids, body='Ghi nước')
                reminder_ids = order.reminder_ids.filtered(lambda reminder: not reminder.is_processed)
                reminder_ids.write({'actual_reminder_date': fields.datetime.now(),
                                    'user_id': uid.id,
                                    'is_processed': True
                                    })
                if payment_term == "pay_now":
                    order.action_paid()
                else:
                    reminder_id = reminder_ids[:1]
                    sequence = reminder_id.reminder_category_id.sequence
                    reminder_days = request.env['ir.config_parameter'].sudo().get_param(
                        'qwaco.reminder_days') or 7
                    reminder_date = fields.Datetime.now() + timedelta(days=int(reminder_days))
                    if sequence == 1:
                        reminder_cate = request.env['qwaco.reminder.category'].search([('sequence', '=', 2)], limit=1)
                    else:
                        reminder_cate = request.env['qwaco.reminder.category'].sudo().search([('sequence', '=', 0)],
                                                                                             limit=1)
                    if reminder_cate:
                        if sequence == 1:
                            vals = {'order_id': order.id,
                                    'reminder_category_id': reminder_cate.id,
                                    'reminder_date': reminder_date
                                    }
                        else:
                            vals = {'order_id': order.id,
                                    'reminder_category_id': reminder_cate.id,
                                    'reminder_date': fields.datetime.now(),
                                    'actual_reminder_date': fields.datetime.now(),
                                    'user_id': uid.id,
                                    'is_processed': True
                                    }
                            reason = 'Khoá nước vì đơn hàng %s trễ hạn thanh toán' % order.name
                            water_vals = {'state': 'inactive',
                                          'reason': reason}
                            order.water_meter_id.write(water_vals)
                        request.env['qwaco.sale.order.reminder'].with_user(request.session.uid).create(vals)

            except UserError as e:
                error_descrip = _('Something went wrong !')
                error = error_code
                _logger.error(e)
                return error_response(400, error, error_descrip)
        else:
            error_descrip = _('Hoá đơn không tồn tại !')
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True
            }),
        )

    @http.route('%s/reminder/get_sale_info' % api_prefix, methods=['POST'], type='http', auth='none',
                csrf=False)  # Upgraded
    @check_permissions
    def api__sale__reminder__get_sale_info(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        order_no = jdata.get('order_no')
        # # Convert json data into Odoo vals:
        if not order_no:
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        uid = request.env['res.users'].sudo().browse(request.session.uid)
        order = request.env['sale.order'].sudo().search([('name', '=', order_no)], limit=1)
        tz = pytz.timezone(str(uid.partner_id.tz) if uid.partner_id.tz else "Asia/Ho_Chi_Minh")
        if order and order.reminder_ids:
            last_qty = 0
            new_quantity = 0
            used_quantity = 0
            quant_his = request.env['qwaco.water.meter.quantity.history'].sudo().search([('order_id', '=', order.id),
                                                                                         ('water_meter_id', '=',
                                                                                          order.water_meter_id.id),
                                                                                         ('type', '=', 'addition')],
                                                                                        limit=1,
                                                                                        order="create_date desc")
            if quant_his:
                last_qty = quant_his.old_quantity
                new_quantity = quant_his.new_quantity
                used_quantity = quant_his.new_quantity - quant_his.old_quantity
            order_line = order.order_line.filtered(lambda l: l.product_uom_qty > 0)
            price_unit = sum(order_line.mapped('price_unit')) or 0
            reminder = order.reminder_ids.filtered(lambda reminder: reminder.is_processed == False)[:1]
            if reminder.reminder_category_id.sequence == 1:
                next_remind = request.env['qwaco.reminder.category'].sudo().search([('sequence', '=', 2)], limit=1)
            else:
                next_remind = request.env['qwaco.reminder.category'].sudo().search([('sequence', '=', 0)], limit=1)

            # if order.water_meter_id and order.water_meter_id.partner_id.vietnam_full_address:
            #    address = order.water_meter_id.partner_id.vietnam_full_address
            # else:
            address = order.partner_id.vietnam_full_address

            popular_name = order.partner_id.popular_name

            # if order.water_meter_id and order.water_meter_id.partner_id and order.water_meter_id.partner_id.name:
            #    name = order.water_meter_id.partner_id.name
            # else:
            name = order.partner_id.name

            if order.partner_id.id_number:  # Bổ sung thông tin CCCD / MST
                id_number = order.partner_id.id_number
            else:
                id_number = ""

            data = {'order_no': order.name,
                    'customer': {'name': name,
                                 'popular_name': popular_name,
                                 'id_number': id_number,
                                 'address': address
                                 },
                    'meter': {'code': order.water_meter_id.name,
                              'last_quantity': round(last_qty, 3),
                              'used_quantity': round(used_quantity, 3),
                              'current_quantity': round(new_quantity, 3)
                              },
                    'amount_total': order.amount_total,
                    'amount_untaxed': order.amount_untaxed + abs(order.get_discount_amount()),
                    'amount_tax': order.amount_tax,
                    'amount_discount': abs(order.get_discount_amount()),
                    'price_unit': price_unit,
                    'reminder': {'name': reminder.reminder_category_id.name,
                                 'sequence': reminder.reminder_category_id.sequence,
                                 'date': reminder.reminder_date.strftime(
                                     DEFAULT_SERVER_DATE_FORMAT),
                                 },
                    'next_reminder': {'name': next_remind.name,
                                      'sequence': next_remind.sequence,
                                      'action': 'lock' if next_remind.sequence == 0 else 'reminder'
                                      },
                    }
        else:
            error_descrip = _('Hoá đơn không tồn tại !')
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'data': data
                }
            }),
        )

    @http.route('%s/reminder/get_category' % api_prefix, methods=['GET'], type='http', auth='none',
                csrf=False)  # Bổ sung giá trị tất cả ứng ID 9
    @check_permissions
    def api__sale__reminder__get_category(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        reminder_cats = request.env['qwaco.reminder.category'].sudo().search(
            [('sequence', '!=', False), ('sequence', '>', 0)])
        data = []
        for cat in reminder_cats:
            data.append({'name': cat.name,
                         'id': cat.id
                         })
        data.append({'name': "Tất cả",
                     'id': 9
                     })
        # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'data': data
                }
            }),
        )

    @http.route('%s/get_sale_info' % api_prefix, methods=['POST'], type='http', auth='none', csrf=False)  # Upgraded
    @check_permissions
    def api__sale__get_sale_info(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        order_no = jdata.get('order_no')
        # # Convert json data into Odoo vals:
        if not order_no:
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        uid = request.env['res.users'].sudo().browse(request.session.uid)
        order = request.env['sale.order'].sudo().search([('name', '=', order_no)], limit=1)
        tz = pytz.timezone(str(uid.partner_id.tz) if uid.partner_id.tz else "Asia/Ho_Chi_Minh")
        if order:
            last_qty = 0
            new_quantity = 0
            used_quantity = 0
            quant_his = request.env['qwaco.water.meter.quantity.history'].sudo().search([('order_id', '=', order.id),
                                                                                         ('water_meter_id', '=',
                                                                                          order.water_meter_id.id),
                                                                                         ('type', '=', 'addition')],
                                                                                        limit=1,
                                                                                        order="create_date desc")
            if quant_his:
                last_qty = quant_his.old_quantity
                new_quantity = quant_his.new_quantity
                used_quantity = quant_his.new_quantity - quant_his.old_quantity
            order_line = order.order_line.filtered(lambda l: l.product_uom_qty > 0)
            price_unit = sum(order_line.mapped('price_unit')) or 0

            # if order.water_meter_id and order.water_meter_id.partner_id.vietnam_full_address:
            #    address = order.water_meter_id.partner_id.vietnam_full_address
            # else:
            address = order.partner_id.vietnam_full_address

            popular_name = order.partner_id.popular_name

            if order.partner_id.id_number:  # Bổ sung thông tin CCCD / MST
                id_number = order.partner_id.id_number
            else:
                id_number = ""

            # if order.water_meter_id and order.water_meter_id.partner_id and order.water_meter_id.partner_id.name:
            #    name = order.water_meter_id.partner_id.name
            # else:
            name = order.partner_id.name

            data = {'order_no': order.name,
                    'customer': {'name': name,
                                 'popular_name': popular_name,
                                 'id_number': id_number,
                                 'address': address
                                 },
                    'meter': {'code': order.water_meter_id.name,
                              'last_quantity': round(last_qty, 3),
                              'used_quantity': round(used_quantity, 3),
                              'current_quantity': round(new_quantity, 3)
                              },
                    'amount_total': order.amount_total,
                    'amount_untaxed': order.amount_untaxed + abs(order.get_discount_amount()),
                    'amount_tax': order.amount_tax,
                    'amount_discount': abs(order.get_discount_amount()),
                    'price_unit': price_unit
                    }
        else:
            error_descrip = _('Hoá đơn không tồn tại !')
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'data': data
                }
            }),
        )

    @http.route('%s/get_list_sale_confirmations_customer' % api_prefix, methods=['POST'], type='http', auth='none',
                csrf=False)
    @check_permissions
    def api__sale_confirmations_customer__get_list_sale(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        customer = jdata.get('customer_code')
        payment_term = jdata.get('payment_term')
        # # Convert json data into Odoo vals:
        uid = request.env['res.users'].sudo().browse(request.session.uid)
        data = []
        if not payment_term or payment_term not in "pay_later":
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        payment_term_id = request.env['account.payment.term'].sudo().search([('code', '=', payment_term)], limit=1)
        if customer and len(customer) > 0:
            orders = request.env['sale.order'].sudo().search([('team_id.member_ids', 'in', uid.ids),
                                                              ('team_id', '!=', False),
                                                              ('partner_id.customer_code', '=', customer),
                                                              ('water_meter_id.state', '=', 'active'),
                                                              ('payment_term_id', '=', payment_term_id.id),
                                                              ('state', 'in', ('sale', 'done'))])
        else:
            orders = request.env['sale.order'].sudo().search([('team_id.member_ids', 'in', uid.ids),
                                                              ('team_id', '!=', False),
                                                              ('partner_id', '!=', False),
                                                              ('water_meter_id.state', '=', 'active'),
                                                              ('payment_term_id', '=', payment_term_id.id),
                                                              ('state', 'in', ('sale', 'done'))], limit=300)

        tz = pytz.timezone(str(uid.partner_id.tz) if uid.partner_id.tz else "Asia/Ho_Chi_Minh")
        for order in orders:
            if order.water_meter_id.balance > 0:
                last_quantity = order.water_meter_id.balance
            else:
                last_quantity = order.water_meter_id.first_balance

            # if order.water_meter_id and order.water_meter_id.partner_id.vietnam_full_address:
            #    address = order.water_meter_id.partner_id.vietnam_full_address
            # else:
            #    address = order.partner_id.vietnam_full_address

            popular_name = order.partner_id.popular_name

            # if order.water_meter_id and order.water_meter_id.partner_id and order.water_meter_id.partner_id.name:
            #    name = order.water_meter_id.partner_id.name
            #    id_number = order.water_meter_id.partner_id.id_number
            # else:
            name = order.partner_id.name

            if order.partner_id.id_number:  # Bổ sung thông tin CCCD / MST
                id_number = order.partner_id.id_number
            else:
                id_number = ""

            vals = {'order_no': order.name,
                    'customer': {'name': name,
                                 'popular_name': popular_name,
                                 'id_number': id_number,
                                 'address': order.partner_id.vietnam_full_address
                                 },
                    'meter': {'code': order.water_meter_id.name,
                              'last_quantity': round(last_quantity, 3),
                              'address': order.water_meter_id.partner_id.vietnam_full_address
                              },
                    'create_date': order.create_date.astimezone(tz).strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'is_paid': order.is_paid
                    }
            data.append(vals)
            # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'data': data
                }
            }),
        )

    @http.route('%s/get_list_sale_customer' % api_prefix, methods=['POST'], type='http', auth='none', csrf=False)
    @check_permissions
    def api__sale__get_list_sale_customer(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        customer_code = jdata.get('customer_code')
        # # Convert json data into Odoo vals:
        uid = request.env['res.users'].sudo().browse(request.session.uid)
        data = []
        if customer_code and len(customer_code) > 0:
            orders = request.env['sale.order'].sudo().search([('team_id.member_ids', 'in', uid.ids),
                                                              ('team_id', '!=', False),
                                                              ('partner_id.customer_code', '=', customer_code),
                                                              ('water_meter_id.state', '=', 'active'),
                                                              ('state', 'in', ('draft', 'sent'))])
        else:
            orders = request.env['sale.order'].sudo().search([('team_id.member_ids', 'in', uid.ids),
                                                              ('team_id', '!=', False),
                                                              ('partner_id', '!=', False),
                                                              ('water_meter_id.state', '=', 'active'),
                                                              ('state', 'in', ('draft', 'sent'))], limit=300)
        tz = pytz.timezone(str(uid.partner_id.tz) if uid.partner_id.tz else "Asia/Ho_Chi_Minh")
        for order in orders:
            if order.water_meter_id.balance > 0:
                last_quantity = order.water_meter_id.balance
            else:
                last_quantity = order.water_meter_id.first_balance

            # if order.water_meter_id and order.water_meter_id.partner_id.vietnam_full_address:
            #    address = order.water_meter_id.partner_id.vietnam_full_address
            # else:
            #    address = order.partner_id.vietnam_full_address

            popular_name = order.partner_id.popular_name

            # if order.water_meter_id and order.water_meter_id.partner_id and order.water_meter_id.partner_id.name:
            #    name = order.water_meter_id.partner_id.name
            #    id_number = order.water_meter_id.partner_id.id_number
            # else:
            name = order.partner_id.name

            if order.partner_id.id_number:  # Bổ sung thông tin CCCD / MST
                id_number = order.partner_id.id_number
            else:
                id_number = ""

            vals = {'order_no': order.name,
                    'customer': {'name': name,
                                 'popular_name': popular_name,
                                 'id_number': id_number,
                                 'address': order.partner_id.vietnam_full_address
                                 },
                    'meter': {'code': order.water_meter_id.name,
                              'last_quantity': round(last_quantity, 3),
                              'address': order.water_meter_id.partner_id.vietnam_full_address
                              },
                    'create_date': order.create_date.astimezone(tz).strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'is_paid': order.is_paid
                    }
            data.append(vals)
            # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'data': data
                }
            }),
        )

    @http.route('%s/reminder/get_list_sale_customer' % api_prefix, methods=['POST'], type='http', auth='none',
                csrf=False)
    @check_permissions
    def api__sale__reminder__get_list_sale_customer(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        customer_code = jdata.get('customer_code')
        reminder_category = jdata.get('reminder_category')
        if not reminder_category:
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        # # Convert json data into Odoo vals:
        uid = request.env['res.users'].sudo().browse(request.session.uid)
        reminder_cat = request.env['qwaco.reminder.category'].sudo().search([('id', '=', int(reminder_category))])

        if int(reminder_category) == 9:
            reminder_cat = request.env['qwaco.reminder.category'].sudo().search(
                [('id', '=', 1)])  # Gán trường bất kỳ với trường hợp search tất cả (reminder_category = 0)
        data = []
        tz = pytz.timezone("Asia/Ho_Chi_Minh")
        date_start = fields.datetime.now().astimezone(tz).strftime(DEFAULT_SERVER_DATE_FORMAT)
        if reminder_cat:

            domain = [('order_id.team_id.member_ids', 'in', uid.ids),
                      ('order_id.team_id', '!=', False),
                      ('order_id.state', 'in', ('sale', 'done')),
                      ('order_id.is_paid', '=', False),
                      ('reminder_category_id', '=', reminder_cat.id),
                      ('reminder_date', '<=', date_start),
                      ('is_processed', '=', False)]

            if int(reminder_category) == 9:  # Loại bỏ điều kiện reminder_category trong domain tìm kiếm
                domain = [('order_id.team_id.member_ids', 'in', uid.ids),
                          ('order_id.team_id', '!=', False),
                          ('order_id.state', 'in', ('sale', 'done')),
                          ('order_id.is_paid', '=', False),
                          ('reminder_date', '<=', date_start),
                          ('is_processed', '=', False)]

            if customer_code and len(customer_code) > 0:
                domain += [('order_id.partner_id.customer_code', '=', customer_code)]
            order_reminders = request.env['qwaco.sale.order.reminder'].sudo().search(domain, limit=300)

            for reminder in order_reminders:
                quant_his = request.env['qwaco.water.meter.quantity.history'].sudo().search(
                    [('order_id', '=', reminder.order_id.id),
                     ('water_meter_id', '=', reminder.order_id.water_meter_id.id),
                     ('type', '=', 'addition')], limit=1)
                if quant_his:
                    last_qty = quant_his.old_quantity
                    new_quantity = quant_his.new_quantity
                    used_quantity = quant_his.new_quantity - quant_his.old_quantity

                # if reminder.order_id.water_meter_id and reminder.order_id.water_meter_id.partner_id.vietnam_full_address:
                #    address = reminder.order_id.water_meter_id.partner_id.vietnam_full_address
                # else:
                #    address = reminder.order_id.partner_id.vietnam_full_address

                popular_name = reminder.order_id.partner_id.popular_name

                # if reminder.order_id.water_meter_id and reminder.order_id.water_meter_id.partner_id and reminder.order_id.water_meter_id.partner_id.name:
                #    name = reminder.order_id.water_meter_id.partner_id.name
                #    id_number = reminder.order_id.water_meter_id.partner_id.id_number
                # else:

                name = reminder.order_id.partner_id.name

                if order.partner_id.id_number:  # Bổ sung thông tin CCCD / MST
                    id_number = reminder.order_id.partner_id.id_number
                else:
                    id_number = ""

                vals = {'order_no': reminder.order_id.name,
                        'customer': {'name': name,
                                     'popular_name': popular_name,
                                     'id_number': id_number,
                                     'address': reminder.partner_id.vietnam_full_address
                                     },
                        'meter': {'code': reminder.order_id.water_meter_id.name,
                                  'address': reminder.order_id.water_meter_id.partner_id.vietnam_full_address,
                                  'last_quantity': round(last_qty, 3),
                                  'used_quantity': round(used_quantity, 3),
                                  'current_quantity': round(new_quantity, 3),
                                  'unit': "m3"
                                  },
                        'is_paid': reminder.order_id.is_paid,
                        'reminder': {'name': reminder.reminder_category_id.name,
                                     'sequence': reminder.reminder_category_id.sequence,
                                     'date': reminder.reminder_date.strftime(
                                         DEFAULT_SERVER_DATE_FORMAT),
                                     }
                        }
                data.append(vals)
        else:
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'data': data
                }
            }),
        )