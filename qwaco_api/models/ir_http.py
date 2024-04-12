# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.http import request
from ..controllers.main import *

_logger = logging.getLogger(__name__)

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_none(cls):        
        if qwaco_api_prefix in request.httprequest.path:
            _logger.info(request.httprequest.path)
            headers = request.httprequest.headers
            try:
                body = json.loads(request.httprequest.data)
            except:
                body = {}
            _logger.info("headers")
            _logger.info(headers)
            _logger.info("params")
            if "password" in body:
                body.pop("password")
            if 'update_sale_info' in request.httprequest.path:
                body = request.httprequest.form
            _logger.info(body)
            language = request.httprequest.headers.get('x-language')
            lang = 'en_US'
            if language and language == 'vi':
                lang = 'vi_VN'
            request.update_context(lang=lang)
        super()._auth_method_none()