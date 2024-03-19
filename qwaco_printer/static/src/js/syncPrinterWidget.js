odoo.define('qwaco_printer.sync_printer_widget', function(require) {
    "use strict";
    var core = require('web.core');
    var Widget = require('web.Widget');
    var SystrayMenu = require('web.SystrayMenu');
    const rpc = require('web.rpc');
    var PrintButtonWidget = require('qwaco_printer.print_button_widget');
    var printWidget = new PrintButtonWidget(self);
    var _t = core._t;
    const {Component} = owl;
    var SyncPrinterWidget = Widget.extend({
        name: 'sync_printer_widget',
        template: 'SyncNetworkPrinterWidget',
        start: function() {
            return this._super();
        },
        willStart: async function() {
            var superDef = this._super.apply(this, arguments);
            return superDef;
        },
    });
    SystrayMenu.Items.push(SyncPrinterWidget);
});