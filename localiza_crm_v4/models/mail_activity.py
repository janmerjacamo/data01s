from odoo import fields, models


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    x_localiza_priority = fields.Selection([
        ('0', 'Normal'), ('1', 'Bajo'), ('2', 'Alto'), ('3', 'Más alto')
    ], string='Prioridad Localiza', default='2')
