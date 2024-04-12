# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class SalesRevenueReport(models.TransientModel):
    _name = "qwaco.sales.revenue.report"
    _description = "Sales Revenue Report"

    date_start = fields.Date(required=True, default=fields.Date.context_today)
    date_end = fields.Date(required=True, default=fields.Date.context_today)

    @api.onchange('date_start')
    def _onchange_start_date(self):
        if self.date_start and self.date_end and self.date_end < self.date_start:
            self.date_end = self.date_start

    @api.onchange('date_end')
    def _onchange_end_date(self):
        if self.date_end and self.date_end < self.date_start:
            self.date_start = self.date_end

    def export_xls(self):
        module = __name__.split("addons.")[1].split(".")[0]
        report_name = "{}.qwaco_sales_revenue_xlsx".format(module)
        report = {
            "type": "ir.actions.report",
            "report_type": "xlsx",
            "report_name": report_name,
            # model name will be used if no report_file passed via context
            "context": dict(self.env.context, report_file="Qwaco Sales Revenue"),
            # report_xlsx doesn't pass the context if the data dict is empty
            # TODO: create PR on report_xlsx to fix this
            "data": {"dynamic_report": True},
        }
        return report
