from odoo import models


class QueueJob(models.Model):
    _inherit = "queue.job"

    def _subscribe_users_domain(self):
        domain = super()._subscribe_users_domain()
        domain.append(("subscribe_job", "=", True))
        return domain