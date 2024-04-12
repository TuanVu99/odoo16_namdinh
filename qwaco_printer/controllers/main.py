# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from OpenSSL import crypto

from odoo import http
from odoo.http import request
from odoo.tools import misc, os, relativedelta

class SignMessage(http.Controller):
    @http.route("/qz-certificate/", auth="public")
    def qz_certificate(self, **kwargs):
        config_param_sudo = request.env["ir.config_parameter"].sudo()
        cert = config_param_sudo.get_param("qz.certificate", default=False)
        if not cert:
            cert = misc.file_open(os.path.join("qwaco_printer", "tests", "cert.pem")).read()
        return request.make_response(cert, [("Content-Type", "text/plain")])

    @http.route("/qz-sign-message/", auth="public")
    def qz_sign_message(self, **kwargs):
        config_param_sudo = request.env["ir.config_parameter"].sudo()
        key = config_param_sudo.get_param("qz.key", default=False)
        if not key:
            key = misc.file_open(os.path.join("qwaco_printer", "tests", "key.pem")).read()
        password = None
        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, key, password)
        data = kwargs.get("request", "").encode("utf-8")
        sign = crypto.sign(pkey, data, "sha512")
        data_base64 = base64.b64encode(sign)
        return request.make_response(data_base64, [("Content-Type", "text/plain")])
