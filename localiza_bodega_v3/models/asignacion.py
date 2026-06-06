from odoo import api, fields, models, _
from odoo.exceptions import UserError

class LocalizaBodegaAsignacion(models.Model):
    _name = 'localiza.bodega.asignacion'
    _description = 'Asignacion Operativa'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char('Referencia', default='Nuevo', copy=False, readonly=True)
    date = fields.Datetime('Fecha / Hora', default=fields.Datetime.now, required=True, tracking=True)
    assignment_type = fields.Selection([
        ('entrega', 'Entrega'),
        ('devolucion', 'Devolucion'),
        ('instalacion', 'Instalacion'),
        ('prestamo', 'Prestamo'),
        ('inventario', 'Inventario'),
        ('traslado', 'Traslado'),
    ], string='Tipo', default='entrega', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('closed', 'Cerrado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True)
    puesto_id = fields.Many2one('localiza.puesto', string='Puesto')
    origin_puesto_id = fields.Many2one('localiza.puesto', string='Puesto origen')
    destination_puesto_id = fields.Many2one('localiza.puesto', string='Puesto destino')
    receiver_name = fields.Char('Persona que recibe')
    receiver_dpi = fields.Char('DPI receptor')
    delivered_by = fields.Char('Persona que entrega')
    requested_by = fields.Char('Persona que solicita')
    motive = fields.Char('Motivo')
    notes = fields.Text('Observaciones')
    line_ids = fields.One2many('localiza.bodega.asignacion.line', 'assignment_id', string='Lineas')
    document_file = fields.Binary('Documento respaldo')
    document_filename = fields.Char('Nombre documento')
    signature_receiver = fields.Binary('Firma receptor')
    signature_responsible = fields.Binary('Firma responsable')
    line_count = fields.Integer(compute='_compute_line_count')

    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('localiza.bodega.asignacion') or 'Nuevo'
        return super().create(vals_list)

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'
            for line in rec.line_ids:
                if line.articulo_id and rec.assignment_type in ('entrega', 'prestamo', 'traslado'):
                    line.articulo_id.state = 'assigned'
                    if rec.destination_puesto_id:
                        line.articulo_id.puesto_id = rec.destination_puesto_id.id
                    elif rec.puesto_id:
                        line.articulo_id.puesto_id = rec.puesto_id.id
                if line.articulo_id and rec.assignment_type == 'instalacion':
                    line.articulo_id.state = 'installed'
                    if rec.puesto_id:
                        line.articulo_id.puesto_id = rec.puesto_id.id
                if line.articulo_id and rec.assignment_type == 'devolucion':
                    line.articulo_id.state = 'available'
        return True

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_print_assignment(self):
        self.ensure_one()
        action = self.env.ref('localiza_bodega_v3.action_report_localiza_bodega_asignacion', raise_if_not_found=False)
        if not action:
            raise UserError(_('No se encontro el reporte de asignacion. Actualice el modulo.'))
        return action.report_action(self)

class LocalizaBodegaAsignacionLine(models.Model):
    _name = 'localiza.bodega.asignacion.line'
    _description = 'Linea de Asignacion Operativa'
    _order = 'id'

    assignment_id = fields.Many2one('localiza.bodega.asignacion', required=True, ondelete='cascade')
    articulo_id = fields.Many2one('localiza.bodega.articulo', string='Articulo')
    product_id = fields.Many2one('product.product', string='Producto Odoo')
    name = fields.Char('Descripcion')
    code = fields.Char('Codigo / Serie')
    quantity = fields.Float('Cantidad', default=1.0)
    condition = fields.Selection([
        ('good', 'Bueno'),
        ('regular', 'Regular'),
        ('damaged', 'Dañado'),
        ('missing', 'Faltante'),
    ], string='Condicion', default='good')
    notes = fields.Char('Observacion')
    photo = fields.Binary('Foto')
    photo_filename = fields.Char('Nombre foto')

    @api.onchange('articulo_id')
    def _onchange_articulo_id(self):
        if self.articulo_id:
            self.product_id = self.articulo_id.product_id
            self.name = self.articulo_id.name
            self.code = self.articulo_id.display_code
