from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LocalizaFormsOperation(models.Model):
    _name = 'localiza.forms.operation'
    _description = 'Formulario operativo de bodega'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Referencia', default='Nuevo', copy=False, readonly=True, tracking=True)
    folio = fields.Char(string='Folio externo', tracking=True)
    form_type = fields.Selection([
        ('entrega_bodega', 'Entrega desde Bodega'),
        ('instalacion_puesto', 'Instalacion en Puesto'),
        ('inventario_puesto', 'Inventario de Puesto'),
        ('prestamo_herramientas', 'Prestamo de Herramientas'),
    ], string='Tipo de formulario', required=True, default='entrega_bodega', tracking=True)
    date = fields.Datetime(string='Fecha / hora', default=fields.Datetime.now, required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('validated', 'Validado'),
        ('closed', 'Cerrado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True)
    active = fields.Boolean(default=True)

    # Personas y responsables
    user_id = fields.Many2one('res.users', string='Usuario que registra', default=lambda self: self.env.user, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado relacionado')
    responsible_id = fields.Many2one('res.partner', string='Responsable / encargado')
    delivered_by = fields.Char(string='Persona encargada de entrega')
    requested_by = fields.Char(string='Persona que solicita')
    receiver_name = fields.Char(string='Persona que recibe')
    receiver_dpi = fields.Char(string='DPI receptor')
    supervisor_name = fields.Char(string='Persona que supervisa')
    guard_name = fields.Char(string='Guardia de turno')
    installer_name = fields.Char(string='Persona que instala / confirma')

    # Puestos y ubicaciones
    puesto_id = fields.Many2one('localiza.puesto', string='Puesto principal')
    puesto_origen_id = fields.Many2one('localiza.puesto', string='Puesto / bodega origen')
    puesto_destino_id = fields.Many2one('localiza.puesto', string='Puesto / destino')
    location_text = fields.Char(string='Ubicacion texto')
    gps_coordinates = fields.Char(string='Coordenadas GPS')

    # Datos operativos
    movement_type = fields.Selection([
        ('salida', 'Salida'),
        ('entrada', 'Entrada'),
        ('inventario', 'Inventario'),
        ('instalacion', 'Instalacion'),
        ('traslado', 'Traslado'),
    ], string='Tipo de movimiento', default='salida')
    main_serial = fields.Char(string='Serie / codigo principal')
    controlled_qty = fields.Integer(string='Cantidad controlada')
    expiration_date = fields.Date(string='Fecha de vencimiento')
    motive = fields.Text(string='Motivo')
    observations = fields.Text(string='Observaciones')
    summary = fields.Text(string='Resumen')
    legal_text = fields.Text(string='Texto de responsabilidad / condicion')

    # Adjuntos ligeros dentro del formulario
    photo_main = fields.Binary(string='Fotografia principal', attachment=True)
    photo_main_name = fields.Char(string='Nombre foto principal')
    photo_document = fields.Binary(string='Fotografia documento / carnet', attachment=True)
    photo_document_name = fields.Char(string='Nombre documento')
    photo_extra = fields.Binary(string='Fotografia adicional', attachment=True)
    photo_extra_name = fields.Char(string='Nombre foto adicional')
    signature_responsible = fields.Binary(string='Firma responsable', attachment=True)
    signature_receiver = fields.Binary(string='Firma receptor / guardia', attachment=True)
    original_pdf = fields.Binary(string='PDF original externo', attachment=True)
    original_pdf_name = fields.Char(string='Nombre PDF original')

    line_ids = fields.One2many('localiza.forms.operation.line', 'form_id', string='Lineas / articulos')
    line_count = fields.Integer(string='Lineas', compute='_compute_line_count')

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = seq.next_by_code('localiza.forms.operation') or 'Nuevo'
        return super().create(vals_list)

    def action_validate(self):
        for rec in self:
            if not rec.line_ids and rec.form_type in ('inventario_puesto', 'prestamo_herramientas'):
                raise UserError(_('Agregue al menos una linea de articulo/herramienta antes de validar.'))
            rec.state = 'validated'

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_print_form(self):
        self.ensure_one()
        report = self.env.ref('localiza_bodega_forms_xim_v2.action_report_localiza_forms_operation', raise_if_not_found=False)
        if not report:
            raise UserError(_('No se encontro la accion del reporte. Actualice el modulo Localiza Bodega Forms XIM V2.'))
        return report.report_action(self)


class LocalizaFormsOperationLine(models.Model):
    _name = 'localiza.forms.operation.line'
    _description = 'Linea de formulario operativo'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    form_id = fields.Many2one('localiza.forms.operation', string='Formulario', required=True, ondelete='cascade')
    form_type = fields.Selection(related='form_id.form_type', store=True, readonly=True)
    section_id = fields.Many2one('localiza.forms.section', string='Seccion')
    product_id = fields.Many2one('product.product', string='Producto Odoo')
    articulo_id = fields.Many2one('localiza.articulo', string='Articulo operativo')
    name = fields.Char(string='Articulo / herramienta / insumo')
    code = fields.Char(string='Codigo')
    serial = fields.Char(string='Serie / IMEI / codigo')
    qty = fields.Float(string='Cantidad', default=1.0)
    uom = fields.Char(string='Unidad')
    movement = fields.Selection([
        ('salida', 'Salida'),
        ('entrada', 'Entrada'),
        ('inventario', 'Inventario'),
        ('instalacion', 'Instalacion'),
        ('observacion', 'Observacion'),
    ], string='Movimiento', default='salida')
    condition = fields.Selection([
        ('bueno', 'Bueno'),
        ('regular', 'Regular'),
        ('danado', 'Dañado'),
        ('faltante', 'Faltante'),
        ('requiere_cambio', 'Requiere cambio'),
    ], string='Estado fisico')
    entry_ok = fields.Boolean(string='Entrada')
    exit_ok = fields.Boolean(string='Salida')
    photo = fields.Binary(string='Foto linea', attachment=True)
    photo_name = fields.Char(string='Nombre foto')
    notes = fields.Text(string='Observacion')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id and not rec.name:
                rec.name = rec.product_id.display_name
            if rec.product_id and not rec.code:
                rec.code = rec.product_id.default_code

    @api.onchange('articulo_id')
    def _onchange_articulo_id(self):
        for rec in self:
            if rec.articulo_id and not rec.name:
                rec.name = rec.articulo_id.display_name
            if rec.articulo_id and not rec.code:
                rec.code = rec.articulo_id.codigo
