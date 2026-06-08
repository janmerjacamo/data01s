from odoo import api, fields, models


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    localiza_priority = fields.Selection([
        ('0', 'Bajo'),
        ('1', 'Normal'),
        ('2', 'Alto'),
        ('3', 'Más alto'),
    ], string='Prioridad Localiza', default='2')
    localiza_state = fields.Selection([
        ('new', 'No iniciado'),
        ('progress', 'En proceso'),
        ('done', 'Realizado'),
    ], string='Estado Localiza', default='new')
