from odoo import fields, models


class LocalizaFormsBoard(models.Model):
    _name = 'localiza.forms.board'
    _description = 'Panel de formularios operativos'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    form_type = fields.Selection([
        ('all', 'Todos'),
        ('entrega_bodega', 'Entrega desde Bodega'),
        ('instalacion_puesto', 'Instalacion en Puesto'),
        ('inventario_puesto', 'Inventario de Puesto'),
        ('prestamo_herramientas', 'Prestamo de Herramientas'),
    ], default='all', required=True)
    color = fields.Integer(default=0)
    icon = fields.Char(default='fa-clipboard-list')
    description = fields.Char()
    total_count = fields.Integer(compute='_compute_counts')
    draft_count = fields.Integer(compute='_compute_counts')
    validated_count = fields.Integer(compute='_compute_counts')
    closed_count = fields.Integer(compute='_compute_counts')
    cancelled_count = fields.Integer(compute='_compute_counts')

    def _domain(self):
        self.ensure_one()
        if self.form_type == 'all':
            return []
        return [('form_type', '=', self.form_type)]

    def _compute_counts(self):
        Form = self.env['localiza.forms.operation']
        for rec in self:
            domain = rec._domain()
            rec.total_count = Form.search_count(domain)
            rec.draft_count = Form.search_count(domain + [('state', '=', 'draft')])
            rec.validated_count = Form.search_count(domain + [('state', '=', 'validated')])
            rec.closed_count = Form.search_count(domain + [('state', '=', 'closed')])
            rec.cancelled_count = Form.search_count(domain + [('state', '=', 'cancelled')])

    def action_open_records(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'localiza.forms.operation',
            'view_mode': 'list,form',
            'domain': self._domain(),
            'context': {'default_form_type': False if self.form_type == 'all' else self.form_type},
        }

    def action_open_draft(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pendientes - %s' % self.name,
            'res_model': 'localiza.forms.operation',
            'view_mode': 'list,form',
            'domain': self._domain() + [('state', '=', 'draft')],
        }

    def action_new_form(self):
        self.ensure_one()
        ctx = {}
        if self.form_type != 'all':
            ctx['default_form_type'] = self.form_type
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nuevo formulario',
            'res_model': 'localiza.forms.operation',
            'view_mode': 'form',
            'target': 'current',
            'context': ctx,
        }
