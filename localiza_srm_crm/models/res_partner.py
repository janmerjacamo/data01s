from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    localiza_commercial_note = fields.Text(string='Nota comercial')
    localiza_lead_count = fields.Integer(string='Oportunidades', compute='_compute_localiza_counts')
    localiza_activity_count = fields.Integer(string='Actividades', compute='_compute_localiza_counts')

    def _compute_localiza_counts(self):
        Lead = self.env['crm.lead']
        Activity = self.env['mail.activity']
        for partner in self:
            partner.localiza_lead_count = Lead.search_count([('partner_id', '=', partner.id)])
            partner.localiza_activity_count = Activity.search_count([('res_model', '=', 'res.partner'), ('res_id', '=', partner.id)])

    @api.constrains('vat', 'email', 'phone', 'mobile', 'name', 'company_type')
    def _check_localiza_duplicates(self):
        for partner in self:
            domain_base = [('id', '!=', partner.id), ('active', 'in', [True, False])]
            if partner.vat:
                dup = self.search(domain_base + [('vat', '=', partner.vat)], limit=1)
                if dup:
                    raise ValidationError(_('Ya existe un contacto con el mismo NIT/RUC: %s') % dup.display_name)
            if partner.email:
                dup = self.search(domain_base + [('email', '=ilike', partner.email)], limit=1)
                if dup:
                    raise ValidationError(_('Ya existe un contacto con el mismo correo: %s') % dup.display_name)

    def action_localiza_create_opportunity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva oportunidad'),
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.id,
                'default_name': _('Oportunidad - %s') % self.display_name,
                'default_type': 'opportunity',
                'default_contact_name': self.name,
                'default_email_from': self.email,
                'default_phone': self.phone or self.mobile,
            },
        }

    def action_localiza_create_activity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva tarea'),
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'res.partner',
                'default_res_id': self.id,
                'default_user_id': self.env.user.id,
            },
        }

    def action_localiza_view_opportunities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Oportunidades'),
            'res_model': 'crm.lead',
            'view_mode': 'kanban,list,form,graph,pivot',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id, 'default_type': 'opportunity'},
        }

    def action_localiza_view_activities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Actividades'),
            'res_model': 'mail.activity',
            'view_mode': 'list,form',
            'domain': [('res_model', '=', 'res.partner'), ('res_id', '=', self.id)],
            'context': {'default_res_model': 'res.partner', 'default_res_id': self.id},
        }
