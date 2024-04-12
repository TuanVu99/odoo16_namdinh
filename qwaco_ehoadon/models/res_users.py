from odoo import fields, models


class ResUsers(models.Model):

    _inherit = "res.users"

    subscribe_job = fields.Boolean(
        "Job Notifications",
        default=False,
        help="If this flag is checked and the "
        "user is Connector Manager, he will "
        "receive job notifications.",
        index=True,
    )