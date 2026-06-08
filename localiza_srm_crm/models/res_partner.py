from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .crm_lead import LOCALIZA_OWNER_SELECTION


def _norm(value):
    return ' '.join((value or '').strip().upper().split())


class ResPartner(models.Model):
    _inherit = 'res.partner'

    localiza_owner = fields.Selection(LOCALIZA_OWNER_SELECTION, string='Comercial Responsable')
    localiza_duplicate_count = fields.Integer(string='Duplicados', compute='_compute_localiza_duplicate_count')

    def _localiza_duplicate_domain(self):
        self.ensure_one()
        parts = []
        name = _norm(self.name)
        if name:
            parts.append(('name', '=ilike', name))
        if self.vat:
            parts.append(('vat', '=', self.vat))
        if self.email:
            parts.append(('email', '=ilike', self.email))
        if self.phone:
            parts.append(('phone', '=', self.phone))
        if not parts:
            return [('id', '=', 0)]
        domain = []
        for p in parts:
            if domain:
                domain = ['|'] + domain + [p]
            else:
                domain = [p]
        return [('id', '!=', self.id)] + domain

    def _compute_localiza_duplicate_count(self):
        for partner in self:
            partner.localiza_duplicate_count = self.sudo().search_count(partner._localiza_duplicate_domain()) if partner.id else 0

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        if not self.env.context.get('localiza_allow_duplicate_partner'):
            partners._localiza_check_duplicates()
        return partners

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('localiza_allow_duplicate_partner') and any(k in vals for k in ['name', 'vat', 'email', 'phone']):
            self._localiza_check_duplicates()
        return res

    def _localiza_check_duplicates(self):
        for partner in self:
            if not partner.name:
                continue
            duplicate = self.sudo().search(partner._localiza_duplicate_domain(), limit=1)
            if duplicate:
                raise ValidationError(_('Ya existe un contacto/cliente similar: %s. Revise la ficha existente antes de crear otro registro.') % duplicate.display_name)

    def action_localiza_view_duplicates(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Posibles duplicados'),
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': self._localiza_duplicate_domain(),
        }

    def action_localiza_create_opportunity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva oportunidad'),
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'context': {
                'default_partner_id': self.id,
                'default_type': 'opportunity',
                'default_localiza_owner': self.localiza_owner,
            },
        }

    def action_localiza_create_activity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva actividad'),
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'res.partner',
                'default_res_model_id': self.env['ir.model']._get_id('res.partner'),
                'default_res_id': self.id,
                'default_summary': _('Seguimiento cliente: %s') % self.display_name,
                'default_localiza_owner': self.localiza_owner,
            },
        }

    def action_localiza_create_meeting(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nueva reunión'),
            'res_model': 'calendar.event',
            'view_mode': 'form',
            'context': {
                'default_localiza_partner_id': self.id,
                'default_partner_ids': [(6, 0, [self.id])],
                'default_name': _('Reunión con %s') % self.display_name,
            },
        }
