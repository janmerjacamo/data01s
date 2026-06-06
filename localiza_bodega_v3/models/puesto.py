from odoo import api, fields, models

class LocalizaPuesto(models.Model):
    _name = 'localiza.puesto'
    _description = 'Puesto Operativo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Puesto', required=True, tracking=True)
    code = fields.Char('Codigo')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    supervisor_id = fields.Many2one('res.partner', string='Supervisor / Responsable')
    type = fields.Selection([
        ('capital', 'Capital'),
        ('departamental', 'Departamental'),
        ('bodega', 'Bodega'),
        ('otro', 'Otro'),
    ], string='Tipo', default='capital', required=True, tracking=True)
    state = fields.Selection([
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
    ], string='Estado', default='active', tracking=True)
    address = fields.Char('Direccion')
    agent_count = fields.Integer('Cantidad de agentes')
    start_date = fields.Date('Fecha de inicio')
    end_date = fields.Date('Fecha de baja')
    location_id = fields.Many2one('stock.location', string='Ubicacion de inventario')
    notes = fields.Text('Observaciones')

    assignment_count = fields.Integer(compute='_compute_counts')
    form_count = fields.Integer(compute='_compute_counts')

    def _compute_counts(self):
        Assignment = self.env['localiza.bodega.asignacion']
        Form = self.env['localiza.bodega.formulario']
        for rec in self:
            rec.assignment_count = Assignment.search_count([('puesto_id', '=', rec.id)])
            rec.form_count = Form.search_count([('puesto_id', '=', rec.id)])

    def action_view_assignments(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': 'Asignaciones', 'res_model': 'localiza.bodega.asignacion', 'view_mode': 'list,form', 'domain': [('puesto_id', '=', self.id)], 'context': {'default_puesto_id': self.id}}

    def action_view_forms(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': 'Formularios', 'res_model': 'localiza.bodega.formulario', 'view_mode': 'list,form', 'domain': [('puesto_id', '=', self.id)], 'context': {'default_puesto_id': self.id}}
