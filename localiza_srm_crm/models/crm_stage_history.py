from odoo import api, fields, models


class LocalizaCrmStageHistory(models.Model):
    _name = 'localiza.crm.stage.history'
    _description = 'Historial de fases de oportunidad'
    _order = 'change_date desc, id desc'

    lead_id = fields.Many2one('crm.lead', string='Oportunidad', required=True, ondelete='cascade', index=True)
    previous_stage_id = fields.Many2one('crm.stage', string='Fase anterior')
    new_stage_id = fields.Many2one('crm.stage', string='Fase nueva', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user, required=True)
    change_date = fields.Datetime(string='Fecha de cambio', default=fields.Datetime.now, required=True)
    previous_change_date = fields.Datetime(string='Fecha anterior')
    days_in_previous_stage = fields.Float(string='Días en fase anterior', digits=(16, 2))
    expected_revenue = fields.Monetary(string='Ingreso esperado', currency_field='company_currency')
    probability = fields.Float(string='Probabilidad')
    company_currency = fields.Many2one('res.currency', related='lead_id.company_currency', store=True, readonly=True)
    notes = fields.Text(string='Notas')
