# -*- coding: utf-8 -*-
from .main import *

_logger = logging.getLogger(__name__)


class ControllerREST(http.Controller):
    
    def define_schema_params(self, request, model_name, method):
        schema = pre_schema = default_vals = None
        cr, uid = request.cr, request.session.uid
        Model = request.env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)
        ResModel = request.env(cr, uid)[model_name]
        if Model.rest_api__used:
            model_available = True
            if method == 'read_all':
                if Model.rest_api__read_all__schema:
                    schema = literal_eval(Model.rest_api__read_all__schema)
                    pre_schema = True
                else:
                    if 'name' in ResModel._fields.keys():
                        schema = ('id', 'name',)
                    else:
                        schema = ('id',)
                    pre_schema = False
            elif method == 'read_one':
                if Model.rest_api__read_one__schema:
                    schema = literal_eval(Model.rest_api__read_one__schema)
                    pre_schema = True
                else:
                    schema = tuple(ResModel._fields.keys())
                    pre_schema = False
            elif method == 'create_one':
                if Model.rest_api__create_one__schema:
                    schema = literal_eval(Model.rest_api__create_one__schema)
                    pre_schema = True
                else:
                    schema = ('id',)
                    pre_schema = False
                default_vals = literal_eval(Model.rest_api__create_one__defaults or '{}')
        else:
            model_available = False
        return model_available, schema, pre_schema, default_vals
    
    # Read all (with optional filters, offset, limit, order, exclude_fields, include_fields):
    @http.route('/api/<string:model_name>', methods=['GET'], type='http', auth='none')
    @check_permissions
    def api__model_name__GET(self, model_name, **kw):
        model_available, schema, pre_schema, _ = self.define_schema_params(request, model_name, 'read_all')
        if not model_available:
            return error_response_501__model_not_available()
        _logger.debug('schema == %s; pre_schema == %s' % (schema, pre_schema))
        return wrap__resource__read_all(
            modelname = model_name,
            default_domain = [],
            success_code = 200,
            OUT_fields = schema,
            pre_schema = pre_schema,
        )
    
    # Read one (with optional exclude_fields, include_fields):
    @http.route('/api/<string:model_name>/<id>', methods=['GET'], type='http', auth='none')
    @check_permissions
    def api__model_name__id_GET(self, model_name, id, **kw):
        model_available, schema, pre_schema, _ = self.define_schema_params(request, model_name, 'read_one')
        if not model_available:
            return error_response_501__model_not_available()
        _logger.debug('schema == %s; pre_schema == %s' % (schema, pre_schema))
        return wrap__resource__read_one(
            modelname = model_name,
            id = id,
            success_code = 200,
            OUT_fields = schema,
            pre_schema = pre_schema,
        )
    
    # Create one:
    @http.route('/api/<string:model_name>', methods=['POST'], type='http', auth='none', csrf=False)
    @check_permissions
    def api__model_name__POST(self, model_name, **kw):
        model_available, schema, _, default_vals = self.define_schema_params(request, model_name, 'create_one')
        if not model_available:
            return error_response_501__model_not_available()
        _logger.debug('schema == %s; default_vals == %s' % (schema, default_vals))
        return wrap__resource__create_one(
            modelname = model_name,
            default_vals = default_vals,
            success_code = 200,
            OUT_fields = schema,
        )
    
    # Update one:
    @http.route('/api/<string:model_name>/<id>', methods=['PUT'], type='http', auth='none', csrf=False)
    @check_permissions
    def api__model_name__id_PUT(self, model_name, id, **kw):
        return wrap__resource__update_one(
            modelname = model_name,
            id = id,
            success_code = 200,
        )
    
    # Delete one:
    @http.route('/api/<string:model_name>/<id>', methods=['DELETE'], type='http', auth='none', csrf=False)
    @check_permissions
    def api__model_name__id_DELETE(self, model_name, id, **kw):
        return wrap__resource__delete_one(
            modelname = model_name,
            id = id,
            success_code = 200,
        )
    
    # Call method (with optional parameters):
    @http.route('/api/<string:model_name>/<id>/<method>', methods=['PUT'], type='http', auth='none', csrf=False)
    @check_permissions
    def api__model_name__id__method_PUT(self, model_name, id, method, **kw):
        return wrap__resource__call_method(
            modelname = model_name,
            id = id,
            method = method,
            success_code = 200,
        )
