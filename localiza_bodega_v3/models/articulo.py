from odoo import api, fields, models

class LocalizaArticulo(models.Model):
    _name = 'localiza.bodega.articulo'
    _description = 'Articulo Operativo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'category, name'

    name = fields.Char('Articulo', required=True, tracking=True)
    code = fields.Char('Codigo interno', tracking=True)
    product_id = fields.Many2one('product.product', string='Producto Odoo')
    category = fields.Selection([
        ('uniforme', 'Uniforme'),
        ('insumo', 'Insumo'),
        ('gps', 'GPS'),
        ('herramienta', 'Herramienta'),
        ('equipo_industrial', 'Equipo industrial'),
        ('control_especial', 'Control especial'),
        ('vehiculo', 'Vehiculo'),
        ('otro', 'Otro'),
    ], string='Categoria', default='insumo', required=True, tracking=True)
    subcategory = fields.Char('Subcategoria')
    size = fields.Char('Talla')
    serial_number = fields.Char('Serie / Codigo fisico')
    imei = fields.Char('IMEI')
    brand = fields.Char('Marca')
    model = fields.Char('Modelo')
    state = fields.Selection([
        ('available', 'Disponible'),
        ('assigned', 'Asignado'),
        ('installed', 'Instalado'),
        ('maintenance', 'Mantenimiento'),
        ('damaged', 'Dañado'),
        ('lost', 'Perdido'),
        ('inactive', 'Inactivo'),
    ], default='available', string='Estado', tracking=True)
    puesto_id = fields.Many2one('localiza.puesto', string='Puesto actual')
    partner_id = fields.Many2one('res.partner', string='Cliente / Responsable')
    quantity = fields.Float('Cantidad referencial', default=1.0)
    cost = fields.Float('Costo')
    purchase_date = fields.Date('Fecha de compra / ingreso')
    invoice_ref = fields.Char('Factura')
    supplier_id = fields.Many2one('res.partner', string='Proveedor')
    location_id = fields.Many2one('stock.location', string='Ubicacion')
    notes = fields.Text('Observaciones')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El codigo interno debe ser unico.'),
    ]

    display_code = fields.Char('Referencia', compute='_compute_display_code', store=True)

    @api.depends('code', 'serial_number', 'imei')
    def _compute_display_code(self):
        for rec in self:
            rec.display_code = rec.code or rec.serial_number or rec.imei or ''
