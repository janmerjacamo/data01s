from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    x_localiza_crm_owner_allowed = fields.Boolean(
        string='Propietario CRM permitido',
        help='Activa este campo solo para usuarios que pueden ser propietarios/comerciales de oportunidades CRM.'
    )
