# -*- coding: utf-8 -*-
from ..main import *
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo import _, tools
from datetime import timedelta, datetime
from odoo.addons.phone_validation.tools import phone_validation
from odoo.osv.expression import get_unaccent_wrapper
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

import time
import pytz
import math
import re

_logger = logging.getLogger(__name__)
# editable

OUT__customer__call_method__SUCCESS_CODE = 200    # editable

error_code = "01"
# api_prefix = "/api/qwaco/user"
api_prefix = "%s/user" % qwaco_api_prefix

class UserControllerREST(http.Controller):

    def define_token_expires_in(self, token_type, jdata):
        token_lifetime = jdata.get('%s_lifetime' % token_type)
        try:
            token_lifetime = float(token_lifetime)
        except:
            pass
        if isinstance(token_lifetime, (int, float)):
            expires_in = token_lifetime
        else:
            try:
                expires_in = float(request.env['ir.config_parameter'].sudo()
                    .get_param('rest_api.%s_token_expires_in' % token_type))
            except:
                expires_in = 31536000
        return int(round(expires_in))

    @http.route('%s/signin' % api_prefix, methods=['POST'], type='http', auth='none', csrf=False)
    def api__user__signin(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)            
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        # # Convert json data into Odoo vals:
        user = jdata.get('user')
        password = jdata.get('password')

        if not user or not password:
            error_descrip = _("Vui lòng nhập đầy đủ giá trị !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        login_id = request.env['res.users'].sudo().search(
            [('login', '=ilike', user)], limit=1)

        if not login_id:
            error_descrip = _("Tài khoản không tồn tại !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        try:
            request.session.authenticate(db_name, user, password)
        except:
            pass

        uid = request.session.uid

        if not uid:
            error_descrip = _("Sai mật khẩu !")
            error = error_code
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)


        # Generate tokens
        access_token = generate_token(length=200)
        expires_in = self.define_token_expires_in('access', jdata)

        # Save all tokens in store

        token = token_store.save_access_token(
            request.env,
            access_token=access_token,
            expires_in=expires_in,
            user_id=uid
            )
        tz = pytz.timezone("Asia/Ho_Chi_Minh")
        expire_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(token.expiry_time))
        token_expire = datetime.strptime(expire_str, "%Y-%m-%d %H:%M:%S").astimezone(tz).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # Save all tokens in store

        # user_context = request.session.get_context() if uid else {}
        # company_id = request.env.user.company_id.id if uid else 'null'
        # Logout from Odoo and close current 'login' session:
        request.session.logout()

        user = request.env['res.users'].sudo().browse(uid)
        if user.company_id:
            data_company = {'name': user.company_id.name, 'phone': user.company_id.phone, 'address': user.company_id.partner_id.vietnam_full_address}
        else:
            company_id = request.env['res.company'].sudo().search([], limit=1)
            data_company = {'name': company_id.name, 'phone': company_id.phone, 'address': company_id.partner_id.vietnam_full_address}

        # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'token': access_token,
                    'token_expired': token_expire,
                    'login': user.login,
                    'name': user.partner_id.name,
                    'email': user.partner_id.email if user.partner_id.email else "",
                    'phone': user.partner_id.phone if user.partner_id.phone else "",
                    'company': data_company
                }
            }),
        )

    @http.route('%s/get_profile' % api_prefix, methods=['GET'], type='http', auth='none', csrf=False)
    @check_permissions
    def api__user__get_profile(self, **kw):
        args = {}
        try:
            body = json.loads(request.httprequest.data)            
        except:
            body = {}
        # Merge all parameters with body priority
        jdata = args.copy()
        jdata.update(body)
        user = request.env['res.users'].sudo().browse(request.session.uid)

        if user.company_id:
            data_company = {'name': user.company_id.name, 'phone': user.company_id.phone,
                            'address': user.company_id.partner_id.vietnam_full_address}
        else:
            company_id = request.env['res.company'].sudo().search([], limit=1)
            data_company = {'name': company_id.name, 'phone': company_id.phone,
                            'address': company_id.partner_id.vietnam_full_address}

        # Successful response:
        return werkzeug.wrappers.Response(
            status=OUT__customer__call_method__SUCCESS_CODE,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'success': True,
                'result': {
                    'name': user.partner_id.name,
                    'email': user.partner_id.email if user.partner_id.email else "",
                    'phone': user.partner_id.phone if user.partner_id.phone else "",
                    'company': data_company
                }
            }),
        )