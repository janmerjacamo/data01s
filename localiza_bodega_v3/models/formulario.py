from odoo import api, fields, models, _
from odoo.exceptions import UserError

class LocalizaBodegaFormulario(models.Model):
    _name = 'localiza.bodega.formulario'
    _description = 'Formulario Operativo de Bodega'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char('Folio', default='Nuevo', copy=False, readonly=True)
    date = fields.Datetime('Fecha / Hora', default=fields.Datetime.now, required=True, tracking=True)
    form_type = fields.Selection([
        ('entrega_bodega', 'Entrega desde Bodega'),
        ('instalacion_puesto', 'Instalacion en Puesto'),
        ('inventario_puesto', 'Inventario de Puesto'),
        ('prestamo_herramienta', 'Prestamo de Herramientas'),
        ('gps_orden', 'Orden GPS'),
        ('vehiculo_taller', 'Vehiculo / Taller'),
        ('otro', 'Otro'),
    ], string='Tipo de formulario', default='entrega_bodega', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validated', 'Validado'),
        ('closed', 'Cerrado'),
        ('cancelled', 'Cancelado'),
    ], default='draft', string='Estado', tracking=True)
    user_text = fields.Char('Usuario / Activo')
    puesto_id = fields.Many2one('localiza.puesto', string='Puesto')
    origin_puesto_id = fields.Many2one('localiza.puesto', string='Puesto origen')
    destination_puesto_id = fields.Many2one('localiza.puesto', string='Puesto destino')
    supervisor_name = fields.Char('Persona que supervisa / instala')
    guard_name = fields.Char('Guardia / Receptor')
    delivered_by = fields.Char('Encargado de entrega')
    received_by = fields.Char('Persona que recibe')
    receiver_dpi = fields.Char('DPI receptor')
    motive = fields.Char('Motivo')
    gps_location = fields.Char('Ubicacion GPS')
    expiration_date = fields.Date('Fecha de vencimiento')
    ammunition_qty = fields.Integer('Cantidad relacionada')
    summary = fields.Text('Resumen')
    notes = fields.Text('Observaciones')
    line_ids = fields.One2many('localiza.bodega.formulario.line', 'form_id', string='Detalle')
    accessory_ids = fields.One2many('localiza.bodega.formulario.accessory', 'form_id', string='Accesorios / Checklist')
    pdf_original = fields.Binary('PDF original')
    pdf_original_filename = fields.Char('Nombre PDF')
    photo_main = fields.Binary('Fotografia principal')
    photo_main_filename = fields.Char('Nombre fotografia')
    signature_1 = fields.Binary('Firma 1')
    signature_2 = fields.Binary('Firma 2')
    assignment_id = fields.Many2one('localiza.bodega.asignacion', string='Asignacion generada', readonly=True)
    line_count = fields.Integer(compute='_compute_counts')
    accessory_count = fields.Integer(compute='_compute_counts')

    @api.depends('line_ids', 'accessory_ids')
    def _compute_counts(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)
            rec.accessory_count = len(rec.accessory_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('localiza.bodega.formulario') or 'Nuevo'
        return super().create(vals_list)

    def action_validate(self):
        self.write({'state': 'validated'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_create_assignment(self):
        Assignment = self.env['localiza.bodega.asignacion']
        for rec in self:
            if rec.assignment_id:
                continue
            assign_type = 'entrega'
            if rec.form_type == 'instalacion_puesto':
                assign_type = 'instalacion'
            elif rec.form_type == 'prestamo_herramienta':
                assign_type = 'prestamo'
            elif rec.form_type == 'inventario_puesto':
                assign_type = 'inventario'
            vals = {
                'assignment_type': assign_type,
                'date': rec.date,
                'puesto_id': rec.puesto_id.id,
                'origin_puesto_id': rec.origin_puesto_id.id,
                'destination_puesto_id': rec.destination_puesto_id.id,
                'receiver_name': rec.received_by or rec.guard_name,
                'receiver_dpi': rec.receiver_dpi,
                'delivered_by': rec.delivered_by or rec.supervisor_name,
                'motive': rec.motive,
                'notes': rec.notes or rec.summary,
            }
            assignment = Assignment.create(vals)
            for line in rec.line_ids:
                self.env['localiza.bodega.asignacion.line'].create({
                    'assignment_id': assignment.id,
                    'articulo_id': line.articulo_id.id,
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'code': line.code or line.serial_number,
                    'quantity': line.quantity,
                    'condition': line.condition,
                    'notes': line.notes,
                })
            rec.assignment_id = assignment.id
        return True

    def action_print_form(self):
        self.ensure_one()
        action = self.env.ref('localiza_bodega_v3.action_report_localiza_bodega_formulario', raise_if_not_found=False)
        if not action:
            raise UserError(_('No se encontro el reporte del formulario. Actualice el modulo.'))
        return action.report_action(self)

class LocalizaBodegaFormularioLine(models.Model):
    _name = 'localiza.bodega.formulario.line'
    _description = 'Linea de Formulario Operativo'
    _order = 'sequence, id'

    form_id = fields.Many2one('localiza.bodega.formulario', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    articulo_id = fields.Many2one('localiza.bodega.articulo', string='Articulo')
    product_id = fields.Many2one('product.product', string='Producto')
    name = fields.Char('Descripcion / Articulo')
    code = fields.Char('Codigo')
    serial_number = fields.Char('Serie / IMEI')
    quantity = fields.Float('Cantidad', default=1.0)
    movement = fields.Selection([
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('inventario', 'Inventario'),
        ('asignacion', 'Asignacion'),
    ], string='Movimiento', default='salida')
    condition = fields.Selection([
        ('good', 'Bueno'),
        ('regular', 'Regular'),
        ('damaged', 'Dañado'),
        ('missing', 'Faltante'),
    ], default='good', string='Condicion')
    notes = fields.Char('Observacion')
    photo = fields.Binary('Foto')
    photo_filename = fields.Char('Nombre foto')

    @api.onchange('articulo_id')
    def _onchange_articulo_id(self):
        if self.articulo_id:
            self.product_id = self.articulo_id.product_id
            self.name = self.articulo_id.name
            self.code = self.articulo_id.display_code
            self.serial_number = self.articulo_id.serial_number or self.articulo_id.imei

class LocalizaBodegaFormularioAccessory(models.Model):
    _name = 'localiza.bodega.formulario.accessory'
    _description = 'Accesorio o Checklist de Formulario'
    _order = 'sequence, id'

    form_id = fields.Many2one('localiza.bodega.formulario', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char('Accesorio / Item', required=True)
    selected = fields.Boolean('Incluido')
    quantity = fields.Float('Cantidad', default=1.0)
    notes = fields.Char('Observacion')
