qz.security.setCertificatePromise(function (resolve, reject) {
    fetch("/qz-certificate", {
        cache: "no-store",
        headers: {"Content-Type": "text/plain"},
    }).then(function (data) {
        data.ok ? resolve(data.text()) : reject(data.text());
    });
});
qz.security.setSignatureAlgorithm("SHA512");
qz.security.setSignaturePromise(function (toSign) {
    return function (resolve, reject) {
        fetch("/qz-sign-message?request=" + toSign, {
            cache: "no-store",
            headers: {"Content-Type": "text/plain"},
        }).then(function (data) {
            data.ok ? resolve(data.text()) : reject(data.text());
        });
    };
});
odoo.define('qwaco_printer.print_button_widget', function(require) {
    "use strict";
    var core = require('web.core');
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    var PrintButtonWidget = Widget.extend({
        template: 'printButtonWidget',
        events: {
            'click': '_printDoc'
        },
        init: function() {
            this._super.apply(this, arguments);
            var self = this;
            this.formData = arguments[1];
            if (self.formData && self.formData.odoo_printer_data)
                self.doc_print_data = self.formData.odoo_printer_data[0];
        },
        willStart: function() {
            var superDef = this._super.apply(this, arguments);
            return superDef;
        },
        start: function() {
            var element = this.$el;
            var self = this;
            return this._super.apply(this, arguments);
        },
        connect_to_printer: function() {
            var self = this
            var printer_name = false;
            self.set_status('connecting')
            return qz.websocket.connect().then(function() {
                if (self.doc_print_data)
                    var printer_name = self.doc_print_data.printer_name;
                if (!printer_name) {
                    printer_name = self.printer_name;
                }
                self.remote_status = 'connected';
                self.set_status(self.remote_status)
                return qz.printers.find(printer_name).then(function(found) {
                    self.config = qz.configs.create(printer_name);
                    self.remote_status = 'success';
                    self.set_status(self.remote_status)
                }).catch(function(e) {
                    self.remote_status = 'c_error';
                    self.set_status(self.remote_status)
                });
            }).catch(function(e) {
                console.error(e);
                self.remote_status = 'c_error';
                self.set_status(self.remote_status)
            });
        },
        set_status(status) {
            var status_list = ['connected', 'connecting', 'c_error', 'success']
            console.log("status_list------set_status------:", status_list)
            for (var i = 0; i < status_list.length; i++) {
                $('.nw_printer .js_' + status_list[i]).addClass('oe_hidden');
            }
            $('.nw_printer .js_' + status).removeClass('oe_hidden');
        },
        disconnect_from_printer: function() {
            return qz.websocket.disconnect();
        },
        connect_to_nw_printer: function(resolve=null) {
            var self = this;
            return self.disconnect_from_printer().finally(function(e) {
                return self.connect_to_printer();
            })
        },
        auto_sync_printer: function(printer_name) {
            var self = this;
            console.log("usingg---auto_sync_printer-")
            if (printer_name) {
                self.printer_name = printer_name
                self.connect_to_nw_printer();
            }
        },
        _printDoc: function(event) {
            var self = this;
            console.log("self-----_printDoc---------:", self)
            event.preventDefault();
            var url = window.location.href;
            var url_half = url.substring(url.lastIndexOf('#id=') + 1);
            var param = url_half.split('&')[0].split('=')[1];
            var res_id = parseInt(param)
            console.log("id-----_printDoc---:", res_id)
            if (self.doc_print_data && self.doc_print_data.printer_type === "thermal") {
                self.print_thermal_printer(self.doc_print_data.id, res_id, self.doc_print_data.printer_name);
            }
        },
        print_thermal_printer: function(id, res_id, printer_name) {
            var self = this;
            self.printer_name = printer_name;
            rpc.query({
                model: 'qwaco.printer',
                method: 'get_prepared_data',
                args: [{
                    "qwaco_printer_id": id,
                    "res_id": res_id
                }]
            }).then(function(data) {
                if (data) {
                    var data = [{
                            type: 'pixel',
                            format: 'html',
                            flavor: 'plain',
                            data: data,
                            options: { pageWidth: 8},
                        }];
                    console.log(data)
                    if (!qz.websocket.isActive()) {
                        self.connect_to_nw_printer().finally(function() {
                            if (self.remote_status == "success") {
                                var config = qz.configs.create(self.printer_name);
                                qz.print(config, data).then(function() {}).catch(function(e) {
                                    console.error(e);
                                });
                            }
                        })
                    } else {
                        // var top = 0.25, right = 0.25, bottom = 0.25, left = 0.25;
                        var config = qz.configs.create(self.printer_name, { margins: { right: -0.1, left: 0.1 }, rasterize: false, scaleContent: false, density: "600" });
                        qz.print(config, data).then(function() {
                        }).catch(function(e) {
                            console.error(e);
                        });
                    }
                }
            }).catch(function(error) {
                console.log("error", error)
                throw Error("Kiểm tra kết nối máy in!")
            })
        }
    });
    return PrintButtonWidget;
});