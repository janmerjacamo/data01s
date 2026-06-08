from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    localiza_modalidad = fields.Selection([
        ('renta', 'Renta'),
        ('venta', 'Venta'),
    ], string='Modalidad')
    localiza_condicion_pago = fields.Selection([
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
    ], string='Condición comercial')
    localiza_fecha_cierre_real = fields.Date(string='Fecha de cierre real')
    localiza_stage_history_ids = fields.One2many('localiza.crm.stage.history', 'lead_id', string='Historial de fases')
    localiza_stage_history_count = fields.Integer(string='Cambios de fase', compute='_compute_localiza_stage_history_count')
    localiza_activity_pending_count = fields.Integer(string='Actividades pendientes', compute='_compute_localiza_activity_counts')
    localiza_activity_today_count = fields.Integer(string='Actividades de hoy', compute='_compute_localiza_activity_counts')
    localiza_activity_overdue_count = fields.Integer(string='Actividades vencidas', compute='_compute_localiza_activity_counts')

    @api.depends('localiza_stage_history_ids')
    def _compute_localiza_stage_history_count(self):
        grouped = self.env['localiza.crm.stage.history'].read_group(
            [('lead_id', 'in', self.ids)], ['lead_id'], ['lead_id']
        ) if self.ids else []
        data = {g['lead_id'][0]: g['lead_id_count'] for g in grouped}
        for lead in self:
            lead.localiza_stage_history_count = data.get(lead.id, 0)

    def _compute_localiza_activity_counts(self):
        today = fields.Date.context_today(self)
        for lead in self:
            acts = lead.activity_ids
            lead.localiza_activity_pending_count = len(acts)
            lead.localiza_activity_today_count = len(acts.filtered(lambda a: a.date_deadline == today))
            lead.localiza_activity_overdue_count = len(acts.filtered(lambda a: a.date_deadline and a.date_deadline < today))

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        for lead in leads.filtered('stage_id'):
            lead._localiza_create_stage_history(previous_stage=False, new_stage=lead.stage_id)
        return leads

    def write(self, vals):
        old_stages = {rec.id: rec.stage_id for rec in self}
        old_dates = {rec.id: rec.write_date for rec in self}
        res = super().write(vals)
        if 'stage_id' in vals:
            for rec in self:
                previous = old_stages.get(rec.id)
                if previous != rec.stage_id and rec.stage_id:
                    rec._localiza_create_stage_history(previous, rec.stage_id, old_dates.get(rec.id))
        return res

    def _localiza_create_stage_history(self, previous_stage, new_stage, previous_date=False):
        self.ensure_one()
        days = 0.0
        if previous_date:
            delta = fields.Datetime.now() - fields.Datetime.to_datetime(previous_date)
            days = delta.total_seconds() / 86400.0
        self.env['localiza.crm.stage.history'].sudo().create({
            'lead_id': self.id,
            'previous_stage_id': previous_stage.id if previous_stage else False,
            'new_stage_id': new_stage.id,
            'previous_change_date': previous_date,
            'days_in_previous_stage': days,
            'expected_revenue': self.expected_revenue,
            'probability': self.probability,
        })

    def action_localiza_mark_won(self):
        for lead in self:
            lead.action_set_won()
            lead.localiza_fecha_cierre_real = fields.Date.context_today(lead)
        return True

    def action_localiza_mark_lost(self):
        lost_reason = self.env['crm.lost.reason'].search([], limit=1)
        for lead in self:
            try:
                lead.action_set_lost(lost_reason_id=lost_reason.id if lost_reason else False)
            except TypeError:
                lead.action_set_lost()
            lead.localiza_fecha_cierre_real = fields.Date.context_today(lead)
        return True

    def action_localiza_open_stage_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Historial de fases'),
            'res_model': 'localiza.crm.stage.history',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id},
        }
