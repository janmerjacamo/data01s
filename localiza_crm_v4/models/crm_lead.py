from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    x_localiza_sequence = fields.Char(string='No. oportunidad', copy=False, readonly=True, index=True)
    x_localiza_modality = fields.Selection([('rent', 'Renta'), ('sale', 'Venta')], string='Modalidad')
    x_localiza_payment_type = fields.Selection([('cash', 'Contado'), ('credit', 'Crédito')], string='Tipo de pago')
    x_localiza_stage_history_ids = fields.One2many('localiza.crm.stage.history', 'lead_id', string='Historial de fases')
    x_localiza_stage_history_count = fields.Integer(string='Cambios de fase', compute='_compute_stage_history_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('x_localiza_sequence'):
                vals['x_localiza_sequence'] = self.env['ir.sequence'].next_by_code('localiza.crm.opportunity') or '/'
        records = super().create(vals_list)
        for rec in records:
            if rec.stage_id:
                self.env['localiza.crm.stage.history'].sudo().create({
                    'lead_id': rec.id,
                    'stage_id': rec.stage_id.id,
                    'expected_revenue': rec.expected_revenue,
                    'probability': rec.probability,
                    'date_start': fields.Datetime.now(),
                })
        return records

    def write(self, vals):
        old_stage = {rec.id: rec.stage_id.id for rec in self}
        res = super().write(vals)
        if 'stage_id' in vals:
            History = self.env['localiza.crm.stage.history'].sudo()
            for rec in self:
                if old_stage.get(rec.id) != rec.stage_id.id:
                    previous = History.search([('lead_id', '=', rec.id), ('date_end', '=', False)], order='date_start desc', limit=1)
                    if previous:
                        previous.date_end = fields.Datetime.now()
                    History.create({
                        'lead_id': rec.id,
                        'stage_id': rec.stage_id.id,
                        'expected_revenue': rec.expected_revenue,
                        'probability': rec.probability,
                        'date_start': fields.Datetime.now(),
                    })
        return res

    @api.constrains('user_id')
    def _check_allowed_owner(self):
        for rec in self:
            if rec.user_id and not rec.user_id.x_localiza_crm_owner_allowed:
                raise ValidationError(_('El propietario seleccionado no está autorizado para CRM. Active “Propietario CRM permitido” en el usuario.'))

    def _compute_stage_history_count(self):
        for rec in self:
            rec.x_localiza_stage_history_count = len(rec.x_localiza_stage_history_ids)

    def action_localiza_mark_won(self):
        return self.action_set_won()

    def action_localiza_mark_lost(self):
        return self.action_set_lost()

    def action_localiza_create_activity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva tarea'),
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_res_model': 'crm.lead', 'default_res_id': self.id, 'default_user_id': self.user_id.id or self.env.uid},
        }


class LocalizaCrmStageHistory(models.Model):
    _name = 'localiza.crm.stage.history'
    _description = 'Historial de fases CRM'
    _order = 'date_start desc, id desc'

    lead_id = fields.Many2one('crm.lead', string='Oportunidad', required=True, ondelete='cascade')
    stage_id = fields.Many2one('crm.stage', string='Fase', required=True)
    expected_revenue = fields.Monetary(string='Importe')
    probability = fields.Float(string='Probabilidad (%)')
    currency_id = fields.Many2one(related='lead_id.company_currency', store=True, readonly=True)
    date_start = fields.Datetime(string='Fecha de entrada', required=True, default=fields.Datetime.now)
    date_end = fields.Datetime(string='Fecha de salida')
    duration_days = fields.Float(string='Duración días', compute='_compute_duration_days', store=True)

    @api.depends('date_start', 'date_end')
    def _compute_duration_days(self):
        now = fields.Datetime.now()
        for rec in self:
            end = rec.date_end or now
            rec.duration_days = rec.date_start and ((end - rec.date_start).total_seconds() / 86400.0) or 0.0
