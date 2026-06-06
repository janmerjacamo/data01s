from odoo import fields, models


class LocalizaFormSection(models.Model):
    _name = 'localiza.forms.section'
    _description = 'Seccion de formulario operativo'
    _order = 'sequence, name'

    name = fields.Char(string='Seccion', required=True)
    code = fields.Char(string='Codigo')
    sequence = fields.Integer(default=10)
    form_type = fields.Selection([
        ('all', 'Todos'),
        ('entrega_bodega', 'Entrega desde Bodega'),
        ('instalacion_puesto', 'Instalacion en Puesto'),
        ('inventario_puesto', 'Inventario de Puesto'),
        ('prestamo_herramientas', 'Prestamo de Herramientas'),
    ], string='Formulario aplicable', default='all', required=True)
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notas')
