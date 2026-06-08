from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_localiza_duplicate_warning = fields.Char(string='Aviso duplicado', compute='_compute_duplicate_warning')
    x_localiza_open_activity_count = fields.Integer(string='Actividades abiertas', compute='_compute_localiza_counts')
    x_localiza_opportunity_count = fields.Integer(string='Oportunidades CRM', compute='_compute_localiza_counts')

    def _duplicate_domain(self, vals=None):
        vals = vals or {}
        name = (vals.get('name') or (self.name if self else '') or '').strip()
        email = (vals.get('email') or (self.email if self else '') or '').strip().lower()
        phone = (vals.get('phone') or vals.get('mobile') or ((self.phone or self.mobile) if self else '') or '').strip()
        vat = (vals.get('vat') or (self.vat if self else '') or '').strip()
        domains = []
        if vat:
            domains.append([('vat', '=ilike', vat)])
        if email:
            domains.append([('email', '=ilike', email)])
        if phone:
            domains.append(['|', ('phone', '=ilike', phone), ('mobile', '=ilike', phone)])
        if name:
            domains.append([('name', '=ilike', name)])
        return expression.OR(domains) if domains else []

    @api.depends('name', 'email', 'phone', 'mobile', 'vat')
    def _compute_duplicate_warning(self):
        for rec in self:
            domain = rec._duplicate_domain()
            duplicates = self.search(domain + [('id', '!=', rec.id)], limit=3) if domain else self.browse()
            rec.x_localiza_duplicate_warning = duplicates and _('Posibles duplicados: %s') % ', '.join(duplicates.mapped('display_name')) or False

    def _compute_localiza_counts(self):
        Activity = self.env['mail.activity'].sudo()
        Lead = self.env['crm.lead'].sudo()
        for rec in self:
            rec.x_localiza_open_activity_count = Activity.search_count([('res_model', '=', 'res.partner'), ('res_id', '=', rec.id)])
            rec.x_localiza_opportunity_count = Lead.search_count([('partner_id', '=', rec.id)])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            temp = self.new(vals)
            domain = temp._duplicate_domain(vals)
            if domain:
                dup = self.search(domain, limit=1)
                if dup:
                    raise ValidationError(_('No se puede crear el cliente porque parece duplicado: %s. Revise nombre, correo, teléfono o NIT.') % dup.display_name)
        return super().create(vals_list)

    def action_localiza_create_opportunity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva oportunidad'),
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_partner_id': self.id, 'default_name': 'Oportunidad - %s' % self.display_name, 'default_type': 'opportunity'},
        }

    def action_localiza_create_activity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva tarea'),
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_res_model': 'res.partner', 'default_res_id': self.id, 'default_user_id': self.env.uid},
        }
