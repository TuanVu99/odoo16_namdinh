odoo.define('@qwaco_printer/js/inheritFormRenderer', async function(require) {
    'use strict';
    let __exports = {};
    const {patch} = require('web.utils');
    var PrintButtonWidget = require('qwaco_printer.print_button_widget');
    var rpc = require('web.rpc');
    const {FormRenderer} = require("@web/views/form/form_renderer");
    var {onMounted} = owl;
    patch(FormRenderer.prototype, '/web/static/src/views/form/form_renderer.js', {
        setup() {
            this._super(...arguments);
            onMounted(this.onMounted);
        },
        onMounted() {
            this.show_button();
        },
        show_button: async function() {
            var self = this;
            self.state.odoo_printer_data = false;
            await self.get_printer_data();
            // if (self.state.odoo_printer_data && self.state.odoo_printer_data.length) {
            if (self.state.odoo_printer_data) {
                var printWidget = new PrintButtonWidget(this,this.state);
                var prepend_el = $('.o-form-buttonbox.oe_button_box')
                printWidget.prependTo(prepend_el);
            }
        },
        get_printer_data: async function() {
            var self = this;
            var currentModel = self.env.model.env.searchModel.resModel;
            var odoo_printer_data = await rpc.query({
                model: 'qwaco.printer',
                method: 'search_read',
                args: [[['model_name', '=', currentModel], ['active', '=', true], ]],
            });
            if (odoo_printer_data.length)
                self.state.odoo_printer_data = odoo_printer_data;
        },
    });
    return __exports;
});
;